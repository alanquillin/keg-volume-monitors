import argparse
import os
import sys
import uuid
from datetime import timedelta

from lib import logging
from lib.config import Config

from resources.devices import api as DevicesNS
from resources.device_measurements import api as DeviceMeasurementsNS

CONFIG = Config()
CONFIG.setup(config_files=["default.json"])
logging.init(fmt=logging.DEFAULT_LOG_FMT)

from flask import Flask, send_from_directory, render_template
from flask.logging import create_logger
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from gevent.pywsgi import LoggingLogAdapter, WSGIServer  # pylint:disable=ungrouped-imports

class IgnoringLogAdapter(LoggingLogAdapter):
    """
    Do not let k8s spam the logs:
    """

    IGNORED_LOGS = ['"GET /health HTTP/1.1" 200']

    def write(self, msg):
        for i in self.IGNORED_LOGS:
            if i in msg:
                return
        super().write(msg)

STATIC_URL_PATH = "static"
API_PREFIX = "/api/v1"
app = Flask(__name__, static_folder='static', static_url_path='')

# NOTE!  the root path handler much be regeistered BEFORE the flask-restx API object is initialized
# to prevent it from being hijacked!  This method serves the UI content
@app.route('/')
def index():
    dir_path = os.path.join(os.getcwd(), STATIC_URL_PATH)
    return send_from_directory(dir_path, "index.html")

api = Api(app, version='0.1', title='Keg Volume Monitor',
    description='Keg Volume Monitor', license="GPLv3", doc=f"{API_PREFIX}/docs",
    default="system"
)
app.secret_key = CONFIG.get("app.secret_key", str(uuid.uuid4()))

app.config.update(
    {
        "app_config": CONFIG,
        "SESSION_COOKIE_SECURE": CONFIG.get("secure_cookies", True),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
    }
)

api.add_namespace(DevicesNS, path=f"{API_PREFIX}/devices")
api.add_namespace(DeviceMeasurementsNS, path=f"{API_PREFIX}/devices/<device_id>/measurements")

@api.route(f"{API_PREFIX}/ping")
class Ping(Resource):
    def get(self):
        return "pong"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # parse logging level arg:
    parser.add_argument(
        "-l",
        "--log",
        dest="loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("LOG_LEVEL", "INFO").upper(),
        help="Set the logging level",
    )
    args = parser.parse_args()
    log_level = getattr(logging, args.loglevel)

    logger = create_logger(app)

    if app.config.get("ENV") == "development":
        logger.debug("Setting up development environment")
        CORS(app)
    else:
        CORS(
            app,
            resources={
                "/user": {
                    "origins": CONFIG.get("api.registration_allow_origins"),
                    "methods": ["PUT", "OPTIONS"],
                }
            },
            expose_headers=["Content-Type"],
            max_age=3000,
            vary_header=True,
        )
    port = CONFIG.get("api.port")
    http_server = WSGIServer(("", port), app, log=IgnoringLogAdapter(app.logger, log_level))
    logger.debug("app.config: %s", app.config)
    logger.debug("config: %s", CONFIG.data_flat)
    logger.info("Serving on port %s", port)

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        logger.info("User interrupted - Goodbye")
        sys.exit()