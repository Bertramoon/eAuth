import logging

from apiflask import abort, HTTPError, APIBlueprint
from flask import g
from flask.views import MethodView
from sqlalchemy import or_

from eAuth.base.schemas import BaseOutSchema
from eAuth.extensions import db
from eAuth.models import User, Role
from eAuth.utils.auth import required_admin, generate_random_password, logout_user
from eAuth.utils.decorator import operate_log, security_log
from eAuth.utils.message import message_util
from eAuth.utils.model import get_page
from .schema import UserQuerySchema, UserPageOutputSchema, UserInputSchema, UserSingleOutputSchema, \
    RegisterInputSchema, ResetPasswordInputSchema, ChangePasswordInputSchema
from ..role.schema import RoleIdListInputSchema, RoleLightOutputSchema

config_user = APIBlueprint("config_user", __name__, url_prefix="/user")

logger = logging.getLogger(__name__)


class UserView(MethodView):
    @config_user.input(UserQuerySchema, location="query", arg_name="query")
    @config_user.output(UserPageOutputSchema)
    @config_user.doc(summary="获取用户",
                     responses=[200, 401, 403, 404, 500],
                     security="Authorization")
    def get(self, uid: int, query: dict):
        model = User.query
        if query.get("username"):
            model = model.filter(or_(
                User.username.like(f"%{query.get('username')}%"),
                User.email.like(f"%{query.get('username')}%")
            ))
        return get_page(model, {"id": uid}, query["page"], query["per_page"])

    @operate_log
    @config_user.input(UserInputSchema, location="json", arg_name="data")
    @config_user.output(UserSingleOutputSchema, status_code=201)
    @config_user.doc(summary="修改用户基本信息",
                     responses=[201, 401, 403, 404, 500],
                     security="Authorization")
    def put(self, uid, data):
        user: User = User.query.get_or_404(uid)
        if not data:
            return user
        email = data.get("email")
        locked = data.get("locked")
        try:
            if email:
                user.email = email
            if locked is not None:
                if user.username == "admin" and locked is True:
                    abort(422, message="Admin can't be locked")
                user.locked = locked
            db.session.commit()
        except HTTPError:
            raise
        except:
            logger.error("[update user] Update failed", exc_info=True)
            db.session.rollback()
            abort(500, message="server error")

        return {
            "data": user
        }


user_view = UserView.as_view("user_view")
config_user.add_url_rule("", view_func=user_view, defaults={"uid": None}, methods=["GET"])
config_user.add_url_rule("/<int:uid>", view_func=user_view, methods=["GET", "PUT"])


@config_user.post("/<int:uid>/role")
@operate_log
@config_user.input(RoleIdListInputSchema, location="json", arg_name="data")
@config_user.output(UserSingleOutputSchema, status_code=201)
@config_user.doc(summary="为用户授权角色",
                 responses=[201, 401, 403, 404, 500],
                 security="Authorization")
def user_set_role(uid: int, data: dict):
    # 查询用户
    user: User = User.query.get_or_404(uid)
    # 筛选出需要添加的角色id列表
    ids = set(data["ids"])
    try:
        role_list = Role.query.filter(Role.id.in_(ids)).all()
        user.roles = role_list
        db.session.commit()
    except:
        logger.error("[user-role] Set roles failed", exc_info=True)
        db.session.rollback()
        abort(500, message="server error")
    return {
        "data": user
    }


@config_user.get('/roles')
@config_user.output(RoleLightOutputSchema)
@config_user.doc(summary="查询所有角色的id和角色名（不分页）",
                 responses=[200, 401, 403, 500],
                 security="Authorization")
def get_roles_light():
    """
    获取轻量级的角色信息，仅包括角色id和名称
    """
    result = [
        {"id": item[0], "name": item[1]}
        for item in
        db.session.query(Role.id, Role.name).order_by(Role.id.asc()).all()
    ]
    return {
        "data": result
    }


@config_user.post('/register')
@operate_log
@config_user.input(RegisterInputSchema, location='json', arg_name='data')
@config_user.output(UserSingleOutputSchema, status_code=201)
@config_user.doc(summary="注册账号",
                 responses=[201, 401, 403, 422],
                 security="Authorization")
@required_admin
def register(data):
    # 注册
    user = User(
        username=data['username'],
        email=data['email']
    )
    password = generate_random_password()
    user.set_password(password)
    try:
        db.session.add(user)
        db.session.commit()
    except:
        db.session.rollback()
        logger.error(f"[user] Create user `{user.username}`({user.email}) fail.", exc_info=True)
        abort(500, message="server error")
    # 推送消息
    message_util.send(None, user.email, '账号注册', 'emails/register', username=user.username, password=password)
    return {"data": user}


@config_user.post('/reset')
@operate_log
@config_user.input(ResetPasswordInputSchema, location='json', arg_name='data')
@config_user.output(UserSingleOutputSchema)
@config_user.doc(summary="重置密码",
                 responses=[200, 401, 403, 422],
                 security="Authorization")
@required_admin
def reset(data):
    email: str = data['email']
    user: User = User.query.filter_by(email=email).first()
    if not user:
        abort(404)

    password = generate_random_password()
    user.set_password(password)
    try:
        db.session.commit()
        logout_user(user.id)
    except:
        db.session.rollback()
        logger.error(f"[user] Reset user `{user.username}`({user.email}) fail.", exc_info=True)
        abort(500, message="server error")
    # 推送消息
    message_util.send(None, user.email, '账号密码重置', 'emails/reset', username=user.username, password=password)
    return {"data": user}


@config_user.post('/change-password')
@security_log("change password")
@config_user.input(ChangePasswordInputSchema, location='json', arg_name='data')
@config_user.output(BaseOutSchema)
@config_user.doc(summary="修改密码",
                 responses=[200, 401, 403, 422],
                 security="Authorization")
def change_password(data):
    new_password: str = data['new_password']
    user: User = g.get('user')
    try:
        user.set_password(new_password)
        db.session.commit()
        logout_user(user.id)
    except:
        db.session.rollback()
        logger.error(f"[user] User `{user.username}`({user.email}) change password failed.", exc_info=True)
        abort(500, message="server error")
