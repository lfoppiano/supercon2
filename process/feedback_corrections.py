import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from commons.correction_utils import collect_corrections, write_correction, write_raw_training_data
from commons.mongo_utils import connect_mongo
from process.grobid_client_generic import GrobidClientGeneric

# supercon_sakai: database containing the re-processed documents corrected by sakai-san
# supercon_sakai_original: database containing the original records corrected by sakai-san

# This part will be implemented in the service
from supercon2.service import rollback


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


def create_as_correct(document, collection, dry_run=False):
    if dry_run:
        print("Creating document as corrected. ")
        return

    document['status'] = 'valid'
    document['type'] = 'manual'
    return collection.insert_one(document)


def flag_as_correct(doc_id, collection, dry_run=False):
    if dry_run:
        print("Flagging document with id ", doc_id, "as corrected. ")
        return

    status = 'valid'
    type = 'manual'

    changes = {'status': status, 'type': type}
    return collection.update_one({'_id': doc_id}, {'$set': changes})


def flag_as_invalid(doc_id, collection, dry_run=False):
    if dry_run:
        print("Flagging document with id ", doc_id, "as invalid (should not have been extracted). ")
        return

    status = 'invalid'
    type = 'manual'

    changes = {'status': status, 'type': type}
    return collection.update_one({'_id': doc_id}, {'$set': changes})


def process(corrections_file, database, dry_run=False):
    changes_report = []

    tabular_collection = database.get_collection("tabular")
    document_collection = database.get_collection("document")
    training_data_collection = database.get_collection("training_data")

    df = pd.read_excel(corrections_file, sheet_name=1, usecols="A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U")
    df = df.replace({np.nan: None})
    for index, row in df.iterrows():
        status = row[0]  # A

        if status is None:
            continue

        raw_material = row[1]
        name = row[2]  # C
        formula = row[3]
        corrected_formula = row[4]  # E
        doping = row[5]
        tc = row[6]
        corrected_tc = row[7]
        pressure = row[8]
        corrected_pressure = row[9]
        shape = row[10]
        material_class = row[11]
        section = row[12]
        sub_section = row[13]
        hash = row[14]
        doi = row[15]
        authors = row[16]
        title = row[17]
        publisher = row[18]
        journal = row[19]
        year = row[20]

        # Iterate on the database records
        documents = tabular_collection.find({"hash": hash, "type": "automatic", "status": "new"})

        matching = False
        for doc in documents:
            if doc['rawMaterial'] != raw_material:
                continue

            if doc['formula'] != formula:
                continue

            if doc["criticalTemperature"] != tc:
                continue

            if doc["appliedPressure"] != pressure:
                continue

            if doc["section"] != section:
                continue

            if doc["subsection"] != sub_section:
                continue

            print("Found record corresponding to material:", doc['_id'], ": ")
            print("- Raw material ", doc['rawMaterial'], "->", raw_material)
            print("- Formula ", doc['formula'], "->", formula)
            print("- Tc ", doc['criticalTemperature'], "->", tc)
            print("- Applied pressure ", doc['appliedPressure'], "->", pressure)
            print("- section ", doc['section'], "->", section)
            print("- subsection ", doc['subsection'], "->", sub_section)
            matching = True

            if status == "correct":
                # since there is no change in the data, we don't create a new record
                flag_as_correct(doc['_id'], tabular_collection, dry_run=dry_run)
                print(" --> flag as correct")
                changes_report.append({"id": str(doc["_id"]), "new_id": str(None),
                                "status": status, "action": "update", "hash": doc["hash"]})
                break
            elif status == "invalid":
                flag_as_invalid(doc['_id'], tabular_collection, dry_run=dry_run)
                print(" --> flag as invalid")
                changes_report.append({"id": str(doc["_id"]), "new_id": str(None),
                                "status": status, "action": "update", "hash": doc["hash"]})
            else:
                print(" --> create new record with corrected data")

            # At this point the record was corrected in the Excel, so I apply the corrections
            corrections = collect_corrections(corrected_formula, corrected_tc, corrected_pressure)

            if len(corrections.keys()) == 0:
                print("This record was identified as to be corrected, but found no usable data.")
                changes_report.append({"id": str(doc["_id"]), "new_id": str(None),
                                "status": status, "action": str(None), "hash": doc["hash"]})
                break
            else:
                new_id = None
                training_data_id = None
                try:
                    new_id = write_correction(doc, corrections, tabular_collection, dry_run=dry_run)
                    training_data_id = write_raw_training_data(doc, new_id, document_collection,
                                                               training_data_collection)
                    changes_report.append({"id": str(doc["_id"]), "new_id": str(new_id),
                                    "status": status, "action": "update", "hash": doc["hash"]})
                    break
                except Exception as e:
                    print("There was an exception. Rolling back. ")
                    rollback(new_id, doc, training_data_id, tabular_collection, training_data_collection)
                    changes_report.append({"id": doc["_id"], "new_id": str(None),
                                    "status": status, "action": "rollback", "hash": doc["hash"]})
                    break

        if not matching:
            print("Record did not match!")
            print("- Raw material ", raw_material)
            print("- Formula ", formula)
            print("- Tc ", tc)
            print("- Applied pressure ", pressure)
            print("- section ", section)
            print("- subsection ", sub_section)
            print("- hash ", hash)

            if status == 'correct' or status == 'missing':
                corrections = collect_corrections(corrected_formula, corrected_tc, corrected_pressure)

                hash_no_original_document = '0000000000'
                new_document = {
                    'rawMaterial': raw_material,
                    'formula': corrections['formula'] if 'formula' in corrections else formula,
                    'criticalTemperature': corrections[
                        'criticalTemperature'] if 'criticalTemperature' in corrections else tc,
                    'appliedPressure': corrections['appliedPressure'] if 'appliedPressure' in corrections else pressure,
                    'section': section,
                    'subsection': sub_section,
                    'name': name,
                    'doping': doping,
                    'shape': shape,
                    'classification': material_class,
                    'hash': hash_no_original_document,
                    'doi': doi,
                    'authors': authors,
                    'title': title,
                    'publisher': publisher,
                    'journal': journal,
                    'year': year
                }

                result_operation = create_as_correct(new_document, tabular_collection, dry_run=dry_run)
                inserted_id = '1234' if result_operation is None else result_operation.inserted_id
                print(" --> insert as correct")
                changes_report.append({"id": str(None), "new_id": str(inserted_id),
                                "status": status, "action": "insert", "hash": hash_no_original_document})
            else:
                print(" --> invalid, let's ignore it. ")
                changes_report.append({"id": str(None), "new_id": str(None), "status": status, "action": str(None)})

    return changes_report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Feedback to SuperCon2 corrections from an Excel file")
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
    parser.add_argument("--report-file", help="Dump report in a file. If the file exists it's overriden", type=Path,
                        required=False, default=None)

    args = parser.parse_args()

    corrections = args.corrections
    config_path = args.config
    dry_run = args.dry_run
    db_name = args.database
    verbose = args.verbose
    report_file = args.report_file

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

    report = process(corrections, database, dry_run=dry_run)

    if report_file is None:
        print(json.dumps(report))
    else:
        if report_file.is_dir:
            with open(report_file, 'w') as f:
                json.dump(report, f)
        else:
            print("Invalid file", report_file, "The report file cannot be produced. ")
