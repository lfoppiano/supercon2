from pymongo import MongoClient


def connect_mongo(config):
    if config is None or config == {}:
        raise Exception("Config is blank!")
    mongo_client_url = config['mongo']['server'] if 'mongo' in config and 'server' in config['mongo'] else ''
    c = MongoClient(mongo_client_url)

    return c