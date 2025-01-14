import bson
import flask
import werkzeug
import superdesk

from datetime import timedelta
from typing import Dict, Optional
from flask import current_app as app
from flask_babel import _
from newsroom.user_roles import UserRole
from superdesk.utc import utcnow
from newsroom.auth import get_user, get_company
from newsroom.types import UserData
from newsroom.utils import get_random_string, is_valid_user
from newsroom.email import (
    send_validate_account_email,
    send_reset_password_email,
    send_new_account_email,
)


# how often we should check in db if session
# user is still valid
SESSION_AUTH_TTL = timedelta(minutes=15)


def sign_user_by_email(
    email: str,
    redirect_on_success: str = "wire.index",
    redirect_on_error: str = "auth.login",
    create_missing: bool = False,
    userdata: Optional[UserData] = None,
) -> werkzeug.Response:
    users = superdesk.get_resource_service("users")
    user: UserData = users.find_one(req=None, email=email)

    if user is None and create_missing and userdata is not None:
        user = userdata.copy()
        user["is_enabled"] = True
        users.create([user])

    if user is None:
        flask.flash(_("User not found"), "danger")
        return flask.redirect(flask.url_for(redirect_on_error, user_error=1))

    assert "_id" in user

    users.system_update(
        user["_id"],
        {
            "is_validated": True,  # in case user was not validated before set it now
            "last_active": utcnow(),
        },
        user,
    )

    start_user_session(user)

    return flask.redirect(flask.url_for(redirect_on_success))


def start_user_session(user: UserData, permanent=False):
    flask.session["user"] = str(user["_id"])  # str to avoid serialization issues
    flask.session["name"] = "{} {}".format(user.get("first_name"), user.get("last_name"))
    flask.session["user_type"] = user["user_type"]
    flask.session["auth_ttl"] = utcnow().replace(tzinfo=None) + SESSION_AUTH_TTL
    flask.session.permanent = permanent


def clear_user_session():
    flask.session["user"] = None
    flask.session["name"] = None
    flask.session["user_type"] = None
    flask.session["auth_ttl"] = None


def is_current_user_admin() -> bool:
    return flask.session.get("user_type") == UserRole.ADMINISTRATOR.value


def is_current_user_account_mgr() -> bool:
    return flask.session.get("user_type") == UserRole.ACCOUNT_MANAGEMENT.value


def is_current_user_company_admin() -> bool:
    return flask.session.get("user_type") == UserRole.COMPANY_ADMIN.value


def is_current_user(user_id):
    """
    Checks if the current session user is the same as given user id
    """
    return flask.session["user"] == str(user_id)


def send_token(user, token_type="validate"):
    if user is not None and user.get("is_enabled", False):
        if token_type == "validate" and user.get("is_validated", False):
            return False

        updates = {}
        add_token_data(updates)
        superdesk.get_resource_service("users").patch(id=bson.ObjectId(user["_id"]), updates=updates)
        if token_type == "validate":
            send_validate_account_email(user["first_name"], user["email"], updates["token"])
        if token_type == "new_account":
            send_new_account_email(user["first_name"], user["email"], updates["token"])
        elif token_type == "reset_password":
            send_reset_password_email(user["first_name"], user["email"], updates["token"])
        return True
    return False


def add_token_data(user):
    user["token"] = get_random_string()
    user["token_expiry_date"] = utcnow() + timedelta(days=app.config["VALIDATE_ACCOUNT_TOKEN_TIME_TO_LIVE"])


def is_valid_session():
    now = utcnow().replace(tzinfo=None)
    return (
        flask.session.get("user")
        and flask.session.get("user_type")
        and (flask.session.get("auth_ttl") and flask.session.get("auth_ttl") > now or revalidate_session_user())
    )


def revalidate_session_user():
    user = superdesk.get_resource_service("users").find_one(req=None, _id=flask.session.get("user"))
    if not user:
        clear_user_session()
        return False
    company = get_company(user)
    is_valid = is_valid_user(user, company)
    if is_valid:
        flask.session["auth_ttl"] = utcnow().replace(tzinfo=None) + SESSION_AUTH_TTL
    return is_valid


def get_user_sections() -> Dict[str, bool]:
    user = get_user()
    if not user:
        return {}
    if user.get("sections"):
        return user["sections"]
    company = get_company(user)
    if company and company.get("sections"):
        return company["sections"]
    return {}


def user_has_section_allowed(section) -> bool:
    sections = get_user_sections()
    if sections:
        return sections.get(section, False)
    return True  # might be False eventually, atm allow access if sections are not set explicitly


def user_can_manage_company(company_id) -> bool:
    if is_current_user_admin() or is_current_user_account_mgr():
        return True
    if is_current_user_company_admin():
        user = get_user()
        if user:
            return str(user.get("company")) == str(company_id) and company_id
    return False
