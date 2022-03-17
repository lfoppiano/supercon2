import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pymongo import DESCENDING

from commons.correction_utils import collect_corrections, write_correction
from commons.mongo_utils import connect_mongo
from process.grobid_client_generic import GrobidClientGeneric


# supercon_sakai: database containing the re-processed documents corrected by sakai-san
# supercon_sakai_original: database containing the original records corrected by sakai-san

# This part will be implemented in the service
def create_training_data_from_passage(passage):
    if 'spans' not in passage or 'text' not in passage:
        return None

    text = passage['text']
    spans = passage['spans']
    tokens = passage['tokens']

    ## Create the annotated text with "spans" and "tokens" and use "text" for validation
    start = 0
    annotated_text = ""
    for span in spans:
        type = span['type']
        ANNOTATION_START = '<rs type="' + type + '">'
        ANNOTATION_END = '</rs>'
        offset_start = span['offset_start']
        offset_end = span['offset_end']
        annotated_text += text[start:offset_start] + ANNOTATION_START + text[offset_start:offset_end] + ANNOTATION_END
        start = offset_end

    annotated_text += text[start:]

    ## Features
    # fluctuations fluctuations f fl flu fluc s ns ons ions NOCAPS NODIGIT 0 NOPUNCT fluctuations xxxx x SAMEFONT SAMEFONTSIZE false false BASELINE false

    features = ""

    for token in tokens:
        text_ = str(token['text'])
        text_, text_.lower(), text_[0], text_[0:1], text_[0:2], text_[0:3], text_[-1], text_[-1:-2], text_[
                                                                                                     -2:-3], text_[
                                                                                                             -3:-4],

    return annotated_text, features


def write_raw_training_data(doc, new_doc_id, document_collection, training_data_collection):
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

                training_data_id = training_data_collection.insert_one(
                    {
                        "text": passage['text'],
                        "spans": passage['spans'],
                        "tokens": passage['tokens'],
                        "hash": hash,
                        "corrected_record_id": str(new_doc_id),
                        "status": "new"
                    }
                )
                return training_data_id

    print("If we are here, it means we did not manage to identify the correct passage to create the training data. ")
    return None


def flag_as_correct(doc_id, collection, dry_run=False):
    if dry_run:
        print("Flagging document with id ", doc_id, "as corrected. ")
        return

    status = 'valid'
    type = 'manual'

    changes = {'status': status, 'type': type}
    return collection.update_one({'_id': doc_id}, {'$set': changes})


def process(corrections_file, database, dry_run=False):
    tabular_collection = database.get_collection("tabular")
    document_collection = database.get_collection("document")
    training_data_collection = database.get_collection("training_data")

    df = pd.read_excel(corrections_file, sheet_name=1, usecols="A,B,D,E,G,H,I,J,O,M,N")
    df.replace({np.nan: None})
    for index, row in df.iterrows():
        status = row[0]
        raw_material = row[1]
        formula = row[2]
        corrected_formula = row[3]
        tc = row[4]
        corrected_tc = row[5]
        pressure = row[6]
        corrected_pressure = row[7]
        section = row[8]
        sub_section = row[9] if str(row[9]) != 'nan' else None
        hash = row[10]

        documents = tabular_collection.find({"hash": hash, "status": "valid"})

        for doc in documents:
            if status == "correct":
                flag_as_correct(doc['_id'], tabular_collection, dry_run=dry_run)
                continue

            if doc['rawMaterial'] != raw_material:
                continue

            if doc["criticalTemperature"] != tc:
                continue

            if doc["appliedPressure"] != pressure:
                continue

            if doc["section"] != section:
                continue

            if doc["subsection"] != sub_section:
                continue

            print("Found record corresponding to material:", doc['rawMaterial'])

            corrections = collect_corrections(corrected_formula, corrected_tc, corrected_pressure)

            if len(corrections.keys()) == 0:
                print("This record was identified as to be corrected, but found no usable data.")
            else:
                new_doc_id = write_correction(doc, corrections, tabular_collection, dry_run=dry_run)

                write_raw_training_data(doc, new_doc_id, document_collection, training_data_collection)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Feedback to supercon2 corrections from an Excel file")
    parser.add_argument("--corrections", help="Correction file (csv or excel)", type=Path, required=True)
    parser.add_argument("--config", help="Configuration file", type=Path, required=True)
    parser.add_argument("--dry-run", help="Perform the operations without writing on the database.",
                        action="store_true",
                        required=False)
    parser.add_argument("--database", "-db",
                        help="Force the database name which is normally read from the configuration file", type=str,
                        required=False,
                        default=None)
    parser.add_argument("--verbose",
                        help="Print all log information",
                        action="store_true",
                        required=False, default=False)

    args = parser.parse_args()

    corrections = args.corrections
    config_path = args.config
    dry_run = args.dry_run
    db_name = args.database
    verbose = args.verbose

    if not os.path.exists(config_path):
        print("The config file does not exists. ")
        parser.print_help()
        sys.exit(-1)

    if not os.path.exists(corrections):
        print("The corrections file does not exists.")
        parser.print_help()
        sys.exit(-1)

    config = GrobidClientGeneric().load_yaml_config_from_file(config_path)
    mongo = connect_mongo(config)

    if db_name is None:
        db_name = config["mongo"]["db"]
    database = mongo.get_database(db_name)

    process(corrections, database, dry_run=dry_run)
