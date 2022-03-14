import json

import gridfs
from apiflask import APIBlueprint, abort, output, input
from bson import ObjectId
from bson.errors import InvalidId
from flask import render_template, Response, url_for

from process.supercon_batch_mongo_extraction import connect_mongo
from process.utils import json_serial
from supercon2.schemas import Publishers, Record, Years, Flag, RecordParamsIn
from supercon2.utils import load_config_yaml

bp = APIBlueprint('supercon', __name__)
config = []


@bp.route('/version')
def get_version():
    version = None
    if version is None:
        try:
            with open("resources/version.txt", 'r') as fv:
                file_version = fv.readline()
            version = file_version.strip() if file_version != "" and file_version is not None else "unknown"
        except:
            version = "unknown"

    info_json = {"name": "supercon2", "version": version}
    return info_json


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/<page>')
def render_page(page):
    return render_template(page)


# @bp.route('/annotation/feedback', methods=['POST'])
# def annotation_feedback():
#     print("Received feedback request. id=" + str(request.form))
#     return request.form


@bp.route('/publishers')
@output(Publishers)
def get_publishers():
    connection = connect_mongo(config=config)
    db_name = config['mongo']['db']
    db = connection[db_name]

    filtered_distinct_publishers = list(filter(lambda x: x is not None, db.tabular.distinct("publisher")))
    return {"publishers": filtered_distinct_publishers}


@bp.route('/years')
@output(Years)
def get_years():
    connection = connect_mongo(config=config)
    db_name = config['mongo']['db']
    db = connection[db_name]

    distinct_years = db.tabular.distinct("year")
    filtered_distinct_years = list(filter(lambda x: x is not None and 1900 < x < 3000, distinct_years))
    return {"years": filtered_distinct_years}


# @bp.route('/process', methods=['POST'])
# def process_pdf():
#     file = request.files['input']
#     grobid = grobid_client_generic(config_path="./config.json")
#     tf = NamedTemporaryFile()
#     tf.write(file.read())
#     result_text = grobid.process_pdf(tf.name, 'processPDF', params={'disableLinking': 'true'},
#                                      headers={'Accept': 'application/json'})
#
#     result_json = json.loads(result_text)
#     new_paragraphs = []
#     paragraphs = result_json['paragraphs']
#     for index, paragraph in enumerate(paragraphs):
#         if 'spans' not in paragraph:
#             new_paragraphs.append(paragraph)
#             continue
#
#         extracted_data_from_paragraphs = RuleBasedLinker().process_paragraph(paragraph)
#         for sentence in extracted_data_from_paragraphs:
#             new_paragraphs.append(sentence)
#
#     result_json['paragraphs'] = new_paragraphs
#
#     return result_json


@bp.route("/stats", methods=["GET"])
def get_stats():
    db_name = config['mongo']['db']
    connection = connect_mongo(config=config)
    db_supercon_dev = connection[db_name]
    tabular_collection = db_supercon_dev.get_collection("tabular")

    pipeline_group_by_publisher = [
        {"$match": {"type": "automatic", "status": "valid"}},
        {"$group": {"_id": "$publisher", "count_records": {"$sum": 1}, "hashes": {"$addToSet": "$hash"}}},
        {"$project": {"_id": 1, "hashes": 1, "count_records": 1, "count_docs": {"$size": "$hashes"}}},
        {"$project": {"hashes": 0}},
        {"$sort": {"count_docs": -1}}
    ]
    by_publisher = tabular_collection.aggregate(pipeline_group_by_publisher)

    pipeline_group_by_year = [
        {"$match": {"type": "automatic", "status": "valid"}},
        {"$group": {"_id": "$year", "count_records": {"$sum": 1}, "hashes": {"$addToSet": "$hash"}}},
        {"$project": {"_id": 1, "hashes": 1, "count_records": 1, "count_docs": {"$size": "$hashes"}}},
        {"$project": {"hashes": 0}},
        {"$sort": {"count_docs": -1}}
    ]
    by_year = tabular_collection.aggregate(pipeline_group_by_year)

    pipeline_group_by_journal = [
        {"$match": {"type": "automatic", "status": "valid"}},
        {"$group": {"_id": "$journal", "count_records": {"$sum": 1}, "hashes": {"$addToSet": "$hash"}}},
        {"$project": {"_id": 1, "hashes": 1, "count_records": 1, "count_docs": {"$size": "$hashes"}}},
        {"$project": {"hashes": 0}},
        {"$sort": {"count_docs": -1}}
    ]
    by_journal = tabular_collection.aggregate(pipeline_group_by_journal)

    return render_template("stats.html", by_publisher=by_publisher, by_year=by_year, by_journal=by_journal)


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


def get_records(type=None, status=None, publisher=None, year=None, start=-1, limit=-1):
    connection = connect_mongo(config=config)
    db_name = config['mongo']['db']
    db_supercon_dev = connection[db_name]

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
        query['status'] = {"$in": ['valid', 'invalid']}
    else:
        query['status'] = status

    entries = []
    tabular_collection = db_supercon_dev.get_collection("tabular")

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


@bp.route("/automatic_database", methods=["GET"])
def get_automatic_database():
    return render_template("automatic_database.html")


@bp.route("/manual_database", methods=["GET"])
def get_manual_database():
    return render_template("manual_database.html")


@bp.route('/document/<hash>', methods=['GET'])
def get_document(hash):
    return render_template("document.html", hash=hash)


@bp.route('/annotation/<hash>', methods=['GET'])
def get_annotations(hash):
    """Get annotations (latest version)"""
    db_name = config['mongo']['db']
    connection = connect_mongo(config=config)
    db = connection[db_name]
    annotations = db.get_collection("document").find({"hash": hash}).sort("timestamp", -1)
    annotation = annotations[0]
    del annotation["_id"]
    return Response(json.dumps(annotation, default=json_serial), mimetype="application/json")


@bp.route('/pdf/<hash>', methods=['GET'])
def get_binary(hash):
    '''GET PDF / binary file '''
    connection = connect_mongo(config=config)
    db_name = config['mongo']['db']
    db_supercon_dev = connection[db_name]
    fs_binary = gridfs.GridFS(db_supercon_dev, collection='binary')

    file = fs_binary.find_one({"hash": hash})
    if file is None:
        return "Document with identifier=" + str(hash) + " not found.", 404
    else:
        return Response(fs_binary.get(file._id).read(), mimetype='application/pdf')


@bp.route('/record/<id>', methods=['GET'])
@output(Record)
def get_record(id):
    object_id = validateObjectId(id)
    connection = connect_mongo(config=config)
    db_name = config['mongo']['db']
    db = connection[db_name]
    record = db.get_collection("tabular").find_one({"_id": object_id})

    record['id'] = str(record['_id'])
    return record


@bp.route('/record/<id>/flags', methods=['GET'])
@output(Flag)
def get_flag(id):
    object_id = validateObjectId(id)
    connection = connect_mongo(config=config)
    db_name = config['mongo']['db']
    db = connection[db_name]
    record = db.get_collection("tabular").find_one({"_id": object_id}, {'_id': 0, 'type': 1, 'status': 1})

    return record


@bp.route('/record/<id>/flag', methods=['PUT', 'PATCH'])
@output(Flag)
def flag_record(id):
    object_id = validateObjectId(id)
    connection = connect_mongo(config=config)
    db_name = config['mongo']['db']
    db = connection[db_name]
    tabular_collection = db.get_collection("tabular")
    record = tabular_collection.find_one({"_id": object_id})
    if record is None:
        return 404
    else:
        new_status = 'invalid'
        new_type = 'manual'

        changes = {'status': new_status, 'type': new_type}

        tabular_collection.update_one({'_id': record['_id']}, {'$set': changes})
        return changes, 200


def validateObjectId(id):
    try:
        return ObjectId(id)
    except InvalidId as e:
        abort(400, "Invalid ObjectID")


@bp.route('/record/<id>/unflag', methods=['PUT', 'PATCH'])
@output(Flag)
def unflag_record(id):
    object_id = validateObjectId(id)
    connection = connect_mongo(config=config)
    db_name = config['mongo']['db']
    db = connection[db_name]
    tabular_collection = db.get_collection("tabular")

    record = tabular_collection.find_one({"_id": object_id})
    if record is None:
        return "Record with id=" + id + " not found.", 404
    else:
        status = 'valid'
        type = 'automatic'

        changes = {'status': status, 'type': type}
        tabular_collection.update_one({'_id': record['_id']}, {'$set': changes})
        return changes, 200


@bp.route('/config', methods=['GET'])
def get_config(config_file='config.yaml'):
    return load_config_yaml(config_file)


@bp.route('/training_data', methods=['GET'])
def get_training_data():
    return render_template("training_data.html")


@bp.route('/training/data/<id>', methods=['GET'])
def export_training_data(id):
    object_id = validateObjectId(id)
    connection = connect_mongo(config=config)
    db_name = config['mongo']['db']
    db = connection[db_name]
    training_data_collection = db.get_collection("training_data")

    single_training_data = training_data_collection.find_one({'_id': object_id}, {'tokens': 0})

    single_training_data['id'] = str(single_training_data['_id'])
    del single_training_data['_id']

    # workaround - to be removed
    if type(single_training_data['corrected_record_id']) == ObjectId:
        single_training_data['corrected_record_id'] = str(single_training_data['corrected_record_id'])

    return single_training_data


def get_span_start(type):
    return '<span class="label ' + type + '">'


def get_span_end():
    return '</span>'


@bp.route('/training/data', methods=['GET'])
def get_training_data_list():
    connection = connect_mongo(config=config)
    db_name = config['mongo']['db']
    db = connection[db_name]
    training_data_collection = db.get_collection("training_data")

    training_data_list = list(training_data_collection.find({}, {'tokens': 0}))

    training_output = []

    for training_data_item in training_data_list:
        text = training_data_item['text']
        spans = training_data_item['spans']

        sorted_spans = list(sorted(spans, key=lambda item: item['offset_start']))
        annotated_text = ""
        start = 0
        for span in sorted_spans:
            type = span['type'].replace("<", "").replace(">", "")
            annotated_text += text[start: span['offset_start']] + get_span_start(type) + text[span['offset_start']: span[
                'offset_end']] + get_span_end()
            start = span['offset_end']

        annotated_text += text[start: len(text)]
        training_output.append({
            "id": str(training_data_item['_id']),
            "text": text,
            "annotated_text": annotated_text,
            "hash": training_data_item['hash'],
            "corrected_record_id": training_data_item['corrected_record_id']
        })

    return Response(json.dumps(training_output, default=json_serial), mimetype="application/json")
