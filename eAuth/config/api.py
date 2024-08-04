import logging

from flask import g
from flask.views import MethodView
from apiflask import APIBlueprint, abort

from .schemas import ApiSchema, RoleSchema, ApiPageOutputSchema, RolePageOutputSchema, UserPageOutputSchema, \
    ApiIdListSchema, RoleSingleOutputSchema, ApiSingleOutputSchema, ApiQuerySchema, RoleQuerySchema
from ..auth.models import Api, Role, User
from ..auth.schemas import RegisterInputSchema, ResetPasswordInputSchema, ChangePasswordInputSchema
from ..base.schemas import BaseOutSchema, PageSchema
from ..extensions import db
from ..utils.auth import required_admin, generate_random_password
from ..utils.decorator import operate_log
from ..utils.message import message_util
from ..utils.model import get_page

config_api = APIBlueprint("config", __name__, url_prefix="/api/config")
logger = logging.getLogger(__name__)


class ApiView(MethodView):
    @config_api.input(ApiQuerySchema, location="query", arg_name="query")
    @config_api.output(ApiPageOutputSchema)
    @config_api.doc(summary="获取API",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def get(self, api_id: int, query: dict):
        model = Api.query
        if query.get("url"):
            model = model.filter(Api.url.like(f"%{query.get('url')}%"))
        return get_page(model, {"id": api_id}, query["page"], query["per_page"])

    @operate_log
    @config_api.input(ApiSchema, location="json", arg_name="data")
    @config_api.output(ApiSingleOutputSchema, status_code=201)
    @config_api.doc(summary="创建API",
                    responses=[201, 401, 403, 422, 500],
                    security="Authorization")
    def post(self, data: dict):
        api = Api(**data)
        try:
            db.session.add(api)
            db.session.commit()
        except:
            logger.error("[api] Create failed", exc_info=True)
            db.session.rollback()
            abort(500, message="server error")
        return {"data": api}

    @operate_log
    @config_api.input(ApiSchema, location="json", arg_name="data")
    @config_api.output(ApiSingleOutputSchema, status_code=201)
    @config_api.doc(summary="修改API",
                    responses=[201, 401, 403, 404, 422, 500],
                    security="Authorization")
    def put(self, api_id: int, data: dict):
        api = Api.query.get_or_404(api_id)
        for field, value in data.items():
            setattr(api, field, value)
        try:
            db.session.commit()
        except:
            logger.error("[api] Update failed", exc_info=True)
            db.session.rollback()
            abort(500, message="server error")
        return {"data": api}

    @operate_log
    @config_api.output(BaseOutSchema)
    @config_api.doc(summary="删除API",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def delete(self, api_id: int):
        api = Api.query.get_or_404(api_id)
        try:
            db.session.delete(api)
            db.session.commit()
        except:
            logger.error("[api] Delete failed", exc_info=True)
            db.session.rollback()
            abort(500, message="server error")
        return {"success": True}


class RoleView(MethodView):
    @config_api.input(RoleQuerySchema, location="query", arg_name="query")
    @config_api.output(RolePageOutputSchema)
    @config_api.doc(summary="获取角色",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def get(self, role_id: int, query: dict):
        model = Role.query
        if query.get("name"):
            model = model.filter(Role.name.like(f"%{query.get('name')}%"))
        return get_page(model, {"id": role_id}, query["page"], query["per_page"])

    @operate_log
    @config_api.input(RoleSchema, location="json", arg_name="data")
    @config_api.output(RoleSingleOutputSchema, status_code=201)
    @config_api.doc(summary="创建角色",
                    responses=[201, 401, 403, 422, 500],
                    security="Authorization")
    def post(self, data: dict):
        role = Role(**data)
        try:
            db.session.add(role)
            db.session.commit()
        except:
            logger.error("[role] Create failed", exc_info=True)
            db.session.rollback()
            abort(500, message="server error")
        return {"data": role}

    @operate_log
    @config_api.input(RoleSchema, location="json", arg_name="data")
    @config_api.output(RoleSingleOutputSchema, status_code=201)
    @config_api.doc(summary="修改角色",
                    responses=[201, 401, 403, 404, 422, 500],
                    security="Authorization")
    def put(self, role_id: int, data: dict):
        role = Role.query.get_or_404(role_id)
        for field, value in data.items():
            setattr(role, field, value)
        try:
            db.session.commit()
        except:
            logger.error("[role] Update failed", exc_info=True)
            db.session.rollback()
            abort(500, message="server error")
        return {"data": role}

    @operate_log
    @config_api.output(BaseOutSchema)
    @config_api.doc(summary="删除角色",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def delete(self, role_id: int):
        role = Role.query.get_or_404(role_id)
        try:
            db.session.delete(role)
            db.session.commit()
        except:
            logger.error("[role] Delete failed", exc_info=True)
            db.session.rollback()
            abort(500, message="server error")
        return {"success": True}


class UserView(MethodView):
    @config_api.input(PageSchema, location="query", arg_name="query")
    @config_api.output(UserPageOutputSchema)
    @config_api.doc(summary="获取用户",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def get(self, username: str, query: dict):
        return get_page(User.query, {"username": username}, query["page"], query["per_page"])


api_view = ApiView.as_view("api_view")
config_api.add_url_rule("/api", view_func=api_view, defaults={"api_id": None}, methods=["GET"])
config_api.add_url_rule("/api", view_func=api_view, methods=["POST"])
config_api.add_url_rule("/api/<int:api_id>", view_func=api_view, methods=["GET", "PUT", "DELETE"])

role_view = RoleView.as_view("role_view")
config_api.add_url_rule("/role", view_func=role_view, defaults={"role_id": None}, methods=["GET"])
config_api.add_url_rule("/role", view_func=role_view, methods=["POST"])
config_api.add_url_rule("/role/<int:role_id>", view_func=role_view, methods=["GET", "PUT", "DELETE"])

user_view = UserView.as_view("user_view")
config_api.add_url_rule("/user", view_func=user_view, defaults={"username": None}, methods=["GET"])
config_api.add_url_rule("/user/<username>", view_func=user_view, methods=["GET"])


@config_api.get("/role/unbind/<int:role_id>")
@config_api.input(ApiQuerySchema, location="query", arg_name="query")
@config_api.output(ApiPageOutputSchema)
@config_api.doc(summary="查询角色未绑定的API列表",
                responses=[200, 401, 403, 404, 500],
                security="Authorization")
def get_role_unbind_api(role_id: int, query: dict):
    role: Role = Role.query.get_or_404(role_id)
    model = Api.query.filter(~Api.id.in_(item.id for item in role.apis))
    if query.get("url"):
        model = model.filter(Api.url.like(f"%{query.get('url')}%"))
    result = get_page(model, {}, query["page"], query["per_page"], role_id=role_id)
    return result


@config_api.put("/role/<int:role_id>/api")
@operate_log
@config_api.input(ApiIdListSchema, location="json", arg_name="data")
@config_api.output(RoleSingleOutputSchema, status_code=201)
@config_api.doc(summary="为角色绑定api",
                responses=[201, 401, 403, 404, 500],
                security="Authorization")
def role_add_api(role_id: int, data: dict):
    # 查询角色
    role: Role = Role.query.get_or_404(role_id)
    # 筛选出需要添加的API id列表
    ids = data["ids"]
    current_ids = set(api.id for api in role.apis)
    add_ids = list()
    for id_ in ids:
        if id_ not in current_ids:
            add_ids.append(id_)
    logger.info(f"[role-api] Role `{role.name}` will add api {add_ids}")
    try:
        # 为角色添加API
        api_add_list = Api.query.filter(Api.id.in_(add_ids)).all()
        role.apis.extend(api_add_list)
        db.session.commit()
    except:
        logger.error("[role-api] Update failed", exc_info=True)
        db.session.rollback()
        abort(500, message="server error")
    return {
        "data": role
    }


@config_api.delete("/role/<int:role_id>/api")
@operate_log
@config_api.input(ApiIdListSchema, location="json", arg_name="data")
@config_api.output(RoleSingleOutputSchema, status_code=201)
@config_api.doc(summary="为角色解绑api",
                responses=[201, 401, 403, 404, 500],
                security="Authorization")
def role_remove_api(role_id: int, data: dict):
    # 查询角色
    role: Role = Role.query.get_or_404(role_id)
    # 筛选出需要删除的API id列表
    ids = set(data["ids"])
    current_apis = role.apis.copy()
    for api in role.apis:
        if api.id in ids:
            current_apis.remove(api)
    logger.info(f"[role-api] Role `{role.name}` will set apis={[api.id for api in current_apis]}")
    try:
        role.apis = current_apis
        db.session.commit()
    except:
        logger.error("[role-api] Delete failed", exc_info=True)
        db.session.rollback()
        abort(500, message="server error")
    return {
        "data": role
    }


@config_api.post('/user/register')
@operate_log
@config_api.input(RegisterInputSchema, location='json', arg_name='data')
@config_api.output(BaseOutSchema)
@config_api.doc(summary="注册账号",
                responses=[200, 401, 403, 422],
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
    # 推送消息
    message_util.send(None, user.email, '账号注册', 'emails/register', username=user.username, password=password)


@config_api.post('/user/reset')
@operate_log
@config_api.input(ResetPasswordInputSchema, location='json', arg_name='data')
@config_api.output(BaseOutSchema)
@config_api.doc(summary="重置密码",
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
    except:
        db.session.rollback()
        logger.error(f"[user] Reset user `{user.username}`({user.email}) fail.", exc_info=True)
    # 推送消息
    message_util.send(None, user.email, '账号密码重置', 'emails/reset', username=user.username, password=password)


@config_api.post('/user/change-password')
@operate_log
@config_api.input(ChangePasswordInputSchema, location='json', arg_name='data')
@config_api.output(BaseOutSchema)
@config_api.doc(summary="修改密码",
                responses=[200, 401, 403, 422],
                security="Authorization")
def change_password(data):
    new_password: str = data['new_password']
    user: User = g.get('user')
    try:
        user.set_password(new_password)
        db.session.commit()
    except:
        db.session.rollback()
        logger.error(f"[user] User `{user.username}`({user.email}) change password failed.", exc_info=True)
