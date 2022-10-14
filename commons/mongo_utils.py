import pymongo
from pymongo import MongoClient


def connect_mongo(config):
    if config is None or config == {}:
        raise Exception("Config is blank!")

    if 'mongo' not in config or 'server' not in config['mongo']:
        raise Exception("Config is incomplete! Server information is missing!")

    mongo_client_url = config['mongo']['server']
    c = MongoClient(mongo_client_url)

    return c


def ensure_indexes(config):
    connection = connect_mongo(config=config)
    if 'db' not in config['mongo']:
        raise Exception("Config is incomplete. Db is missing!")

    db = connection[config['mongo']['db']]

    db.document.create_index([("hash", pymongo.ASCENDING), ("timestamp", pymongo.ASCENDING)])
    db.document.create_index("hash")
    db.document.create_index([("type", pymongo.ASCENDING), ("status", pymongo.ASCENDING)])
    db.document.create_index("timestamp")
    db.document.create_index("biblio.year")
    db.document.create_index("biblio.journal")
    db.document.create_index("biblio.publisher")

    db.tabular.create_index([("type", pymongo.ASCENDING), ("status", pymongo.ASCENDING)])
    db.tabular.create_index(
        [("hash", pymongo.ASCENDING), ("timestamp", pymongo.ASCENDING), ("type", pymongo.ASCENDING)])
    db.tabular.create_index([("hash", pymongo.ASCENDING), ("timestamp", pymongo.ASCENDING)])
    db.tabular.create_index("hash")
    db.tabular.create_index([("doi", pymongo.ASCENDING)])
    db.tabular.create_index([("title", pymongo.ASCENDING)])
    db.tabular.create_index([("author", pymongo.ASCENDING)])
    db.tabular.create_index([("year", pymongo.ASCENDING)])

    db.binary.chunks.create_index([("files_id", pymongo.ASCENDING), ("n", pymongo.ASCENDING)])

    db.binary.files.create_index([("filename", pymongo.ASCENDING), ("uploadDate", pymongo.ASCENDING)])
    db.binary.files.create_index("hash")

    db.training_data.create_index("hash")
    db.training_data.create_index([("hash", pymongo.ASCENDING), ("status", pymongo.ASCENDING)])