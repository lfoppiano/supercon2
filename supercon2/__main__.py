import argparse
import json
from pathlib import Path

from flask import Flask

from supercon2.service import bp


def load_config(config_file):
    global config
    try:
        with open(config_file, 'r') as fp:
            config = json.load(fp)

    except Exception as e:
        print("configuration could not be loaded: ", str(e))
        exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Run the supercon2 service.")
    parser.add_argument("--host", type=str, default='0.0.0.0',
                        help="Host of the service.")
    parser.add_argument("--port", type=str, default=8080,
                        help="Port of the service.")
    parser.add_argument("--root-path", type=str, default="/supercon", required=False,
                        help="Root path prefix for the URLs.")
    parser.add_argument("--config-file", type=Path, required=False, help="Configuration file to be used.",
                        default='./config.json')
    parser.add_argument("--debug", action="store_true", required=False, default=False,
                        help="Activate the debug mode for the service")

    args = parser.parse_args()

    load_config(args.config_file)

    root_path = args.root_path
    static_path = root_path + '/static'

    app = Flask(__name__, static_url_path=static_path)
    app.register_blueprint(bp, url_prefix=root_path)
    print(app.url_map)

    app.run(host=args.host, port=args.port, debug=args.debug)
