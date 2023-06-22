import argparse
import os
import re
import sys
from pathlib import Path
import pymatgen.core as mg
from material2class import ClassResolver

from commons.correction_utils import write_raw_training_data
from process.grobid_client_generic import GrobidClientGeneric
from supercon_batch_mongo_extraction import connect_mongo


def validate_formula(formula):

    try:
        mg.Composition(formula, strict=False)
    except:
        material_formula_with_replacements = re.sub(r'[+-][ZXYzxy]', '', formula)
        try:
            mg.Composition(material_formula_with_replacements, strict=False)
        except Exception as e2:
            return False, str(e2)

    return True, ""


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Process extracted documents and compute the tabular format.")
    parser.add_argument("--config", help="Configuration file", type=Path, required=True)
    parser.add_argument("--database", "-db",
                        help="Set the database name which is normally read from the configuration file", type=str,
                        required=False)
    parser.add_argument("--dry-run", help="Don't write on the database", action="store_true", default=False)
    parser.add_argument("--verbose",
                        help="Print all log information", action="store_true", required=False, default=False)

    args = parser.parse_args()
    config_path = args.config
    db_name = args.database
    dry_run = args.dry_run
    verbose = args.verbose

    if not os.path.exists(config_path):
        print("The config file does not exists. ")
        parser.print_help()
        sys.exit(-1)

    config = GrobidClientGeneric().load_yaml_config_from_file(config_path)

    if db_name is None:
        db_name = config["mongo"]["db"]
    else:
        db_name = db_name

    connection = connect_mongo(config=config)
    db = connection[db_name]
    tabular_collection = db.get_collection("tabular")

    temp_regex = re.compile(r"^([0-9.]+) ?(m?K{1})$")
    # tabular_cursor = tabular_collection.find({"status": {"$not": {"$in": ["empty", "invalid", "removed", "obsolete"]}}})
    tabular_cursor = tabular_collection.find({"status": {"$in": ["new"]}})
    anomalies = []
    for record in tabular_cursor:
        tc = record['criticalTemperature']
        if tc:
            search = temp_regex.search(tc)
            if search:
                value = search.groups()[0]
                unit = search.groups()[1]
                anomaly = {
                    "id": record['_id'],
                    "type": "tc",
                    "value": tc
                }

                try:
                    float_value = float(value)
                except:
                    anomaly['description'] = "Tc not parseable"
                    anomalies.append(anomaly)
                    continue

                if float_value > 270:
                    anomaly['description'] = "Tc too high"
                    anomalies.append(anomaly)
                    continue
                elif value.startswith("-"):
                    anomaly['description'] = "Tc negative"
                    anomalies.append(anomaly)
                    continue

        formula = record['formula'] if 'formula' in record else None
        variables = record['variables'] if 'variables' in record else None
        if formula and not variables:
            valid, exception = validate_formula(formula)
            if not valid:
                anomalies.append(
                    {
                        "id": record['_id'],
                        "type": "formula",
                        "value": formula,
                        "description": exception
                    }
                )

    if dry_run:
        if verbose:
            for anomaly in anomalies:
                print(anomaly['type'], "-", anomaly['value'], "-", anomaly['description'])

    else:
        print("Writing on the database:", db_name, config['mongo']['server'])
        input_value = input("Continue [y/N]")
        if input_value == "y":
            document_collection = db.get_collection("document")
            training_data_collection = db.get_collection("training_data")
            for anomaly in anomalies:
                if verbose:
                    print(anomaly['type'], "-", anomaly['value'], "-", anomaly['description'])

                    old_doc = tabular_collection.find_one({'_id': anomaly['id'], "status": "new"})
                    if old_doc:
                        new_status = 'invalid'
                        new_type = 'automatic'
                        error_type = "anomaly_detection"

                        changes = {'status': new_status, 'type': new_type, 'error_type': error_type}

                        tabular_collection.update_one({'_id': anomaly['id']}, {'$set': changes})
                        training_data_id = write_raw_training_data(old_doc, anomaly['id'], document_collection,
                                                                   training_data_collection,
                                                                   action="anomaly")

                    else:
                        print("Document", anomaly['id'], "not found, ignoring it.")


        else:
            print("Aborting")

    print("Anomalies in Tc:", len(list(filter(lambda x: x['type'] == "tc", anomalies))))
    print("Anomalies in Materials:", len(list(filter(lambda x: x['type'] == "formula", anomalies))))
