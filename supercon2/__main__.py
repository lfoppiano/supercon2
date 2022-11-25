import argparse
import sys
import urllib.parse
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

    print("root_path:", root_path)

    app = APIFlask(__name__, static_url_path=root_path + '/static', spec_path=root_path + '/spec',
                   docs_path=root_path + '/docs', redoc_path=root_path + '/redoc')
    app.config['OPENAPI_VERSION'] = '3.0.2'
    app.config['SPEC_FORMAT'] = 'json'
    app.tags = ['supercon']

    app.register_blueprint(bp, url_prefix=root_path)

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

    if args.root_path != '/':
        service.config['root-path'] = args.root_path
        print("Override manually the root path: ", args.root_path)

    if not service.config['root-path'].endswith("/"):
        service.config['root-path'] += "/"

    app = create_app(service.config['root-path'])

    env = args.env
    if env == "development" or args.debug:
        # force development env
        print("Running in development mode. For serious installation, use --env production")
        app.env = 'development'
        app.run(host=args.host, port=args.port, debug=args.debug)
    elif env == "production":
        print("Running in production mode. Faster and less verbose. "
              "Use either --env development or --debug for development.")
        waitress.serve(app, host=args.host, port=args.port)
    else:
        print("Wrong environment value. ")
        parser.print_help()
        sys.exit(-1)
