import logging

from apiflask import APIBlueprint
from apiflask import abort
from flask.views import MethodView

from eAuth.base.schemas import BaseOutSchema
from eAuth.extensions import db
from eAuth.models import Api
from eAuth.utils.decorator import operate_log
from eAuth.utils.model import get_page
from .schema import ApiQuerySchema, ApiPageOutputSchema, ApiInputSchema, ApiSingleOutputSchema

config_api = APIBlueprint("config_api", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)


class ApiView(MethodView):
    @config_api.input(ApiQuerySchema, location="query", arg_name="query")
    @config_api.output(ApiPageOutputSchema)
    @config_api.doc(summary="获取API",
                    responses=[200, 401, 403, 404, 500],
                    security="Authorization")
    def get(self, api_id: int, query: dict):
        model = Api.query
        search = query.get("search")
        if search:
            model = model.filter((Api.url.like(f"%{search}%")) | (Api.description.like(f"%{search}%")))
        method: str = query.get("method")
        if method:
            model = model.filter(Api.method == method)
        return get_page(model, {"id": api_id}, query["page"], query["per_page"])

    @operate_log
    @config_api.input(ApiInputSchema, location="json", arg_name="data")
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
    @config_api.input(ApiInputSchema, location="json", arg_name="data")
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


api_view = ApiView.as_view("api_view")
config_api.add_url_rule("", view_func=api_view, defaults={"api_id": None}, methods=["GET"])
config_api.add_url_rule("", view_func=api_view, methods=["POST"])
config_api.add_url_rule("/<int:api_id>", view_func=api_view, methods=["GET", "PUT", "DELETE"])
