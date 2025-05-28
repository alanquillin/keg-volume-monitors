from datetime import datetime
import uuid

from lib.config import Config
from lib import logging
from lib.util import snake_to_camel

from flask import request
from flask_restx import Resource

DEVICE_STATE_MAP = {
    1: "ready",
    2: "ready_no_service",
    10: "calibration_mode_enabled",
    11: "calibrating",
    99: "maintenance_mode_enabled"
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
        return await method(*args, **kwargs)