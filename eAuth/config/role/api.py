import logging

from apiflask import abort, APIBlueprint
from flask.views import MethodView

from eAuth.base.schemas import BaseOutSchema
from eAuth.extensions import db
from eAuth.models import Role, Api
from eAuth.utils.decorator import operate_log
from eAuth.utils.model import get_page
from .schema import RoleQuerySchema, RolePageOutputSchema, RoleInputSchema, RoleSingleOutputSchema
from ..api.schema import ApiQuerySchema, ApiPageOutputSchema, ApiIdListInputSchema

config_role = APIBlueprint("config_role", __name__, url_prefix="/role")

logger = logging.getLogger(__name__)


class RoleView(MethodView):
    @config_role.input(RoleQuerySchema, location="query", arg_name="query")
    @config_role.output(RolePageOutputSchema)
    @config_role.doc(summary="获取角色",
                     responses=[200, 401, 403, 404, 500],
                     security="Authorization")
    def get(self, role_id: int, query: dict):
        model = Role.query
        search = query.get("search")
        if search:
            model = model.filter((Role.name.like(f"%{search}%")) | (Role.description.like(f"%{search}%")))
        return get_page(model, {"id": role_id}, query["page"], query["per_page"])

    @operate_log
    @config_role.input(RoleInputSchema, location="json", arg_name="data")
    @config_role.output(RoleSingleOutputSchema, status_code=201)
    @config_role.doc(summary="创建角色",
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
    @config_role.input(RoleInputSchema, location="json", arg_name="data")
    @config_role.output(RoleSingleOutputSchema, status_code=201)
    @config_role.doc(summary="修改角色",
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
    @config_role.output(BaseOutSchema)
    @config_role.doc(summary="删除角色",
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


role_view = RoleView.as_view("role_view")
config_role.add_url_rule("", view_func=role_view, defaults={"role_id": None}, methods=["GET"])
config_role.add_url_rule("", view_func=role_view, methods=["POST"])
config_role.add_url_rule("/<int:role_id>", view_func=role_view, methods=["GET", "PUT", "DELETE"])


@config_role.get("/unbind/<int:role_id>")
@config_role.input(ApiQuerySchema, location="query", arg_name="query")
@config_role.output(ApiPageOutputSchema)
@config_role.doc(summary="查询角色未绑定的API列表",
                 responses=[200, 401, 403, 404, 500],
                 security="Authorization")
def get_role_unbind_api(role_id: int, query: dict):
    role: Role = Role.query.get_or_404(role_id)
    model = Api.query.filter(~Api.id.in_(item.id for item in role.apis))
    search = query.get("search")
    if search:
        model = model.filter((Api.url.like(f"%{search}%")) | (Api.description.like(f"%{search}%")))
    method: str = query.get("method")
    if method:
        model = model.filter(Api.method == method)
    result = get_page(model, {}, query["page"], query["per_page"], role_id=role_id)
    return result


@config_role.put("/<int:role_id>/api")
@operate_log
@config_role.input(ApiIdListInputSchema, location="json", arg_name="data")
@config_role.output(RoleSingleOutputSchema, status_code=201)
@config_role.doc(summary="为角色绑定api",
                 responses=[201, 401, 403, 404, 500],
                 security="Authorization")
def role_add_api(role_id: int, data: dict):
    # 查询角色
    role: Role = Role.query.get_or_404(role_id)
    # 筛选出需要添加的API id列表
    ids = set(data["ids"])
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


@config_role.delete("/<int:role_id>/api")
@operate_log
@config_role.input(ApiIdListInputSchema, location="json", arg_name="data")
@config_role.output(RoleSingleOutputSchema, status_code=201)
@config_role.doc(summary="为角色解绑api",
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
