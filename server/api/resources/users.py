import inspect

from flask_login import current_user
from flask_restx import Namespace, reqparse

import asyncio
from db import session_scope
from db.users import Users as UsersDB
from lib.util import random_string
from resources import AsyncBaseResource, async_login_required

api = Namespace('users', description='Users APIs')

@api.route("/me")
class Me(AsyncBaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('get_current_user', security=["apiKey"])
    @api.response(200, 'Success')
    async def get(self):    
        if inspect.iscoroutine(current_user):
            cu = await current_user
        else:
            cu = current_user

        if not cu:
            api.abort(401)

        if not cu.is_authenticated:
            api.abort(401)

        if not cu.human:
            api.abort(401)
            
        with session_scope(self.config) as db_session:      
            user = UsersDB.get_by_pkey(db_session, cu.id)
            remove_keys = ["password_hash"]
            if not user.admin:
                remove_keys.append("admin")
            return self.transform_response(user, remove_keys=remove_keys)
        
class UserResource(AsyncBaseResource):
    async def transform_response(self, user, transform_keys=None, remove_keys=None):
        data = user.to_dict()
        FILTERED_KEYS = ["password_hash", "google_oidc_id"]

        user_c = current_user
        if not user_c.admin and user_c.id == user.id:
            FILTERED_KEYS.append("api_key")

        data["password_enabled"] = False
        if data.get("password_hash"):
            data["password_enabled"] = True

        for key in FILTERED_KEYS:
            if key in data:
                del data[key]

        res = AsyncBaseResource.transform_response(user, transform_keys=transform_keys, remove_keys=remove_keys)
        return res

@api.route("/")
class Users(UserResource):
    @api.doc('get_users', security=["apiKey"])
    @api.response(200, 'Success')
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def get(self):
        with session_scope(self.config) as db_session:
            users = UsersDB.query(db_session)

            return [self.transform_response(u) for u in users]

    @api.doc('create_user', security=["apiKey"])
    @api.response(200, 'Success')
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def post(self):
        data = self.get_request_data(remove_key=["id"])

        with session_scope(self.config) as db_session:
            self.logger.debug("Creating user with data: %s", data)
            user = UsersDB.create(db_session, **data)
            return self.transform_response(user)


@api.route('/<id>')
class User(UserResource):
    @api.doc('patch_user', security=["apiKey"])
    @api.response(200, 'Success')
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def patch(self, user_id):
        user_c = current_user
        data = self.get_request_data(remove_key=["id", "apiKey", "locations"])

        if "password" in data and user_c.id != user_id:
            api.abort(400, "You are not authorized to change the password for another user.")

        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_id)

            if not user:
                api.abort(404)

            if "password" in data and data["password"] is None:
                del data["password"]
                self.logger.debug("Disabling password for user '%s' (%s): %s", user.email, user_id)
                UsersDB.disable_password(db_session, user_id)

            self.logger.debug("Updating user '%s' (%s) with data: %s", user.email, user_id, data)
            user = UsersDB.update(db_session, user_id, **data)
            return self.transform_response(user)

    @api.doc('delete_user', security=["apiKey"])
    @api.response(200, 'Success')
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def delete(self, user_id):
        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_id)

            if not user:
                api.abort(404)

            if user_id == current_user.id:
                api.abort(400, "You cannot delete your own user")

            self.logger.debug("Deleting user '%s' (%s)", user.email, user_id)
            UsersDB.delete(db_session, user_id)
            return True
        

@api.route('/<id>/api_key')
class UserAPIKey(UserResource):
    @api.doc('get_user_api_key', security=["apiKey"])
    @api.response(200, 'Success')
    @async_login_required(allow_device=False, allow_service_account=False)
    async def get(self, user_id):
        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_id)

            if not user:
                api.abort(404)

            if user_id != current_user.id and not current_user.admin:
                api.abort(400, "You cannot access the API key for another users")

            return user.api_key
    
    @api.doc('generate_user_api_key', security=["apiKey"])
    @api.response(200, 'Success')
    @async_login_required(allow_device=False, allow_service_account=False)
    async def post(self, user_id):
        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_id)

            if not user:
                api.abort(404)

            if user_id != current_user.id and not current_user.admin:
                api.abort(400, "You cannot generate and API key for another users")

            parser = reqparse.RequestParser()
            parser.add_argument('regen', location='args')
            args = parser.parse_args()
            self.logger.debug(f"args: {args}")
            allow_regen = args.get("regen")

            if user.api_key and (not allow_regen or allow_regen.lower() not in ["", "1", "true", "yes"]):
                api.abort(400, "API key already exists")

            self.logger.debug("Generating API key for user '%s' (%s)", user.email, user_id)
            api_key = random_string(self.config.get("general.default_api_key_length"))
            UsersDB.update(db_session, user_id, api_key=api_key)
            return api_key

    @api.doc('delete_user_api_key', security=["apiKey"])
    @api.response(200, 'Success')
    @async_login_required(allow_device=False, allow_service_account=False)
    async def delete(self, user_id):
        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_id)

            if not user:
                api.abort(404)

            if user_id != current_user.id and not current_user.admin:
                api.abort(400, "You cannot delete another users API Key")

            self.logger.debug("Deleting user '%s' (%s)s api key", user.email, user_id)
            UsersDB.update(db_session, user_id, api_key=None)
            return True