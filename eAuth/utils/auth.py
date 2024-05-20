import logging
import time
from functools import wraps

from apiflask import abort
from authlib.jose import jwt, JWTClaims, JoseError
from flask import current_app, request, g

from ..auth.models import User


logger = logging.getLogger(__name__)


def verify_token(token: str):
    """
    校验token，成功返回user，失败返回None

    :param token:
    :return:
    """
    try:
        data: JWTClaims = jwt.decode(token.encode("ascii"), current_app.config["SECRET_KEY"])
        if data.get("exp") < time.time():
            raise JoseError("Token expired")
        user: User = User.query.get(data.get("uid"))
        if user and (user.is_locked or user.login_incorrect >= current_app.config.get("MAX_LOGIN_INCORRECT", 3)):
            return None
    except JoseError:
        return None
    except Exception:
        logger.info("[verify token] Verify token failed", exc_info=True)
        return None
    else:
        return user


def verify_permission(func):
    """
    鉴权装饰器

    :param func:
    :return:
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(g, "user") or not g.user:
            logger.info("[verify permission] Verify permission failed: user is none")
            abort(403, message="No permission")
        user = g.user
        url = request.path
        method = request.method
        if not user.can(url, method):
            logger.info("[verify permission] Verify permission failed: no permission")
            abort(403, message="No permission")
        return func(*args, **kwargs)
    return wrapper
