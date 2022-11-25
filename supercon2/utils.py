import json

import yaml


def load_config_json(config_file):
    config = []
    try:
        with open(config_file, 'r') as fp:
            config = json.load(fp)
    except Exception as e:
        print("Configuration could not be loaded: ", str(e))
        exit(1)
    return config


def load_config_yaml(config_file):
    config = []
    try:
        with open(config_file, 'r') as the_file:
            raw_configuration = the_file.read()

        config = yaml.safe_load(raw_configuration)
    except Exception as e:
        print("Configuration could not be loaded: ", str(e))
        exit(1)

    return config
