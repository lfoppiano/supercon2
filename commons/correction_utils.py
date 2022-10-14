from collections import OrderedDict
from datetime import datetime

from bson import ObjectId
from deepdiff import DeepDiff
from pymongo import DESCENDING


def collect_corrections(corrected_formula, corrected_tc, corrected_pressure):
    corrections = {}
    if corrected_formula is not None and str(corrected_formula) != 'nan':
        print("Correcting formula with", corrected_formula)
        corrections['formula'] = corrected_formula

    if corrected_tc is not None and str(corrected_tc) != 'nan':
        print("Correcting tc with", corrected_tc)
        corrections['criticalTemperature'] = corrected_tc

    if corrected_pressure is not None and str(corrected_pressure) != 'nan':
        print("Correcting pressure with", corrected_pressure)
        corrections['appliedPressure'] = corrected_pressure

    return corrections


def find_differences(new, old, ignored_fields=[]):
    # exclude_paths = {"root['type']", "root['status']", "root['_id']", "root['previous']"}

    differences = DeepDiff(new, old, ignore_order=True,
                           exclude_paths={"root['"+str(field)+"']" for field in ignored_fields})

    return differences


def write_correction(old_doc, corrections, collection, dry_run: bool = False, skip_none=True,
                     remove_trailing_space=True, error_type=None) -> ObjectId:
    """Write corrections into the database"""

    new_doc = post_process_fields(old_doc, remove_trailing_space, skip_none)
    correction_clean = post_process_fields(corrections, remove_trailing_space, skip_none)

    differences = find_differences(new_doc, correction_clean, ignored_fields=['type', 'status', '_id', 'previous', 'error_type'])

    if len(differences) == 0:
        raise Exception(
            "The updated record is the same as the original one. "
            "Spaces are being removed. Are you sure you didn't add just spaces? ")

    for field, value in correction_clean.items():
        new_doc[field] = value

    old_doc['status'] = "obsolete"  ## 'obsolete' means that another record is taking over
    # doc['type'] = "automatic"

    # We save the error type in the previous document
    if error_type: 
        old_doc['error_type'] = error_type

    obsolete_id = old_doc['_id']
    new_doc['previous'] = obsolete_id
    new_doc['type'] = 'manual'
    new_doc['status'] = 'valid'
    new_doc['timestamp'] = datetime.utcnow()

    # Cleanup
    for x in ['id', '_id']:
        if x in new_doc:
            del new_doc['_id']

    if dry_run:
        print("Updating record with id: ", old_doc['_id'],
              "and setting flags 'status'='obsolete' and 'type'='automatic'.")
        print("Creating new record with status'='valid' and 'type'='manual'\n", new_doc)

        print("Creating training data. Saving the sentence for the moment.")
        new_doc_id = "00000"
    else:
        collection.update_one({
            '_id': old_doc['_id']
        }, {
            '$set': {
                'status': 'obsolete',
                'type': 'automatic'
            }
        }, upsert=False)
        result = collection.insert_one(new_doc)
        new_doc_id = result.inserted_id

    return new_doc_id


def post_process_fields(doc, remove_trailing_space=True, skip_none=True):
    """Remove trailing spaces and None fields"""

    new_doc = OrderedDict()

    for field, value in doc.items():
        if value is None and skip_none:
            continue
        elif type(value) is str and remove_trailing_space:
            new_doc[field] = str.strip(value)
        else:
            new_doc[field] = value
    return new_doc


def write_raw_training_data(doc, new_doc_id, document_collection, training_data_collection, dry_run=False) -> ObjectId:
    """Training data generation"""

    hash = doc['hash']

    # We get the latest document
    document_latest_version = \
        document_collection.find({'hash': hash}).sort([('timestamp', DESCENDING)]).limit(1)[0]

    print("Document found ", document_latest_version["_id"])

    for passage in document_latest_version['passages'] if 'passages' in document_latest_version else []:
        spans = passage['spans'] if 'spans' in passage else []
        for span in spans:
            if span['id'] == doc['materialId']:
                print("Found span and sentence. Pull them out. ")
                # annotated_text, features = create_training_data_from_passage(passage)

                if dry_run:
                    print("Adding training data for span", span['id'])
                else:
                    result = training_data_collection.insert_one(
                        {
                            "text": passage['text'],
                            "spans": passage['spans'],
                            "tokens": passage['tokens'],
                            "hash": hash,
                            "corrected_record_id": str(new_doc_id),
                            "status": "new",
                            "timestamp": datetime.utcnow()
                        }
                    )
                    return result.inserted_id

    print("If we are here, it means we did not manage to identify the correct passage to create the training data. ")
    return None
