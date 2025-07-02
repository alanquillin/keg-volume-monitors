import os
from resources import AsyncBaseResource, DEVICE_STATE_MAP, async_login_required, STATIC_URL_PATH, SWAGGER_AUTHORIZATIONS

import asyncio
from flask import send_from_directory
from flask_restx import Namespace

api = Namespace('ui', description='UI resources', authorizations=SWAGGER_AUTHORIZATIONS)


@api.route("/home")
@api.route("/measurements")
@api.route("/me")
@api.route("/users")
@api.route("/settings")
class UI(AsyncBaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('protected_ui', security=["apiKey"])
    @async_login_required(allow_device=False, allow_service_account=False, allow_callback=True)
    async def get(self, *args, current_user=None, **kwargs):
        dir_path = os.path.join(os.getcwd(), STATIC_URL_PATH)
        return send_from_directory(dir_path, "index.html")
    
@api.route("/login")
class UnprotectedUI(AsyncBaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('open_ui')
    async def get(self):
        dir_path = os.path.join(os.getcwd(), STATIC_URL_PATH)
        return send_from_directory(dir_path, "index.html")