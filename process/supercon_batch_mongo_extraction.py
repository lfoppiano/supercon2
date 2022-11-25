import argparse
import json
import math
import multiprocessing
import os
import sys
from datetime import datetime
from hashlib import blake2b
from pathlib import Path

import gridfs
from pymongo.errors import DocumentTooLarge
from tqdm import tqdm

from commons.mongo_utils import connect_mongo, ensure_indexes
from process.grobid_client_generic import GrobidClientGeneric

multiprocessing.set_start_method("fork")


def get_file_hash(fname):
    hash_md5 = blake2b()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class MongoSuperconProcessor:
    grobid_client = None
    config = {}

    m = multiprocessing.Manager()
    queue_input = None
    queue_output = None
    queue_logger = None

    def __init__(self, config_path, verbose=False):
        self.verbose = verbose
        self.grobid_client = GrobidClientGeneric()
        self.config = self.grobid_client.load_yaml_config_from_file(config_path)
        self.grobid_client.set_config(self.config, ping=True)

        if verbose:
            print("Configuration: ", self.config)

        if verbose:
            print("Init completed.")

    def write_mongo_status(self, db_name, service):
        """Write the status of the document being processed"""
        connection = connect_mongo(config=self.config)
        db = connection[db_name]
        while True:
            status_info = self.queue_logger.get(block=True)
            if status_info is None:
                print("Got termination. Shutdown 'logger' processor.")
                self.queue_logger.put(None)
                break

            status_info['service'] = service
            try:
                db.logger.insert_one(status_info)
            except DocumentTooLarge as e:
                print("Error while logging: ", status_info, ". Exception:", e)
            except UnicodeEncodeError as ue:
                print("Error while logging: ", status_info, ". Exception:", ue)
        pass

    def write_mongo_single(self, db_name):
        """Write the result of the document being processed"""

        connection = connect_mongo(config=self.config)
        db = connection[db_name]
        fs_binary = gridfs.GridFS(db, collection='binary')
        while True:
            output = self.queue_output.get(block=True)
            if output is None:
                if self.verbose:
                    print("Got termination. Shutdown 'writer' processor.")
                self.queue_output.put(None)
                break

            output_json = output[0]
            output_original_path = output[1]
            hash = output_json['hash']
            timestamp = output_json['timestamp']

            if self.verbose:
                print("Storing annotations in mongodb, hash: ", hash)

            try:
                document_id = db.document.insert_one(output_json).inserted_id
            except DocumentTooLarge as e:
                status_info = {
                    'status': None,
                    'path': str(output_original_path),
                    'message': str(e),
                    'timestamp': datetime.utcnow(),
                    'hash': hash
                }
                self.queue_logger.put(status_info, block=True)
                if self.verbose:
                    print(e)
                continue
            except UnicodeEncodeError as ue:

                try:
                    if self.verbose:
                        print("Invalid unicode detected. Trying to remove surrogates. ")

                    if 'passages' in output_json:
                        for passage in output_json['passages']:
                            passage['text'] = passage['text'].encode('utf-16', 'backslashreplace').decode('utf-16')
                            if 'spans' in passage:
                                for span in passage['spans']:
                                    span['text'] = span['text'].encode('utf-16', 'backslashreplace').decode('utf-16')
                                    if 'formattedText' in span:
                                        span['formattedText'] = span['formattedText'].encode('utf-16', 'backslashreplace').decode('utf-16')
                                    if 'attributes' in span:
                                        for attribute_key in span['attributes'].keys():
                                            span['attributes'][attribute_key] = span['attributes'][attribute_key].encode('utf-16', 'backslashreplace').decode('utf-16')

                            if 'tokens' in passage:
                                for token in passage['tokens']:
                                    token['text'] = token['text'].encode('utf-16', 'backslashreplace').decode('utf-16')

                    document_id = db.document.insert_one(output_json).inserted_id
                except UnicodeEncodeError as ue2:
                    status_info = {
                        'status': None,
                        'path': str(output_original_path),
                        'message': str(ue),
                        'timestamp': datetime.utcnow(),
                        'hash': hash
                    }
                    self.queue_logger.put(status_info, block=True)
                    if self.verbose:
                        print(ue2)
                    continue

            if self.verbose:
                print("Storing binary ", hash)
            file = fs_binary.find_one({"hash": hash})
            if not file:
                with open(output_original_path, 'rb') as f:
                    fs_binary.put(f, hash=hash, timestamp=timestamp)
            else:
                if self.verbose:
                    print("Binary already there, skipping")

            if self.verbose:
                print("Inserted document ", document_id)

    def process_batch_single(self):
        while True:
            source_path = self.queue_input.get(block=True)
            if source_path is None:
                if self.verbose:
                    print("Got termination. Shutdown 'process' processor.")
                self.queue_input.put(source_path)
                break

            hash_full = get_file_hash(source_path)
            hash = hash_full[:10]
            if self.process_only_new:
                connection = connect_mongo(config=self.config)
                db = connection[self.db_name]
                document = db.document.find_one({"hash": hash})
                if document:
                    continue

            if self.verbose:
                print("Processing file " + str(source_path))

            r, status = self.grobid_client.process_pdf(str(source_path), "processPDF",
                                                       headers={"Accept": "application/json"}, verbose=self.verbose)

            if r is not None:
                if status == 200:
                    status_info = {'path': str(source_path), 'status': status, 'timestamp': datetime.utcnow(),
                                   'hash': hash}
                    extracted_json = self.prepare_data(r, source_path)
                    extracted_json['type'] = 'automatic'
                    self.queue_output.put((extracted_json, source_path), block=True)
                else:
                    status_info = {'path': str(source_path), 'status': status, 'timestamp': datetime.utcnow(),
                                   'hash': hash, 'message': r}
            else:
                status_info = {'path': str(source_path), 'status': status, 'timestamp': datetime.utcnow(),
                               'hash': hash}

            self.queue_logger.put(status_info, block=True)

    def prepare_data(self, extracted_data, abs_path):
        extracted_json = json.loads(extracted_data)
        hash_full = get_file_hash(abs_path)
        hash = hash_full[:10]
        extracted_json['hash'] = hash
        timestamp = datetime.utcnow()
        extracted_json['timestamp'] = timestamp

        return extracted_json

    def setup_batch_processes(self, db_name=None, num_threads=os.cpu_count() - 1, only_new=False):
        if db_name is None:
            self.db_name = self.config["mongo"]["db"]
        else:
            self.db_name = db_name

        if self.verbose:
            print("Database:", self.db_name)

        if verbose:
            print("Ensuring indexes...")
        ensure_indexes(self.config)

        num_threads_process = num_threads
        num_threads_store = num_threads if num_threads > 1 else 1

        self.queue_input = self.m.Queue(maxsize=num_threads_process)
        self.queue_output = self.m.Queue(maxsize=num_threads_store)
        self.queue_logger = self.m.Queue(maxsize=num_threads_store)

        print("Processing files using ", num_threads_process, "/", num_threads_store,
              "for process/store on mongodb.")

        self.process_only_new = only_new

        self.pool_write = multiprocessing.Pool(num_threads_store, self.write_mongo_single, (self.db_name,))
        self.pool_logger = multiprocessing.Pool(num_threads_store, self.write_mongo_status,
                                                (self.db_name, 'extraction',))
        self.pool_process = multiprocessing.Pool(num_threads_process, self.process_batch_single, ( ))

        return self.queue_input, self.pool_process, self.queue_logger, self.pool_logger, self.queue_output, self.pool_write

    def tear_down_batch_processes(self):
        self.queue_input.put(None)
        self.pool_process.close()
        self.pool_process.join()

        self.queue_output.put(None)
        self.pool_write.close()
        self.pool_write.join()

        self.queue_logger.put(None)
        self.pool_logger.close()
        self.pool_logger.join()

    def get_queue_input(self):
        return self.queue_input


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Extract superconductor materials and properties and save them on MongoDB - extraction")
    parser.add_argument("--input", help="Input directory", type=Path, required=True)
    parser.add_argument("--config", help="Configuration file", type=Path, required=True)
    parser.add_argument("--num-threads", "-n", help="Number of concurrent processes", type=int, default=3,
                        required=False)
    parser.add_argument("--only-new", help="Processes only documents that have not record in the database",
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

    input_path = args.input
    num_threads = args.num_threads
    config_path = args.config
    db_name = args.database
    only_new = args.only_new
    verbose = args.verbose

    if not os.path.exists(config_path):
        print("The config file does not exists. ")
        parser.print_help()
        sys.exit(-1)

    if not os.path.isdir(input_path):
        print("The input should be a directory")
        parser.print_help()
        sys.exit(-1)

    processor_ = MongoSuperconProcessor(config_path, verbose)
    processor_.setup_batch_processes(num_threads=num_threads, db_name=db_name, only_new=only_new)
    start_queue = processor_.get_queue_input()

    if verbose:
        print("Counting documents.")

    count = 0
    for root, dirs, files in os.walk(input_path, followlinks=False):
        for file_ in files:
            if not file_.lower().endswith(".pdf"):
                continue
            count += 1

    if verbose:
        print("Counting documents finished.", count, "documents to process.")

    with tqdm(total=count, unit='document') as tq:
        for root, dirs, files in os.walk(input_path, followlinks=False):
            for file_ in files:
                if not file_.lower().endswith(".pdf"):
                    continue
                abs_path = os.path.join(root, file_)
                start_queue.put(abs_path, block=True)
                tq.update()

    print("Starting tearing down processes. ")
    processor_.tear_down_batch_processes()
    print("Finishing! ")
