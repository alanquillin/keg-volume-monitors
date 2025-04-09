import os

from lib.config import Config
from lib import logging
from lib.util import snake_to_camel

from flask_restx import Resource

class BaseResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)

    def transform_response(self, data, transform_keys=None, remove_keys=None):
        if not data:
            return data

        if getattr(data, "to_dict", None):
            return self.transform_response(data.to_dict(), transform_keys=transform_keys, remove_keys=remove_keys)

        if isinstance(data, BaseResource):
            return self.transform_response(data.to_dict(), transform_keys=transform_keys, remove_keys=remove_keys)

        if isinstance(data, list):
            return [self.transform_response(d, transform_keys=transform_keys, remove_keys=remove_keys) for d in data]

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
                _key = "".join([key.title() if ix > 0 else key.lower() for ix, key in enumerate(key.split("_"))])
            else:
                _key = key

            if isinstance(val, dict):
                val = self.transform_response(val, transform_keys=transform_keys, remove_keys=remove_keys)

            transformed[snake_to_camel(_key)] = val

        return transformed