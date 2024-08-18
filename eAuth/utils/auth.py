import logging
import secrets
import time
from functools import wraps

from apiflask import abort
from authlib.jose import jwt, JWTClaims, JoseError
from flask import current_app, g

from ..auth.models import User
from ..constant import CACHE_PREFIX_LOGOUT, CACHE_TIME_LOGOUT_DELAY
from ..extensions import cache

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
        # 若已经注销了，则token无效
        logout_time = cache.get(f"{CACHE_PREFIX_LOGOUT}_{data.get('uid')}")
        if logout_time and logout_time >= data.get("iat"):
            raise JoseError("Invalid token")
        user: User = User.query.get(data.get("uid"))
        if user and user.is_locked:
            return None
    except JoseError:
        return None
    except:
        logger.info("[verify token] Verify token failed", exc_info=True)
        return None
    else:
        return user


def required_admin(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if g.user.username != "admin":  # admin直接通过
            abort(403)
        return func(*args, **kwargs)
    return decorator


def generate_random_password():
    return secrets.token_hex(32)


def logout_user(uid: int):
    """
    注销

    :param uid:
    :return:
    """
    cache.set(f"{CACHE_PREFIX_LOGOUT}_{uid}", int(time.time()),
              current_app.config.get("TOKEN_EXPIRED", 60 * 60) + CACHE_TIME_LOGOUT_DELAY)
