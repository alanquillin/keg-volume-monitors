import json
import inspect

import requests
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask import redirect, request
from flask_login import UserMixin, login_user, logout_user, current_user
from flask_restx import Namespace, fields, reqparse

from oauthlib.oauth2 import WebApplicationClient

import asyncio
from db import session_scope
from db.users import Users as UsersDB
from resources import BaseResource, AsyncBaseResource

api = Namespace('auth', description='Auth APIs')
session_urls = Namespace('auth_session_urls', description='Auth Session Urls')

login_mod = api.model("Login", {

})
class AuthUser(UserMixin):
    def __init__(self, id_, first_name, last_name, email, profile_pic, google_oidc_id, api_key, admin=False, human=False, service_account=False, device=False):
        super().__init__()

        self.id = id_
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.profile_pic = profile_pic
        self.google_oidc_id = google_oidc_id
        self.api_key = api_key
        self.admin = admin
        self.human = human
        self.service_account = service_account
        self.device = device

    @staticmethod
    def from_user(user):
        if not user:
            return None

        return AuthUser(user.id, user.first_name, user.last_name, user.email, user.profile_pic, user.google_oidc_id, user.api_key, admin=user.admin, human=True)
    
    @staticmethod
    def from_device(device):
        if not device:
            return None

        return AuthUser(device.id, device.name, None, None, None, None, device.api_key, device=True)
    
    @staticmethod
    def from_service_account(svc_acc):
        if not svc_acc:
            return None

        return AuthUser(svc_acc.id, svc_acc.name, None, None, None, None, svc_acc.api_key, service_account=True)


class GoogleResourceMixin():
    def __init__(self):
        super().__init__()
        self.client_id = self.config.get("auth.oidc.google.client_id")
        self.client_secret = self.config.get("auth.oidc.google.client_secret")
        self.discovery_url = self.config.get("auth.oidc.google.discovery_url")

        self.client = WebApplicationClient(self.client_id)

    def get_provider_cfg(self):
        return requests.get(self.discovery_url).json()

@session_urls.route('', '/login/google"')
class GoogleLogin(BaseResource, GoogleResourceMixin):
    async def get(self):
        if not self.config.get("auth.oidc.google.enabled"):
            api.abort(403, "Google authentication is disabled")

        # Find out what URL to hit for Google login
        google_provider_cfg = self.get_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login and provide
        # scopes that let you retrieve user's profile from Google
        request_uri = self.client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request.base_url + "/callback",
            scope=["openid", "email", "profile"],
        )
        self.logger.debug("redirecting to google SSO: %s", request_uri)
        return redirect(request_uri)

@session_urls.route('"/login/google/callback"')
class GoogleCallback(BaseResource, GoogleResourceMixin):
    async def get(self):
        # Get authorization code Google sent back to you
        code = request.args.get("code")

        # Find out what URL to hit to get tokens that allow you to ask for
        # things on behalf of a user
        google_provider_cfg = self.get_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare and send a request to get tokens! Yay tokens!
        token_url, headers, body = self.client.prepare_token_request(
            token_endpoint, authorization_response=request.url, redirect_url=request.base_url, code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(self.client_id, self.client_secret),
        )

        # Parse the tokens!
        self.client.parse_request_body_response(json.dumps(token_response.json()))

        # Now that you have tokens (yay) let's find and hit the URL
        # from Google that gives you the user's profile information,
        # including their Google profile image and email
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = self.client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # You want to make sure their email is verified.
        # The user authenticated with Google, authorized your
        # app, and now you've verified their email through Google!
        userinfo = userinfo_response.json()
        self.logger.debug("user info: %s", userinfo)
        if userinfo.get("email_verified"):
            unique_id = userinfo.get("sub")
            users_email = userinfo.get("email")
            picture = userinfo.get("picture")
            first_name = userinfo.get("given_name")
            last_name = userinfo.get("family_name")
        else:
            api.abort(400, "User email not available or not verified by Google.")

        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_email(db_session, users_email)

            if not user:
                api.abort(401, "No user found for the given Google account.  User email must match the Google account email.")

            update_data = {}

            if not user.first_name and first_name:
                self.logger.debug("User '%s' first name not set in database.  Updating from google: %s", users_email, first_name)
                update_data["first_name"] = first_name

            if not user.last_name and last_name:
                self.logger.debug("User '%s' last name not set in database.  Updating from google: %s", users_email, last_name)
                update_data["last_name"] = last_name

            if not user.google_oidc_id and unique_id:
                self.logger.debug("User '%s' google OIDC Id not set in database.  Updating from google: %s", users_email, unique_id)
                update_data["google_oidc_id"] = unique_id

            if not user.profile_pic and picture:
                self.logger.debug("User '%s' profile pic url not set in database.  Updating from google: %s", users_email, picture)
                update_data["profile_pic"] = picture

            if update_data:
                self.logger.debug("Updating user account '%s' with missing data: %s", users_email, update_data)
                UsersDB.update(db_session, user.id, **update_data)

            # Begin user session by logging the user in
            login_user(AuthUser.from_user(user))

        # Send user back to homepage
        return redirect("/home")

@session_urls.route("/logout")
class Logout(AsyncBaseResource):
    async def get(self):
        if inspect.iscoroutine(current_user):
            cu = await current_user
        else:
            cu = current_user
        
        await asyncio.sleep(1)
        if not cu:
            return redirect("/login")

        if not cu.is_authenticated:
            return redirect("/login")
        
        self.logger.debug("Logging out user")
        logout_user()
        self.logger.debug("User logged out successfully!")
        
        return redirect("/login")
    
@session_urls.route("/me")
class Me(AsyncBaseResource):
    async def get(self):
        if inspect.iscoroutine(current_user):
            cu = await current_user
        else:
            cu = current_user

        if not cu:
            return None

        if not cu.is_authenticated:
            return None
        
        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, cu.id)
            remove_keys = ["password_hash"]
            if not user.admin:
                remove_keys.append("admin")
            return self.transform_response(user, remove_keys=remove_keys)


@api.route("/login")
@api.expect(login_mod, validate=True)
class Login(AsyncBaseResource):
    async def post(self):
        data = api.payload

        email = data.get("email")
        password = data.get("password")

        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_email(db_session, email)

            if not user:
                api.abort(401)

            password_hash = user.password_hash
            self.logger.debug(f"user found, checking password gainst hasH {password_hash}")
            if not password_hash:
                api.abort(400, "The user does not have a password set.  Please try logging in with google.")

            self.logger.debug(f"checking user {email} with password {password}")
            ph = PasswordHasher()
            try:
                if not ph.verify(password_hash, password):
                    api.abort(401)
            except VerifyMismatchError:
                api.abort(401)

            login_user(AuthUser.from_user(user))

        return True
