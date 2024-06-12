import logging

from flask.views import MethodView
from apiflask import APIBlueprint, abort, pagination_builder

from .schemas import ApiSchema, RoleSchema, ApiPageOutputSchema, RolePageOutputSchema, UserPageOutputSchema, \
    ApiIdListSchema, RoleSingleOutputSchema, ApiSingleOutputSchema
from ..auth.models import Api, Role, User
from ..base.schemas import BaseOutSchema, PageSchema
from ..extensions import db
from ..utils.decorator import operate_log
from ..utils.model import get_page

config_api = APIBlueprint("config", __name__, url_prefix="/api/config")
logger = logging.getLogger(__name__)


class ApiView(MethodView):
    @config_api.input(PageSchema, location="query", arg_name="query")
    @config_api.output(ApiPageOutputSchema)
    @config_api.doc(summary="获取API",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def get(self, api_id: int, query: dict):
        return get_page(Api.query, {"id": api_id}, query["page"], query["per_page"])

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
    @config_api.input(PageSchema, location="query", arg_name="query")
    @config_api.output(RolePageOutputSchema)
    @config_api.doc(summary="获取角色",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def get(self, role_id: int, query: dict):
        return get_page(Role.query, {"id": role_id}, query["page"], query["per_page"])

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


@config_api.put("/role/<int:role_id>/api")
@operate_log
@config_api.input(ApiIdListSchema, location="json", arg_name="data")
@config_api.output(RoleSingleOutputSchema, status_code=201)
@config_api.doc(summary="为角色绑定api",
                responses=[200, 401, 403, 404, 500],
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
                responses=[200, 401, 403, 404, 500],
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
