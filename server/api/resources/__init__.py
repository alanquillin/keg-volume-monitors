import os

from lib.config import Config
from lib import logging

from flask_restx import Resource

class BaseResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)