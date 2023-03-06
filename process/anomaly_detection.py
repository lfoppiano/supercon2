import argparse
import os
import re
import sys
from pathlib import Path
import pymatgen.core as mg

from process.grobid_client_generic import GrobidClientGeneric
from supercon_batch_mongo_extraction import connect_mongo

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
    tabular_cursor = tabular_collection.find({"status": {"$in": ["new", "curated", "validated"]}})
    anomaly_tc_count = 0
    anomaly_formula_count = 0
    for record in tabular_cursor:
        tc = record['criticalTemperature']
        if tc:
            search = temp_regex.search(tc)
            if search:
                value = search.groups()[0]
                unit = search.groups()[1]
                if float(value) > 270:
                    print("anomaly T", tc)
                    anomaly_tc_count += 1

            else:
                pass
                # print("not match", tc)

        formula = record['formula']
        variables = record['variables'] if 'variables' in record else None
        if formula and not variables:
            try:
                mg.Composition(formula, strict=False)
            except ValueError as ve:
                anomaly_formula_count += 1
                print("anomaly F", formula, ve)

    print("Anomalies in Tc:", anomaly_tc_count)
    print("Anomalies in Materials:", anomaly_formula_count)
