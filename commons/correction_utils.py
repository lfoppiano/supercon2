import copy
import datetime


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


def write_correction(doc, corrections, collection, dry_run: bool = False):
    """Write corrections into the database"""

    new_doc = copy.copy(doc)

    for field, value in corrections.items():
        new_doc[field] = value

    doc['status'] = "obsolete"  ## 'obsolete' means that another record is taking over
    doc['type'] = "automatic"
    obsolete_id = doc['_id']
    new_doc['previous'] = obsolete_id
    new_doc['type'] = 'manual'
    new_doc['status'] = 'valid'
    new_doc['timestamp'] = datetime.datetime.now().isoformat()
    del new_doc['_id']

    if dry_run:
        print("Updating record with id: ", doc['_id'],
              "and setting flags 'status'='obsolete' and 'type'='automatic'.")
        print("Creating new record with status'='valid' and 'type'='manual'\n", new_doc)

        print("Creating training data. Saving the sentence for the moment.")
        new_doc_id = "00000"
    else:
        collection.update_one({
            '_id': doc['_id']
        }, {
            '$set': {
                'status': 'obsolete',
                'type': 'automatic'
            }
        }, upsert=False)
        result = collection.insert_one(new_doc)
        new_doc_id = result.inserted_id

    return new_doc_id