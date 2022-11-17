import json
import urllib
from collections import OrderedDict
from datetime import datetime
from typing import Union

import gridfs
from apiflask import APIBlueprint, abort, output, input
from bson import ObjectId
from bson.errors import InvalidId
from flask import render_template, Response, url_for, request
from pymongo import UpdateOne

from commons.correction_utils import write_correction, write_raw_training_data
from commons.label_studio_commons import to_label_studio_format_single
from commons.mongo_utils import connect_mongo
from process.utils import json_serial
from supercon2.schemas import Record, Flag, RecordParamsIn, UpdatedRecord, Publishers, Years

bp = APIBlueprint('supercon', __name__)
config = []
VALID_STATUSES = ["invalid", "new", "curated", "validated"]


@bp.route('/version')
def get_version():
    version = None
    revision = None
    if version is None:
        version = read_info_from_file("resources/version.txt")

    if revision is None:
        revision = read_info_from_file("resources/revision.txt")

    info_json = {"name": "supercon2", "version": version + "-" + str(revision)}
    return info_json


def read_info_from_file(file, default="unknown"):
    version = default
    try:
        with open(file, 'r') as fv:
            file_version = fv.readline()

        version = file_version.strip() if file_version != "" and file_version is not None else default
    except:
        pass

    return version


@bp.route('/')
def index():
    return render_template('index.html', version=get_version()['version'])


# @bp.route('/<page>')
# def render_page(page):
#     return render_template(page)


# @bp.route('/annotation/feedback', methods=['POST'])
# def annotation_feedback():
#     print("Received feedback request. id=" + str(request.form))
#     return request.form


@bp.route('/publishers')
@output(Publishers)
def get_publishers():
    db = connect_and_get_db()

    filtered_distinct_publishers = list(filter(lambda x: x is not None, db.tabular.distinct("publisher")))
    return {"publishers": filtered_distinct_publishers}


def connect_and_get_db():
    connection = connect_mongo(config=config)
    db_name = config['mongo']['db']
    db = connection[db_name]
    return db


@bp.route('/years')
@output(Years)
def get_years():
    db = connect_and_get_db()

    distinct_years = db.tabular.distinct("year")
    filtered_distinct_years = list(filter(lambda x: x is not None and 1900 < x < 3000, distinct_years))
    return {"years": filtered_distinct_years}


@bp.route("/stats", methods=["GET"])
def get_stats():
    db = connect_and_get_db()
    tabular_collection = db.get_collection("tabular")

    pipeline_group_by_publisher = [
        {"$match": {"type": "automatic", "status": {"$in": VALID_STATUSES}}},
        {"$group": {"_id": "$publisher", "count_records": {"$sum": 1}, "hashes": {"$addToSet": "$hash"}}},
        {"$project": {"_id": 1, "hashes": 1, "count_records": 1, "count_docs": {"$size": "$hashes"}}},
        {"$project": {"hashes": 0}},
        {"$sort": {"count_docs": -1}}
    ]
    by_publisher = tabular_collection.aggregate(pipeline_group_by_publisher)
    by_publisher_fixed = replace_empty_key(by_publisher)

    pipeline_group_by_year = [
        {"$match": {"type": "automatic", "status": {"$in": VALID_STATUSES}}},
        {"$group": {"_id": "$year", "count_records": {"$sum": 1}, "hashes": {"$addToSet": "$hash"}}},
        {"$project": {"_id": 1, "hashes": 1, "count_records": 1, "count_docs": {"$size": "$hashes"}}},
        {"$project": {"hashes": 0}},
        {"$sort": {"count_docs": -1}}
    ]
    by_year = tabular_collection.aggregate(pipeline_group_by_year)
    by_year_fixed = replace_empty_key(by_year)

    pipeline_group_by_journal = [
        {"$match": {"type": "automatic", "status": {"$in": VALID_STATUSES}}},
        {"$group": {"_id": "$journal", "count_records": {"$sum": 1}, "hashes": {"$addToSet": "$hash"}}},
        {"$project": {"_id": 1, "hashes": 1, "count_records": 1, "count_docs": {"$size": "$hashes"}}},
        {"$project": {"hashes": 0}},
        {"$sort": {"count_docs": -1}}
    ]
    by_journal = tabular_collection.aggregate(pipeline_group_by_journal)
    by_journal_fixed = replace_empty_key(by_journal)

    return render_template("stats.html", by_publisher=by_publisher_fixed, by_year=by_year_fixed,
                           by_journal=by_journal_fixed, version=get_version()['version'])


@bp.route("/correction_logger", methods=["GET"])
def get_correction_log():
    base_url = get_base_url(config)
    return render_template("correction_log.html", version=get_version()['version'], base_url=base_url)


@bp.route("/correction_logger/document/<hash>", methods=["GET"])
def get_correction_log_filter_by_document(hash):
    base_url = get_base_url(config)
    return render_template("correction_log.html", hash=hash, version=get_version()['version'], base_url=base_url)


def get_base_url(config):
    return urllib.parse.urljoin(request.host_url, config['root-path'])


def replace_empty_key(input):
    output = [{k: v for k, v in item.items()} for item in input]
    for pub in output:
        if pub['_id'] == "":
            pub['_id'] = 'N/A'
            break
    return output


@bp.route("/record/<id>", methods=["PUT", "PATCH"])
@input(Record)
@output(UpdatedRecord)
def update_record(id, record: Union[Record, dict]):
    object_id = validateObjectId(id)
    validate_record(record)
    db = connect_and_get_db()

    try:
        new_id = _update_record(object_id, record, db=db)
    except Exception as e:
        abort(400, str(e))

    return_info = UpdatedRecord()
    return_info.id = new_id
    return_info.previous_id = id

    return return_info


def find_latest(current_record, collection):
    next_record = collection.find_one({'previous': current_record['_id']})
    if next_record is None:
        return current_record
    elif next_record['status'] != "obsolete":
        return next_record
    else:
        return find_latest(next_record, collection)


def _update_record(object_id: ObjectId, new_doc: Union[Record, dict], db):
    tabular_collection = db.get_collection("tabular")
    document_collection = db.get_collection("document")
    training_data_collection = db.get_collection("training_data")

    if 'id' in new_doc:
        del new_doc['id']
    if 'sentence_decorated' in new_doc:
        del new_doc['sentence_decorated']

    old_doc = tabular_collection.find_one({"_id": object_id})
    if old_doc['status'] == "obsolete":
        latest_record = find_latest(old_doc, tabular_collection)
        message = "The record with id " + str(
            object_id) + " is obsolete. The latest updated record of the chain is" + str(
            latest_record['_id'])
        raise Exception(message)

    new_doc_id = None
    training_data_id = None
    try:
        # If there is an error type, we fetch it and add it to the record that will be marked obsolete
        error_type = None
        if 'error_type' in new_doc:
            error_type = new_doc['error_type']
            # del record['error_type']

        new_doc_id = write_correction(old_doc, new_doc, tabular_collection, error_type=error_type)
        training_data_id = write_raw_training_data(old_doc, new_doc_id, document_collection, training_data_collection,
                                                   action="update")
        return new_doc_id
    except Exception as e:
        # Roll back!
        print("Exception:", e, "Rolling back.")
        rollback(new_doc_id, old_doc, training_data_id, tabular_collection, training_data_collection)
        raise e


def rollback(new_id, old_doc, training_data_id, tabular_collection, training_data_collection):
    if training_data_id is not None:
        training_data_collection.delete_one({"_id": training_data_id})

    if new_id is not None:
        tabular_collection.delete_one({"_id": new_id})
        query_set = {"status": old_doc['status']}
        query_unset = {"previous": ""}

        # When rolling back I might have the error type or not, in the previous record
        if 'error_type' in old_doc:
            query_set['error_type'] = old_doc['error_type']
        else:
            query_unset['error_type'] = ""

        tabular_collection.update_one(
            {'_id': old_doc['_id']},
            {
                "$set": query_set,
                "$unset": query_unset
            }
        )


def rollback_delete(previous_record, training_data_id, tabular_collection, training_data_collection):
    if training_data_id is not None:
        training_data_collection.delete_one({"_id": training_data_id})

    if previous_record is not None:
        query_update = {"$set": {"status": previous_record['status']}}
        if 'error_type' in previous_record:
            query_update["$set"]["error_type"] = previous_record['error_type']

        tabular_collection.update_one(
            {'_id': previous_record['_id']},
            query_update
        )


@bp.route("/record", methods=["POST"])
@input(Record)
@output(Record)
def create_record(record: Record):
    validate_record(record)
    if 'timestamp' not in record:
        record['timestamp'] = datetime.utcnow()

    new_id = add_record(record)

    return_info = UpdatedRecord()
    return_info.id = new_id

    return return_info


@bp.route("/error_types", methods=["GET"])
def get_error_types():
    error_types = OrderedDict()

    error_types['from_table'] = "From table"
    error_types['extraction'] = "Extraction"
    error_types['tc_classification'] = "Tc classification"
    error_types['linking'] = "Linking"
    error_types['composition_resolution'] = "Composition resolution"
    error_types['value_resolution'] = "Value resolution"

    return error_types


def validate_record(record):
    if 'hash' not in record or record['hash'] == "":
        abort(400, "Missing document hash")

    if 'doi' not in record or record['doi'] == "":
        abort(400, "Missing DOI")

    if 'type' in record:
        abort(400, "'type' and 'status' cannot be set by update as they are internal values.")

    if 'status' in record:
        abort(400, "'type' and 'status' cannot be set by update as they are internal values.")


def add_record(record: Record):
    db = connect_and_get_db()

    tabular_collection = db.get_collection("tabular")

    record['timestamp'] = datetime.utcnow()
    record['status'] = "valid"
    record['type'] = "manual"

    new_record = tabular_collection.insert_one(record)

    return new_record.inserted_id


@bp.route("/records", methods=["GET"])
@input(RecordParamsIn, location='query')
@output(Record(many=True))
def get_records_from_form_data(query_data):
    return get_records(**query_data)


@bp.route("/records/<type>", methods=["GET"])
@output(Record(many=True))
def get_tabular_from_path_by_type(type):
    return get_records(type)


@bp.route("/records/<type>/<publisher>/<year>", methods=["GET"])
@output(Record(many=True))
def get_tabular_from_path_by_type_publisher_year(type, publisher, year):
    return get_records(type, publisher, year)


@bp.route("/records/<type>/<year>", methods=["GET"])
@output(Record(many=True))
def get_tabular_from_path_by_type_year(type, year):
    return get_records(type, publisher=None, year=year)


@bp.route("/records_curated", methods=["GET"])
@output(Record(many=True))
def get_curation_log():
    db = connect_and_get_db()

    pipeline = [
        {"$match": {"previous": {"$exists": 1}, "status": {"$not": {"$in": ["empty", "new", "obsolete"]}}}}
    ]
    entries = []
    tabular_collection = db.get_collection("tabular")

    cursor_aggregation = tabular_collection.aggregate(pipeline)

    entities = []
    for entry in cursor_aggregation:
        entry['id'] = str(entry['_id'])
        previous_id = entry['previous']
        entry['previous'] = str(entry['previous'])
        entities.append(entry)

        count = 0
        while previous_id is not None:
            previous_record = tabular_collection.find_one({"_id": previous_id})
            previous_id = previous_record['previous'] if 'previous' in previous_record else None
            count += 1

        entry['update_count'] = count

    return entities


def get_records(type=None, status=None, document=None, publisher=None, year=None, start=-1, limit=-1):
    db = connect_and_get_db()

    # pipeline = [
    #     {"$group": {"_id": "$hash", "versions": {"$addToSet": "$timestamp"}, "count": {"$sum": 1}}},
    #     {"$sort": {"count": -1}}
    # ]

    # type and status allowed combinations are: valid/manual, valid/automatic, invalid/manual, invalid/automatic,
    query = {}
    if type is None:
        query['type'] = {"$in": ['automatic', 'manual']}
    else:
        query['type'] = type

    if status is None:
        query['status'] = {"$in": VALID_STATUSES}
    else:
        query['status'] = status

    entries = []
    tabular_collection = db.get_collection("tabular")

    if document:
        query['hash'] = document

    if publisher:
        query['publisher'] = publisher

    if year:
        query['year'] = int(year)

    cursor = tabular_collection.find(query)

    if start > 0:
        cursor.skip(start)

    if limit > 0:
        cursor.limit(limit)

    for entry in cursor:
        entry['id'] = str(entry['_id'])
        entry['section'] = entry['section'] if 'section' in entry and entry['section'] is not None else ''
        entry['subsection'] = entry['subsection'] if 'subsection' in entry and entry[
            'subsection'] is not None else ''
        entry['title'] = entry['title'] if 'title' in entry and entry[
            'title'] is not None else ''

        if 'sentence' in entry:
            if 'spans' in entry:
                entry['sentence_decorated'] = decorate_text_with_annotations(entry['sentence'], entry['spans'])
            else:
                entry['sentence_decorated'] = entry['sentence']
        else:
            entry['sentence'] = ""

        entries.append(entry)

        if type == "manual":
            entry['doc_url'] = None
        elif type == 'automatic':
            # document_collection = db_supercon_dev.get_collection("document")
            # documents = document_collection.aggregate(pipeline)
            # document_list = list(documents)
            # aggregation_query = [{"$sort": {"hash": 1, "timestamp": 1}}, {"$group": {"_id": "$hash", "lastDate": {"$last": "$timestamp"}}}]
            # aggregation_query = [{"$match": {"type": type}}] + aggregation_query
            # cursor_aggregation = document_collection.aggregate(aggregation_query)
            entry['doc_url'] = url_for('supercon.get_document', hash=entry['hash'])

    return entries


@bp.route("/database", methods=["GET"])
def get_automatic_database():
    base_url = get_base_url(config)
    return render_template("database.html", base_url=base_url)


@bp.route("/database/document/<hash>", methods=["GET"])
def get_automatic_database_filter_by_document(hash):
    base_url = get_base_url(config)
    return render_template("database.html", hash=hash, base_url=base_url)


@bp.route('/document/<hash>', methods=['GET'])
def get_document(hash):
    return render_template("document.html", hash=hash)


@bp.route('/annotation/<hash>', methods=['GET'])
def get_annotations(hash):
    """Get annotations (latest version)"""
    db = connect_and_get_db()
    annotations = db.get_collection("document").find({"hash": hash}).sort("timestamp", -1)
    annotation = annotations[0]
    del annotation["_id"]
    return Response(json.dumps(annotation, default=json_serial), mimetype="application/json")


@bp.route('/pdf/<hash>', methods=['GET'])
def get_binary(hash):
    """GET PDF / binary file """
    db = connect_and_get_db()
    fs_binary = gridfs.GridFS(db, collection='binary')

    file = fs_binary.find_one({"hash": hash})
    if file is None:
        return "Document with identifier=" + str(hash) + " not found.", 404
    else:
        return Response(fs_binary.get(file._id).read(), mimetype='application/pdf')


@bp.route('/record/<id>', methods=['GET'])
@output(Record)
def get_record(id):
    object_id = validateObjectId(id)
    db = connect_and_get_db()
    record = db.get_collection("tabular").find_one({"_id": object_id})

    record['id'] = str(record['_id'])
    return record


def _delete_record(id, error_type, db):
    tabular_collection = db.get_collection("tabular")
    document_collection = db.get_collection("document")
    training_data_collection = db.get_collection("training_data")
    old_doc = None
    training_data_id = None
    try:
        old_doc = tabular_collection.find_one({"_id": id})
        record_information = tabular_collection.update_one({"_id": id}, {"$set": {"status": "removed", "error_type": error_type}})
        training_data_id = write_raw_training_data(old_doc, old_doc['_id'], document_collection,
                                                   training_data_collection, action="delete")

    except Exception as e:
        # Rollback!
        print("Exception:", e, "Rolling back.")
        rollback_delete(old_doc, training_data_id, tabular_collection, training_data_collection)
        raise e

    return record_information


@bp.route('/record/<id>', methods=['DELETE'])
@output(UpdatedRecord)
def delete_record(id, error_type):
    object_id = validateObjectId(id)
    db = connect_and_get_db()

    if error_type not in get_error_types.keys():
        abort(400, "The specified error type: " + str(error_type) + " is invalid.")

    try:
        _delete_record(object_id, error_type, db=db)
    except Exception as e:
        abort(400, str(e))

    return_info = UpdatedRecord()
    return_info.id = object_id

    return return_info


@bp.route('/record/<id>/status', methods=['GET'])
@output(Flag)
def get_record_status(id):
    object_id = validateObjectId(id)
    db = connect_and_get_db()
    record = db.get_collection("tabular").find_one({"_id": object_id}, {'_id': 0, 'type': 1, 'status': 1})

    return record


@bp.route('/record/<id>/mark_invalid', methods=['PUT', 'PATCH'])
@output(Flag)
def mark_record_invalid(id):
    """The record is marked as invalid"""
    object_id = validateObjectId(id)
    db = connect_and_get_db()
    tabular_collection = db.get_collection("tabular")
    record = tabular_collection.find_one({"_id": object_id, "status": {"$in": VALID_STATUSES}})
    if record is None:
        return 404
    else:
        new_status = 'invalid'
        new_type = 'manual'

        changes = {'status': new_status, 'type': new_type}

        tabular_collection.update_one({'_id': record['_id']}, {'$set': changes})
        return changes, 200


@bp.route('/record/<id>/mark_validated', methods=['PUT', 'PATCH'])
@output(Flag)
def mark_record_validated(id):
    """The record is marked as correct"""
    object_id = validateObjectId(id)
    db = connect_and_get_db()
    return _mark_validated(db, object_id)


def _mark_validated(db, id: ObjectId):
    tabular_collection = db.get_collection("tabular")
    record = tabular_collection.find_one({"_id": id, "status": {"$in": VALID_STATUSES}})
    if record is None:
        return "Record with id=" + id + " not found.", 404

    new_status = 'validated'
    new_type = 'manual'

    changes = {'status': new_status, 'type': new_type}

    tabular_collection.update_one({'_id': record['_id']}, {'$set': changes})
    return changes, 200


def validateObjectId(id):
    try:
        return ObjectId(id)
    except InvalidId as e:
        abort(400, "Invalid identifier (objectId)")


@bp.route('/record/<id>/reset', methods=['PUT', 'PATCH'])
@output(Flag)
def reset_record(id):
    """Reset the status of the record"""
    object_id = validateObjectId(id)
    db = connect_and_get_db()
    return _reset_record(db, object_id)


def _reset_record(db, id: ObjectId):
    tabular_collection = db.get_collection("tabular")
    record = tabular_collection.find_one({"_id": id, "status": {"$in": VALID_STATUSES}})
    if record is None:
        return "Valid record with id=" + str(id) + " not found.", 404

    if 'previous' in record:
        status = 'curated'
        type = 'manual'
    else:
        status = 'new'
        type = 'automatic'

    changes = {'status': status, 'type': type}
    tabular_collection.update_one({'_id': record['_id']}, {'$set': changes})

    return changes, 200


@bp.route('/config', methods=['GET'])
def get_config():
    return config


# def get_config(config_file='config.yaml'):
#     return load_config_yaml(config_file)


@bp.route('/training_data', methods=['GET'])
def get_training_data():
    return render_template("training_data.html")


@bp.route('/training/data/<id>', methods=['GET'])
def export_training_data(id):
    object_id = validateObjectId(id)
    db = connect_and_get_db()
    training_data_collection = db.get_collection("training_data")

    single_training_data = training_data_collection.find_one({'_id': object_id}, {'tokens': 0})

    single_training_data['id'] = str(single_training_data['_id'])
    del single_training_data['_id']

    # workaround - to be removed
    if type(single_training_data['corrected_record_id']) == ObjectId:
        single_training_data['corrected_record_id'] = str(single_training_data['corrected_record_id'])

    return single_training_data


@bp.route('/biblio/<hash>')
def get_biblio_by_hash(hash):
    db = connect_and_get_db()
    last_documents = db.get_collection("document").find({"hash": hash}).sort("timestamp", -1)
    last_document = last_documents[0]
    return last_document['biblio']


@bp.route('/training/data/status/<status>')
def export_training_data_by_status(status):
    db = connect_and_get_db()
    new_format, _ = get_training_data_by_status(status, db)

    return Response(json.dumps(new_format, default=json_serial), mimetype="application/json")


def get_training_data_by_status(status, db):
    training_data_collection = db.get_collection("training_data")
    training_data_list = list(training_data_collection.find({'status': status}, {'tokens': 0}))
    new_format = []
    ids = []
    for training_data in training_data_list:
        new_structure = to_label_studio_format_single(training_data['text'], training_data['spans'])
        new_format.append(new_structure)
        ids.append(training_data['_id'])
    return new_format, ids


def get_training_data_by_id_and_status(record_id, status, db):
    id = validateObjectId(record_id)
    training_data_collection = db.get_collection("training_data")
    training_data = training_data_collection.find_one({'_id': id, 'status': status}, {'tokens': 0})
    if not training_data:
        return None, None
    new_structure = to_label_studio_format_single(training_data['text'], training_data['spans'])
    return new_structure, training_data['_id']


def get_span_start(type):
    return '<span class="label ' + type + '">'


def get_span_end():
    return '</span>'


@bp.route('/training/data', methods=['GET'])
def get_training_data_list():
    db = connect_and_get_db()
    training_data_collection = db.get_collection("training_data")

    training_data_list = list(training_data_collection.find({}, {'tokens': 0}))

    training_output = []

    for training_data_item in training_data_list:
        text = training_data_item['text']
        spans = training_data_item['spans']
        task_id = training_data_item['task_id'] if 'task_id' in training_data_item else None

        annotated_text = decorate_text_with_annotations(text, spans)
        training_output.append({
            "id": str(training_data_item['_id']),
            "text": text,
            "status": training_data_item['status'],
            "timestamp": training_data_item['timestamp'].replace(
                microsecond=0).isoformat() if "timestamp" in training_data_item else "",
            "annotated_text": annotated_text,
            "task_id": task_id,
            "hash": training_data_item['hash'],
            "corrected_record_id": training_data_item['corrected_record_id']
        })

    return Response(json.dumps(training_output, default=json_serial), mimetype="application/json")


def decorate_text_with_annotations(text, spans):
    sorted_spans = list(sorted(spans, key=lambda item: item['offset_start']))
    annotated_text = ""
    start = 0
    for span in sorted_spans:
        type = span['type'].replace("<", "").replace(">", "")
        annotated_text += text[start: span['offset_start']] + get_span_start(type) + text[
                                                                                     span['offset_start']: span[
                                                                                         'offset_end']] + get_span_end()
        start = span['offset_end']
    annotated_text += text[start: len(text)]
    return annotated_text


@bp.route("/label/studio/projects", methods=['GET'])
def get_projects_label_studio():
    authentication_token = get_label_studio_token()

    from label_studio_sdk import Client
    ls = Client(url=config['label-studio']['url'], api_key=authentication_token)

    ls.check_connection()
    projects = None
    try:
        projects = ls.get_projects()
    except Exception as e:
        abort(e.response.status_code, message="Error when fetching data from label studio",
              detail=json.loads(e.response.text)['detail'])

    if projects is None or len(projects) == 0:
        abort(404, "No project were found.")

    result_projects = []

    for project in projects:
        params = project.params
        result_projects.append({
            'id': params['id'],
            'title': params['title'],
            'description': params['description']
        })

    return Response(json.dumps(result_projects, default=json_serial), mimetype="application/json")


def get_label_studio_token():
    if 'Authentication' not in request.headers:
        abort(400, "The authentication token should be provided in the headers. ")
    elif not request.headers['Authentication'].startswith("Token "):
        abort(400, "The authentication token must start with 'Token'")
    authentication_token = request.headers['Authentication'].replace("Token ", "")
    return authentication_token


@bp.route("/label/studio/project/<project_id>", methods=['GET'])
def get_project_label_studio(project_id):
    authentication_token = get_label_studio_token()

    from label_studio_sdk import Client
    ls = Client(url=config['label-studio']['url'], api_key=authentication_token)

    ls.check_connection()
    try:
        project = ls.get_project(project_id)
    except Exception as e:
        abort(e.response.status_code, message="Error when fetching data from label studio",
              detail=json.loads(e.response.text)['detail'])

    if project is None:
        abort(404, "No project were found.")

    output_project_format = {
        'params': project.params,
        'parsed_label_config': project.parsed_label_config,
        'tasks': project.tasks,
        'tasks_ids': project.tasks_ids
    }

    return Response(json.dumps(output_project_format, default=json_serial), mimetype="application/json")


@bp.route("/label/studio/project/<project_id>/records", methods=['POST', 'PUT'])
def post_tasks_to_label_studio_project(project_id):
    db = connect_and_get_db()
    tasks_to_send, ids = get_training_data_by_status('new', db)

    if len(tasks_to_send) == 0:
        abort(404, "No training data to send. All data has been already transferred. ")

    authentication_token = get_label_studio_token()

    from label_studio_sdk import Client
    ls = Client(url=config['label-studio']['url'], api_key=authentication_token)

    ls.check_connection()
    try:
        project = ls.get_project(project_id)
    except Exception as e:
        abort(e.response.status_code, message="Error when fetching data from label studio",
              detail=json.loads(e.response.text)['detail'])

    if project is None:
        abort(404, "No project were found.")

    try:
        result = project.import_tasks(tasks_to_send)
    except Exception as e:
        abort(e.response.status_code, message="Error when sending data to label studio",
              detail=json.loads(e.response.text)['detail'])

    if len(ids) != len(result):
        abort(500, "The training_data ids length did not match the identifier length. Something was lost on the way. ")

    training_data_collection = db.get_collection("training_data")
    updates = []
    ids_mapping = []
    for idx, identifier in enumerate(ids):
        updates.append(UpdateOne({'_id': identifier}, {'$set': {'status': 'in_progress', 'task_id': result[idx]}}))
        ids_mapping.append({
            'record_id': str(identifier),
            'task_id': result[idx]
        })

    op_result = training_data_collection.bulk_write(updates)

    result_response = {
        'ids_mapping': ids_mapping,
        'modified': op_result.modified_count
    }

    return Response(json.dumps(result_response, default=json_serial), mimetype="application/json")


@bp.route("/label/studio/project/<project_id>/record/<record_id>", methods=['POST', 'PUT'])
def post_task_to_label_studio_project(project_id, record_id):
    db = connect_and_get_db()
    task_to_send, task_id = get_training_data_by_id_and_status(record_id, 'new', db)

    if not task_to_send:
        abort(404, "No available training data to send. The requested record is not available"
                   " or it had been sent already. ")

    authentication_token = get_label_studio_token()

    from label_studio_sdk import Client
    ls = Client(url=config['label-studio']['url'], api_key=authentication_token)

    ls.check_connection()
    try:
        project = ls.get_project(project_id)
    except Exception as e:
        abort(e.response.status_code, message="Error when fetching data from label studio",
              detail=json.loads(e.response.text)['detail'])

    if project is None:
        abort(404, "No project were found.")

    try:
        result = project.import_tasks(task_to_send)
    except Exception as e:
        abort(e.response.status_code, message="Error when sending data to label studio",
              detail=json.loads(e.response.text)['detail'])

    if len(result) != 1:
        abort(500, "One result is expected but not obtained. Something was lost on the way. ")

    training_data_collection = db.get_collection("training_data")
    op_result = training_data_collection.update_one({'_id': task_id},
                                                    {'$set': {'status': 'in_progress', 'task_id': result[0]}})

    result_response = {
        'ids_mapping': [
            {str(task_id): result[0]}
        ],
        'modified': op_result.modified_count
    }

    return Response(json.dumps(result_response, default=json_serial), mimetype="application/json")


@bp.route("/training/data/<id>", methods=['DELETE'])
def delete_training_data_record(id):
    db = connect_and_get_db()
    training_data_collection = db.get_collection("training_data")

    object_id = validateObjectId(id)
    result = training_data_collection.delete_one({"_id": object_id})

    return Response(json.dumps({"deleted": result.deleted_count}, default=json_serial), mimetype="application/json")

# @bp.after_request
# def add_header(r):
#     """
#     Add headers to both force latest IE rendering engine or Chrome Frame,
#     and also to cache the rendered page for 10 minutes.
#     """
#     r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#     r.headers["Pragma"] = "no-cache"
#     r.headers["Expires"] = "0"
#     r.headers['Cache-Control'] = 'public, max-age=0'
#     return r
