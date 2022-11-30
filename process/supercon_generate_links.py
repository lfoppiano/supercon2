import argparse
import os
import sys
from math import floor
from pathlib import Path

# multiprocessing.set_start_method("fork")

from process.grobid_client_generic import GrobidClientGeneric
from process.supercon_batch_mongo_extraction import connect_mongo

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Automatic generation of document links for Supercon 2 curation.")
    parser.add_argument("--config", help="Configuration file", type=Path, required=True)
    parser.add_argument("--database", "-db",
                        help="Set the database name which is normally read from the configuration file", type=str,
                        required=False)
    parser.add_argument("--only-new", "-n",
                        help="Only documents from new records. Ignores records that have been already curated. ",
                        action="store_true", default=False)
    parser.add_argument("--verbose",
                        help="Print all log information", action="store_true", required=False, default=False)
    parser.add_argument("--prefix", help="URL prefix for the links", type=str, required=True)
    parser.add_argument("--people", help="Number of people to which split the links assignement", type=int,
                        required=False, default=1)

    args = parser.parse_args()
    config_path = args.config
    db_name = args.database
    only_new = args.only_new
    verbose = args.verbose
    prefix = args.prefix
    people = args.people

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

    query = {}
    if only_new:
        query = {"status": 'new'}

    projection = {"hash": 1, "_id": 0}

    cursor = tabular_collection.find(query, projection)

    links_all = list(set([prefix + cursor_item['hash'] for cursor_item in cursor]))

    assignment = []
    if people > 1:
        links_assigned_per_person = floor(len(links_all) / people)

        person_id = 0
        previous_link_id = 0
        for p in range(people):
            person_links = []
            for n in range(previous_link_id, previous_link_id + links_assigned_per_person):
                person_links.append(links_all[n])

            assignment.append(person_links)
            previous_link_id += links_assigned_per_person

        if previous_link_id < len(links_all):
            person_links = []

            for n in range(previous_link_id, len(links_all)):
                person_links.append(links_all[n])

            assignment.append(person_links)

    else:
        assignment = [links_all]

    for n, groups in enumerate(assignment):
        if n < people:
            print("##### Person", n, "#####")
        else:
            print("##### Leftovers #####")

        for link in groups:
            print(link)
