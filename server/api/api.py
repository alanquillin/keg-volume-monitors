import argparse
import os
import sys
import uuid
import base64
from binascii import Error as binasciiError

from lib import logging
from lib.config import Config

CONFIG = Config()
CONFIG.setup(config_files=["default.json"])
logging.init(fmt=logging.DEFAULT_LOG_FMT)

LOGGER = logging.getLogger(__name__)

from db import session_scope
from db.devices import Devices as DevicesDB
from db.users import Users as UsersDB
from db.service_accounts import ServiceAccount as ServiceAccountsDB
from resources import API_PREFIX
from resources.auth import AuthUser, api as AuthNS, session_urls as AuthSessionUrlsNS
from resources.devices import api as DevicesNS
from resources.device_measurements import api as DeviceMeasurementsNS
from resources.device_status import api as DeviceStatusNS
from resources.ui import api as UINS

from flask import Flask, redirect
from flask.logging import create_logger
from flask_cors import CORS
from flask_login import LoginManager
from flask_restx import Api, Resource
from flask_restx.errors import abort
from aiohttp import web
from aiohttp_wsgi import WSGIHandler, serve


app = Flask(__name__, static_folder='static', static_url_path='')

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
async def load_user(user_id):
    with session_scope(CONFIG) as db_session:
        print("refreshing user %s" % user_id)

        return AuthUser.from_user(UsersDB.get_by_pkey(db_session, user_id))
    
@login_manager.unauthorized_handler
async def redirect_not_logged_in():
    return redirect("/login")

@login_manager.request_loader
async def load_user_from_request(request):

    # first, try to login using the api_key url arg
    bearer_token = request.args.get('api_key')

    if not bearer_token:
        LOGGER.debug("No api_key found in query string, checking for bearer token in Authorization header.")
        auth_token = request.headers.get('Authorization')
        if auth_token:
            LOGGER.debug(f"Authorization header found: {auth_token}")
            bearer_token = auth_token.replace('Bearer ', '', 1).strip()
            

    if bearer_token:
        LOGGER.debug(f"Bearer token found, attempting to decode and authorize.  Bearer token: {bearer_token}")
        try:
            bearer_token = base64.b64decode(bearer_token).decode('ascii')
            LOGGER.debug(f"Bearer token decoded successfully.  Decoded bearer token: {bearer_token}")
        except TypeError as e:
            abort(401, "Invalid Bearer token format")
        except binasciiError as e:
            abort(401, "Invalid Bearer token format")
        parts = bearer_token.split('|')
        if len(parts) != 2:
            abort(401, "Invalid Bearer token format")
        
        type = parts[0].lower()
        key = parts[1]
        LOGGER.info(f"Bearer token type: {type}")
        LOGGER.info(f"API Key: {key}")
        if type == "user":
            with session_scope(CONFIG) as db_session:
                user = UsersDB.get_by_api_key(db_session, key)
                if user:
                    return AuthUser.from_user(user) 
        elif type == "svc":
            with session_scope(CONFIG) as db_session:
                svc_acc = ServiceAccountsDB.get_by_api_key(db_session, key)
                if svc_acc:
                    return AuthUser.from_service_account(svc_acc)
        elif type == "device":
            with session_scope(CONFIG) as db_session:
                dev = DevicesDB.get_by_api_key(db_session, key)
                if dev:
                    return AuthUser.from_device(dev)
        else:
            abort(401, "Invalid Bearer token format")

    # finally, return None if both methods did not login the user
    return None

# NOTE!  the root path handler much be regeistered BEFORE the flask-restx API object is initialized
# to prevent it from being hijacked!  This method serves the UI content

@app.route("/health")
async def health():
    return {"healthy": True}

@app.route('/')
async def home():
    return redirect("/home")

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

api.add_namespace(UINS, path="/")
api.add_namespace(AuthSessionUrlsNS, path=f"/auth")
api.add_namespace(AuthNS, path=f"{API_PREFIX}/auth")
api.add_namespace(DevicesNS, path=f"{API_PREFIX}/devices")
api.add_namespace(DeviceMeasurementsNS, path=f"{API_PREFIX}/devices/<device_id>/measurements")
api.add_namespace(DeviceStatusNS, path=f"{API_PREFIX}/devices/<id>/status")

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
    
    with session_scope(CONFIG) as db_session:
        init_admin_username = CONFIG.get("auth.initial_admin.username")
        init_admin = UsersDB.get_by_email(db_session, init_admin_username)
        if not init_admin:
            init_admin_pass = CONFIG.get("auth.initial_admin.password")
            api_key = CONFIG.get("auth.initial_admin.api_key")
            logger.info(f"Creating initial admin user {init_admin_username}")
            UsersDB.create(db_session, password=init_admin_pass, email=init_admin_username, api_key=api_key, admin=True)

    port = CONFIG.get("api.port")
    logger.debug("app.config: %s", app.config)
    logger.debug("config: %s", CONFIG.data_flat)
    logger.info("Serving on port %s", port)

    try:
        # app.run(host="0.0.0.0", port=port, debug=False)
        wsgi_handler = WSGIHandler(app)
        serve(app, port=port)
    except KeyboardInterrupt:
        logger.info("User interrupted - Goodbye")
        sys.exit()