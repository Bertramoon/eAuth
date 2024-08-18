import datetime
import logging

from apiflask import APIBlueprint, abort
from flask import current_app, g

from .models import User
from .schemas import LoginInputSchema, LoginOutputSchema, AuthInputSchema, AuthOutputSchema
from ..base.schemas import BaseOutSchema
from ..extensions import limiter, db
from ..log.models import SecurityLog
from ..utils.auth import logout_user
from ..utils.decorator import security_log

auth_api = APIBlueprint("auth", __name__, url_prefix="/api/auth")
logger = logging.getLogger(__name__)


@auth_api.post("/login")
@security_log("login")
@auth_api.input(LoginInputSchema, location="json", arg_name="data")
@auth_api.output(LoginOutputSchema, status_code=200)
@auth_api.doc(summary="登录接口，返回token信息", responses=[200, 401, 422])
@limiter.limit('2000/day;800/hour;100/minute;5/second')
def login(data):
    username, password = data["username"], data["password"]
    user = User.query.filter_by(username=username).first()

    if not user:
        logger.info("[login] Get none user.")
        abort(401, message="Username or password failed")
    if user.is_locked:
        logger.info(f"[login] User <{user.username}> is locked")
        abort(401, message="Username or password failed")

    # 设置短期最大登录失败次数和长期最大登录失败次数，达到长期最大登录失败次数后，不能再进行登录，只能通过找回密码的方式重置密码
    is_max_login_incorrect = user.login_incorrect >= current_app.config.get("MAX_LOGIN_INCORRECT", 9)
    if is_max_login_incorrect:
        logger.info(
            f"[login] Over than the MAX_LOGIN_INCORRECT(user <{user.username}>, times <{user.login_incorrect}>)")
        abort(401, message="Username or password failed")

    last_login_log: SecurityLog = \
        SecurityLog.query.filter_by(username=user.username, success=False).order_by(
            SecurityLog.operate_datetime.desc()).first()
    is_short_max_login_incorrect = (
            user.login_incorrect >= current_app.config.get("SHORT_MAX_LOGIN_INCORRECT", 3)
            and last_login_log is not None
            and datetime.datetime.utcnow() - last_login_log.operate_datetime <
            datetime.timedelta(hours=current_app.config.get("SHORT_MAX_LOGIN_DELAY", 3)))
    if is_short_max_login_incorrect:
        logger.info(
            f"[login] Over than the SHORT_MAX_LOGIN_DELAY(user <{user.username}>, times <{user.login_incorrect}>)")
        abort(401, message="Username or password failed")

    if not user.validate_password(password):
        try:
            user.login_incorrect += 1
            db.session.commit()
        except:
            db.session.rollback()
            logger.error(f"[login] Set the login_incorrect failed for user {user.username}", exc_info=True)
        logger.warning(f"[auth] The password of the user `{user.username}` was failed.")
        abort(401, message="Username or password failed")

    logger.info(f"[login] User <{user.username}> login success")

    try:
        user.login_incorrect = 0
        db.session.commit()
    except:
        db.session.rollback()
        logger.warning(f"[login] Set the login_incorrect to zero failed for user {user.username}", exc_info=True)

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


@auth_api.post("/logout")
@auth_api.output(BaseOutSchema)
@auth_api.doc(summary="用于推出登录",
              responses=[200, 401, 403, 422],
              security="Authorization")
def logout():
    # 调用到该方法说明认证通过了，因此只需要将该用户uid以及当前时间加入缓存中即可
    user: User = g.get("user")
    logout_user(user.id)


@auth_api.get("/ping")
@auth_api.output(BaseOutSchema)
def ping():
    return {"success": True}
