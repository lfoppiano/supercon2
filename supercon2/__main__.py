import argparse
import sys
from pathlib import Path

import waitress
from apiflask import APIFlask

from commons.mongo_utils import ensure_indexes
from supercon2 import service
from supercon2.service import bp
from supercon2.utils import load_config_yaml


def create_app(root_path):
    ensure_indexes(service.config)
    print("Ensuring indexes completed..")

    final_root_path = root_path
    if root_path == "/" and ('root-path' in service.config and service.config['root-path'] is not None):
        final_root_path = service.config['root-path']

    print("root_path:", root_path)

    app = APIFlask(__name__, static_url_path=final_root_path + '/static', spec_path=final_root_path + '/spec',
                   docs_path=final_root_path + '/docs', redoc_path=final_root_path + '/redoc')
    app.config['OPENAPI_VERSION'] = '3.0.2'
    app.config['SPEC_FORMAT'] = 'json'
    app.tags = ['supercon']

    app.register_blueprint(bp, url_prefix=final_root_path)

    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Run the SuperCon2 service.")
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
    parser.add_argument("--env", type=str, choices=["development", "production"], required=False,
                        default="production", help="Select whether to run the service in production")

    parser.add_argument("--db-name", type=str, required=False, help="Force the database name.")

    args = parser.parse_args()

    service.config = load_config_yaml(args.config_file)
    if args.db_name:
        service.config['mongo']['db'] = args.db_name
        print("Override manually the database name:", args.db_name)

    root_path = args.root_path

    app = create_app(root_path)

    env = args.env
    if env == "development":
        # force development env
        app.env = 'development'
        app.run(host=args.host, port=args.port, debug=args.debug)
    elif env == "production":
        waitress.serve(app, host=args.host, port=args.port)
    else:
        print("Wrong environment value. ")
        parser.print_help()
        sys.exit(-1)

