import argparse
import json
import os
from pathlib import Path

import yaml
from flask import Flask

from supercon2 import service
from supercon2.service import bp
from supercon2.utils import load_config_yaml

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Run the supercon2 service.")
    parser.add_argument("--host", type=str, default='0.0.0.0',
                        help="Host of the service.")
    parser.add_argument("--port", type=str, default=8080,
                        help="Port of the service.")
    parser.add_argument("--root-path", type=str, default="/", required=False,
                        help="Root path prefix for the URLs.")
    parser.add_argument("--config-file", type=Path, required=False, help="Configuration file to be used.",
                        default='config.yaml')
    parser.add_argument("--debug", action="store_true", required=False, default=False,
                        help="Activate the debug mode for the service")

    args = parser.parse_args()

    service.config = load_config_yaml(args.config_file)

    root_path = args.root_path

    if root_path == "/" and ('root-path' in service.config and service.config['root-path'] is None):
        root_path = service.config['root-path']

    static_path = root_path + '/static'
    app = Flask(__name__, static_url_path=static_path)
    app.register_blueprint(bp, url_prefix=root_path)

    app.run(host=args.host, port=args.port, debug=args.debug)
