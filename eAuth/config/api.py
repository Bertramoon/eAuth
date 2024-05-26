import logging
from typing import Any

from flask.views import MethodView
from apiflask import APIBlueprint, abort, pagination_builder

from .schemas import ApiSchema, RoleSchema, ApiPageOutputSchema, RolePageOutputSchema, UserPageOutputSchema
from ..auth.models import Api, Role, User
from ..base.schemas import BaseOutSchema, PageSchema
from ..extensions import db
from ..utils.auth import verify_permission

config_api = APIBlueprint("config", __name__, url_prefix="/api/config")
logger = logging.getLogger(__name__)


class ApiView(MethodView):
    decorators = [verify_permission]

    @config_api.input(PageSchema, location="query", arg_name="query")
    @config_api.output(ApiPageOutputSchema)
    @config_api.doc(summary="获取API",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def get(self, api_id: int, query: dict):
        return _get(Api, "id", api_id, query["page"], query["per_page"])

    @config_api.input(ApiSchema, location="json", arg_name="data")
    @config_api.output(ApiSchema, status_code=201)
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
        return api

    @config_api.input(ApiSchema, location="json", arg_name="data")
    @config_api.output(ApiSchema, status_code=201)
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
        return api

    @config_api.output(BaseOutSchema)
    @config_api.doc(summary="修改API",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def delete(self, api_id: int):
        if not db.session.query(db.exists().where(Api.id == api_id)).scalar():
            abort(404, message="Not found")
        result = Api.query.filter_by(id=api_id).delete()
        try:
            db.session.commit()
        except:
            logger.error("[api] Delete failed", exc_info=True)
            db.session.rollback()
            abort(500, message="server error")
        return {"success": result}


class RoleView(MethodView):
    decorators = [verify_permission]

    @config_api.input(PageSchema, location="query", arg_name="query")
    @config_api.output(RolePageOutputSchema)
    @config_api.doc(summary="获取角色",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def get(self, role_id: int, query: dict):
        return _get(Role, "id", role_id, query["page"], query["per_page"])

    @config_api.input(RoleSchema, location="json", arg_name="data")
    @config_api.output(RoleSchema, status_code=201)
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
        return role

    @config_api.input(RoleSchema, location="json", arg_name="data")
    @config_api.output(RoleSchema, status_code=201)
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
        return role

    @config_api.output(BaseOutSchema)
    @config_api.doc(summary="删除角色",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def delete(self, role_id: int):
        if not db.session.query(db.exists().where(Role.id == role_id)).scalar():
            abort(404, message="Not found")
        result = Role.query.filter_by(id=role_id).delete()
        try:
            db.session.commit()
        except:
            logger.error("[role] Delete failed", exc_info=True)
            db.session.rollback()
            abort(500, message="server error")
        return {"success": result}


class UserView(MethodView):
    decorators = [verify_permission]

    @config_api.input(PageSchema, location="query", arg_name="query")
    @config_api.output(UserPageOutputSchema)
    @config_api.doc(summary="获取用户",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def get(self, username: str, query: dict):
        return _get(User, "username", username, query["page"], query["per_page"])


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


def _get(model: db.Model, field_name: str, field_value: Any, page: int, per_page: int):
    if field_value is None:
        pagination = model.query.paginate(
            page=page,
            per_page=per_page
        )
    else:
        pagination = model.query.filter_by(**{field_name: field_value}).paginate(
            page=page,
            per_page=per_page
        )
    data = pagination.items
    if not data:
        abort(404)
    return {
        "data": data,
        "pagination": pagination_builder(pagination)
    }
