import argparse
import json
import os
import re
import sys
from pathlib import Path

import pymatgen.core as mg
import requests
from textdistance import RatcliffObershelp

from commons.correction_utils import write_raw_training_data
from process.grobid_client_generic import GrobidClientGeneric
from supercon_batch_mongo_extraction import connect_mongo


def validate_formula_strict(formula):
    try:
        mg.Composition(formula, strict=False)
    except:
        material_formula_with_replacements = re.sub(r'[+-][ZXYzxy]', '', formula)
        try:
            mg.Composition(material_formula_with_replacements, strict=False)
        except Exception as e2:
            return False, str(e2)

    return True, ""


def validate_formula_naive(formula):
    formula_parser_url = "http://falcon.nims.go.jp/material/nlp/stable/convert/formula/composition"

    data = {'input': formula}
    response = requests.post(formula_parser_url, data=data)

    if response.status_code != 200:
        if response.status_code == 400:
            return False, ""
        else:
            print("Cannot parse the formula")
            return True, ""

    else:
        if response.text == "{}":
            return False, ""

        return True, ""
        # comp = json.loads(response.text)['composition']
        #
        # result = ''
        # for key, value in comp.items():
        #     if value == '1':
        #         result += key + ' '
        #     else:
        #         result += key + value + ' '
        #
        # line.insert(header.index("parsed_formula"), comp)
        # line.insert(header.index("formatted_formula"), result)


def parse_tc_regex(tc) -> float:
    search = temp_regex.search(tc)
    if search:
        value = search.groups()[0]
        unit = search.groups()[1]
        float_value = float(value)
        if "K" in unit and unit != "K":
            if unit.startswith("m"):
                float_value *= 1000

            return float_value
        elif unit == "K":
            return float_value
        else:
            raise Exception("Value not in Kelvin. Might not be a Tc. ")
    else:
        raise Exception("No Tc found")


grobid_quantities_url = "http://falcon.nims.go.jp/quantities/stable"
# grobid_quantities_url = "https://lfoppiano-grobid-quantities.hf.space"
quantity_text_url = grobid_quantities_url + "/service/processQuantityText"


def parse_pressure_regex(pressure):
    if RatcliffObershelp().normalized_similarity(applied_pressure, "ambient pressure") > 0.9:
        return 0.0

    search = pressure_regex.search(pressure)
    if search:
        value = search.groups()[0]
        unit = search.groups()[1]
        float_value = float(value)
        if "Pa" in unit and unit != "Pa":
            if unit.startswith("k"):
                float_value *= 1000
            if unit.startswith("G"):
                float_value *= 1000000000
            return float_value
        elif unit == "Pa":
            return float_value
        elif "bar" in unit:
            float_value *= 100000
            if unit != "bar":
                if unit.startswith("k"):
                    float_value *= 1000

            return float_value
        else:
            raise Exception("Value not in Pascal. Might not be an applied pressure. ")
    else:
        raise Exception("No pressure found")


def parse_quantity(quantity_raw_text, type="tc"):
    data = str({'text': quantity_raw_text})
    response = requests.post(quantity_text_url, files={"text": data})

    if response.status_code == 200:
        parsed_response = json.loads(response.text)
        if 'measurements' in parsed_response:
            quantities_value = []
            for found_measurement in parsed_response['measurements']:
                type = found_measurement['type']
                if type == 'value':
                    quantity_obj = found_measurement['quantity']
                    quantity_value = get_value_as_float(quantity_obj)
                    quantities_value.append(quantity_value)
                elif type == 'interval':
                    if 'quantityLeast' in found_measurement:
                        quantity_obj = found_measurement['quantityLeast']
                        quantities_value.append(get_value_as_float(quantity_obj))
                    if 'quantityMost' in found_measurement:
                        quantity_obj = found_measurement['quantityMost']
                        quantities_value.append(get_value_as_float(quantity_obj))

                elif type == 'listc':
                    quantities_obj = found_measurement['quantities']
                    for quantity_obj in quantities_obj:
                        quantities_value.append(get_value_as_float(quantity_obj))

            return quantities_value

    if type == "tc":
        float_value = parse_tc_regex(quantity_raw_text)
        return [float_value]
    elif type == "pressure":
        float_value = parse_pressure_regex(quantity_raw_text)
        return [float_value]


def get_value_as_float(quantity_obj):
    quantity_value = 0.0
    if 'normalizedUnit' in quantity_obj:
        normalized_quantity = quantity_obj['normalizedQuantity']
        # normalized_unit = quantity_obj['normalizedUnit']['name']
        quantity_value = float(normalized_quantity)
    elif 'parsedValue' in quantity_obj:
        parsed_quantity = quantity_obj['parsedValue']['parsed']
        quantity_value = float(parsed_quantity)
    return quantity_value


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

    temp_regex = re.compile(r"^([0-9.,]+) ?(m?K{1})$")
    pressure_regex = re.compile(r"^([0-9.,]+) ?([Gk]?Pa{1})$")
    # tabular_cursor = tabular_collection.find({"status": {"$not": {"$in": ["empty", "invalid", "removed", "obsolete"]}}})
    tabular_cursor_count = tabular_collection.count_documents({"status": {"$in": ["new", "invalid"]}})
    tabular_cursor = tabular_collection.find({"status": {"$in": ["new", "invalid"]}})
    anomalies = []
    materials = {}

    float_value = -1.0
    for record in tabular_cursor:
        tc = record['criticalTemperature']
        # tc_float_value = 0.0
        if tc:
            anomaly = {
                "id": record['_id'],
                "type": "tc",
                "value": tc
            }
            try:
                float_values = parse_quantity(tc)
                is_anomaly = False
                for float_value in float_values:
                    if float_value > 270:
                        anomaly['description'] = "Tc too high"
                        anomalies.append(anomaly)
                        is_anomaly = True
                    elif float_value < 0:
                        anomaly['description'] = "Tc negative"
                        anomalies.append(anomaly)
                        is_anomaly = True
                if is_anomaly:
                    continue

            except Exception as e:
                anomaly['description'] = "Tc not parseable, " + str(e)
                anomalies.append(anomaly)
                continue

        else:
            anomaly = {"id": record['_id'], "type": "tc", "value": tc, 'description': "Tc null or empty"}
            anomalies.append(anomaly)

        applied_pressure = record['appliedPressure']
        if applied_pressure:
            anomaly = {
                "id": record['_id'],
                "type": "applied_pressure",
                "value": applied_pressure
            }

            try:
                float_values = parse_quantity(applied_pressure, type="pressure")
                is_anomaly = False
                for float_value in float_values:
                    if float_value > 250 * 1000000000:
                        anomaly['description'] = "Pressure too high"
                        anomalies.append(anomaly)
                        is_anomaly = True
                    elif float_value < 0:
                        anomaly['description'] = "Pressure negative"
                        anomalies.append(anomaly)
                        is_anomaly = True
                if is_anomaly:
                    continue

            except Exception as e:
                anomaly['description'] = "Applied pressure not parseable, " + str(e)
                anomalies.append(anomaly)
                continue

        formula = record['formula'] if 'formula' in record else None
        variables = record['variables'] if 'variables' in record else None

        if formula and not variables:
            valid, exception = validate_formula_naive(formula)
            if not valid:
                anomalies.append(
                    {
                        "id": record['_id'],
                        "type": "formula",
                        "value": formula,
                        "description": exception
                    }
                )
            else:
                if formula not in materials.keys():
                    materials[formula] = {}

                if float_value > 0:
                    if float_value in materials[formula].keys():
                        materials[formula][float_value] += 1
                    else:
                        materials[formula][float_value] = 1

    duplicated_materials = {key: value for key, value in materials.items() if len(value) > 1}

    weighted_averages_dict = {}

    total_duplicated_tc = 0
    for key, inner_dict in duplicated_materials.items():
        weighted_sum = sum(key * value for key, value in inner_dict.items())
        total_weight = sum(inner_dict.values())
        total_duplicated_tc += total_weight
        weighted_average = weighted_sum / total_weight
        weighted_averages_dict[key] = weighted_average

    nb_outliers = 0
    for mat_key, inner_dict in duplicated_materials.items():
        for val_key, value in inner_dict.items():
            if not weighted_averages_dict[mat_key] * 0.5 < val_key < weighted_averages_dict[mat_key] * 1.5:
                print(mat_key, "Outlier!", val_key, "outside the range", weighted_averages_dict[mat_key] * 0.5, "-",
                      weighted_averages_dict[mat_key] * 1.5)
                nb_outliers += 1

    if dry_run:
        if verbose:
            for anomaly in anomalies:
                print(anomaly['type'], "-", anomaly['value'], "-", anomaly['description'])
    else:
        print("Writing on the database:", db_name, config['mongo']['server'])
        input_value = input("Continue [y/N]")
        pass
        # if input_value == "y":
        #     document_collection = db.get_collection("document")
        #     training_data_collection = db.get_collection("training_data")
        #     for anomaly in anomalies:
        #         if verbose:
        #             print(anomaly['type'], "-", anomaly['value'], "-", anomaly['description'])
        #
        #             old_doc = tabular_collection.find_one({'_id': anomaly['id'], "status": "new"})
        #             if old_doc:
        #                 new_status = 'invalid'
        #                 new_type = 'automatic'
        #                 error_type = "anomaly_detection"
        #
        #                 changes = {'status': new_status, 'type': new_type, 'error_type': error_type}
        #
        #                 tabular_collection.update_one({'_id': anomaly['id']}, {'$set': changes})
        #                 training_data_id = write_raw_training_data(old_doc, anomaly['id'], document_collection,
        #                                                            training_data_collection,
        #                                                            action="anomaly")
        #
        #             else:
        #                 print("Document", anomaly['id'], "not found, ignoring it.")


        # else:
        #     print("Aborting")

    print("Total number of records", tabular_cursor_count)
    print("Anomalies in Tc:", len(list(filter(lambda x: x['type'] == "tc", anomalies))))
    print("Anomalies in applied pressure:", len(list(filter(lambda x: x['type'] == "applied_pressure", anomalies))))
    print("Anomalies in Materials formula:", len(list(filter(lambda x: x['type'] == "formula", anomalies))))
    print("Anomalies in materials with multiple Tc: ", len(duplicated_materials),
          "with outliers", nb_outliers, "/", total_duplicated_tc)
