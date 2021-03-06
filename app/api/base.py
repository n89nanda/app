from functools import wraps

import arrow
from flask import Blueprint, request, jsonify, g
from flask_login import current_user

from app.extensions import db
from app.log import LOG
from app.models import ApiKey

api_bp = Blueprint(name="api", import_name=__name__, url_prefix="/api")


def require_api_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_authenticated:
            g.user = current_user
        else:
            api_code = request.headers.get("Authentication")
            api_key = ApiKey.get_by(code=api_code)

            if not api_key:
                return jsonify(error="Wrong api key"), 401

            # Update api key stats
            api_key.last_used = arrow.now()
            api_key.times += 1
            db.session.commit()

            g.user = api_key.user

        return f(*args, **kwargs)

    return decorated


@api_bp.app_errorhandler(404)
def not_found(e):
    return jsonify(error="No such endpoint"), 404


@api_bp.app_errorhandler(Exception)
def internal_error(e):
    LOG.exception(e)
    return jsonify(error="Internal error"), 500


@api_bp.app_errorhandler(405)
def wrong_method(e):
    return jsonify(error="Method not allowed"), 405
