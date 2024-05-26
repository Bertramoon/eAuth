import logging

from apiflask import APIBlueprint, abort
from flask import current_app, g

from .schemas import LoginInputSchema, LoginOutputSchema, AuthInputSchema, AuthOutputSchema
from .models import User
from ..extensions import limiter

auth_api = APIBlueprint("auth", __name__, url_prefix="/api/auth")
logger = logging.getLogger(__name__)


@auth_api.post("/login")
@auth_api.input(LoginInputSchema, location="json", arg_name="data")
@auth_api.output(LoginOutputSchema, status_code=200)
@auth_api.doc(summary="登录接口，返回token信息", responses=[200, 401, 422])
@limiter.limit('2000/day;800/hour;100/minute;5/second')
def login(data):
    username, password = data["username"], data["password"]
    user = User.query.filter_by(username=username).first()

    if user and (user.is_locked or user.login_incorrect >= current_app.config.get("MAX_LOGIN_INCORRECT", 3)):
        logger.info(f"[login] User's locked: {user.is_locked} and login incorrect: {user.login_incorrect}")
        abort(401, message="Login is limited, please contact your administrator")

    if not (user and user.validate_password(password)):
        if not user:
            logger.info("[login] Get none user.")
        else:
            logger.warning(f"[auth] The password of the user `{user.username}` was failed.")
        abort(401, message="Username or password failed")

    logger.info(f"[login] User `{user.username}` login success")

    return {
        "token": user.auth_token
    }


@auth_api.post("/check")
@auth_api.input(AuthInputSchema, location="json", arg_name="data")
@auth_api.output(AuthOutputSchema)
@auth_api.doc(summary="鉴权接口，传入请求URL及请求方法，返回响应码200表示鉴权通过",
              responses=[200, 401, 403, 422],
              security="Authorization")
@limiter.limit('10000/day;2000/hour;500/minute;10/second')
def auth(data):
    url, method = data["url"], data["method"]
    user: User = g.user
    success: bool = True
    if not user.can(url, method):
        success = False
        abort(403, message="No permission")
    logger.info(f"[check] User: `{user.username}`, url: `{url}`, method: `{method}`, check result is {success}")
    return {}


@auth_api.get("/ping")
def ping():
    return {"success": "ok"}
