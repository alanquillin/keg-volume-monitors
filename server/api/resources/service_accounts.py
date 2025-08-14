import inspect

from flask_login import current_user as _current_user
from flask_restx import Namespace, reqparse, fields

import asyncio
from db import session_scope
from db.service_accounts import ServiceAccounts as ServiceAccountsDB
from lib.util import random_string, obj_keys_camel_to_snake
from resources import AsyncBaseResource, async_login_required

api = Namespace('service_accounts', description='Service Accounts APIs')

IN_FIELDS = {
    "name": fields.String(required=True, description=""),
    "apiKey": fields.String(description="", readonly=True)
}

new_sa_mod = api.model("NewServiceAccount", IN_FIELDS)
sa_mod = api.model("ServiceAccount", {
        "id": fields.String(description="The id of the service account", readonly=True)
    } | IN_FIELDS)


class ServiceAccountResource(AsyncBaseResource):
    async def transform_response(self, service_account, transform_keys=None, remove_keys=None, current_user=None):
        data = service_account.to_dict()

        if not current_user:
            current_user = _current_user

        if not current_user.admin and current_user.id == service_account.id:
            remove_keys.append("api_key")

        res = AsyncBaseResource.transform_response(data, transform_keys=transform_keys, remove_keys=remove_keys)
        return res
        

@api.route("", "/")
class ServiceAccounts(ServiceAccountResource):
    @api.doc('get_service_accounts', security=["apiKey"])
    @api.response(200, 'Success', sa_mod)
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def get(self, *args, current_user=None, **kwargs):
        with session_scope(self.config) as db_session:
            service_accounts = ServiceAccountsDB.query(db_session)

            return [await self.transform_response(u, current_user=current_user) for u in service_accounts]

    @api.doc('create_service_account', security=["apiKey"])
    @api.expect(new_sa_mod, validate=True)
    @api.response(201, 'Success', sa_mod)
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def post(self, *args, current_user=None, **kwargs):
        data = data = api.payload

        with session_scope(self.config) as db_session:
            u_data = obj_keys_camel_to_snake(data)
            self.logger.debug("Creating service account with data: %s", u_data)
            service_account = ServiceAccountsDB.create(db_session, **u_data)
            return await self.transform_response(service_account, current_user=current_user)


@api.route('/<service_account_id>')
class ServiceAccount(ServiceAccountResource):
    @api.doc('patch_service_account', security=["apiKey"])
    @api.response(200, 'Success', sa_mod)
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def get(self, service_account_id, *args, current_user=None, **kwargs):
        with session_scope(self.config) as db_session:
            service_account = ServiceAccountsDB.get_by_pkey(db_session, service_account_id)

            if not service_account:
                api.abort(404)

            return await self.transform_response(service_account, current_user=current_user)
        
    @api.doc('patch_service_account', security=["apiKey"])
    @api.response(200, 'Success', sa_mod)
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def patch(self, service_account_id, *args, current_user=None, **kwargs):
        data = api.payload

        with session_scope(self.config) as db_session:
            service_account = ServiceAccountsDB.get_by_pkey(db_session, service_account_id)

            if not service_account:
                api.abort(404)

            u_data = obj_keys_camel_to_snake(data)
            self.logger.debug("Updating service account '%s' (%s) with data: %s", service_account.name, service_account_id, u_data)
            service_account = ServiceAccountsDB.update(db_session, service_account_id, **u_data)
            return await self.transform_response(service_account, current_user=current_user)

    @api.doc('delete_service_account', security=["apiKey"])
    @api.expect(new_sa_mod, validate=False)
    @api.response(200, 'Success', sa_mod)
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def delete(self, service_account_id, *args, current_user=None, **kwargs):
        with session_scope(self.config) as db_session:
            service_account = ServiceAccountsDB.get_by_pkey(db_session, service_account_id)

            if not service_account:
                api.abort(404)

            self.logger.debug("Deleting service account '%s' (%s)", service_account.name, service_account_id)
            ServiceAccountsDB.delete(db_session, service_account_id)
            return True
        
@api.route('/<service_account_id>/api_key')
class ServiceAccountsAPIKey(ServiceAccountResource):
    @api.doc('generate_service_account_api_key', security=["apiKey"])
    @api.response(200, 'Success')
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def post(self, service_account_id, *args, current_user=None, **kwargs):
        with session_scope(self.config) as db_session:
            service_account = ServiceAccountsDB.get_by_pkey(db_session, service_account_id)

            if not service_account:
                api.abort(404)

            parser = reqparse.RequestParser()
            parser.add_argument('regen', location='args')
            args = parser.parse_args()
            self.logger.debug(f"args: {args}")
            allow_regen = args.get("regen")

            if service_account.api_key and (not allow_regen or allow_regen.lower() not in ["", "1", "true", "yes"]):
                api.abort(400, "API key already exists")

            self.logger.debug("Generating API key for service account '%s' (%s)", service_account.name, service_account_id)
            api_key = random_string(self.config.get("general.default_api_key_length"))
            ServiceAccountsDB.update(db_session, service_account_id, api_key=api_key)
            return api_key
