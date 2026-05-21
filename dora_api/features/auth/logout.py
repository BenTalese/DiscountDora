import logging

from flask import session

from dora_api.features.routers import AUTH_ROUTER
from dora_api.infrastructure.api_response import no_content


@AUTH_ROUTER.route("/logout", methods=["POST"])
def logout():
    _Logger = logging.getLogger(__name__)
    _UserId = session.get("user_id")
    session.clear()
    if _UserId:
        _Logger.info(f"Logout for user {_UserId}")
    return no_content()
