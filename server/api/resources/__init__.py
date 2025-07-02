from functools import wraps
from datetime import datetime
import uuid
import inspect

from lib.config import Config
from lib import logging
from lib.util import snake_to_camel

from flask import current_app, request
from flask_login import current_user
from flask_login.config import EXEMPT_METHODS
from flask_restx import Resource
from flask_restx.errors import abort

DEVICE_STATE_MAP = {
    1: "ready",
    2: "ready_no_service",
    10: "calibration_mode_enabled",
    11: "calibrating",
    99: "maintenance_mode_enabled"
}

STATIC_URL_PATH = "static"
API_PREFIX = "/api/v1"

SWAGGER_AUTHORIZATIONS = {
    "apiKey": {
        "type": "apiKey",
        "in": "query",
        "name": "api_key"
    }
}

class BaseResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @staticmethod
    def transform_response(data, transform_keys=None, remove_keys=None):
        if not data:
            return data

        if getattr(data, "to_dict", None):
            return BaseResource.transform_response(data.to_dict(), transform_keys=transform_keys, remove_keys=remove_keys)

        if isinstance(data, list):
            return [BaseResource.transform_response(d, transform_keys=transform_keys, remove_keys=remove_keys) for d in data]

        transformed = {}

        if not transform_keys:
            transform_keys = {}

        if not remove_keys:
            remove_keys = []

        for key, val in data.items():
            if key in remove_keys:
                continue

            if val is None:
                continue

            if key in transform_keys:
                _key = transform_keys[key]
            elif "_" in key:
                _key = snake_to_camel(key)
            else:
                _key = key

            if isinstance(val, dict):
                val = BaseResource.transform_response(val, transform_keys=transform_keys, remove_keys=remove_keys)

            if isinstance(val, uuid.UUID):
                val = str(val)

            if isinstance(val, datetime):
                val = val.isoformat()

            transformed[_key] = val

        return transformed
    
class AsyncBaseResource(BaseResource):
    async def dispatch_request(self, *args, **kwargs):
        """
        Dispatch the request to the appropriate method.
        """
        # Get the method name from the request
        method_name = request.method.lower()
        # Get the method from the class
        method = getattr(self, method_name)
        # Call the method and await its result

        if inspect.iscoroutinefunction(method):
            return await method(*args, **kwargs)
        else:
            return method(*args, **kwargs)

def async_login_required(allow_device=True, allow_service_account=True, require_admin=False, allow_callback=False):
    def dec(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            is_authenticated = False
            if inspect.iscoroutine(current_user):
                cu = await current_user
            else:
                cu = current_user

            if cu:
                is_authenticated = cu.is_authenticated
            
            if not is_authenticated:
                if allow_callback:
                    return await current_app.login_manager.unauthorized()
                else:
                    abort(401)

            if require_admin and (not cu.admin and not cu.admin):
                abort(401, "you are not authorized to execute admin actions")

            if cu.device and not allow_device:
                abort(401, "devices are not allowed")   

            if cu.service_account and not allow_service_account:
                abort(401, "service accounts are not allowed")           

            return await func(*args, current_user=cu, **kwargs)
        return wrapper
    return dec