import logging

from apiflask import Schema
from flask import request
from marshmallow import validates_schema, ValidationError
from marshmallow.fields import String, Integer, List, Nested
from marshmallow.validate import Length, Regexp, OneOf
from sqlalchemy import and_

from eAuth.auth.models import Api
from eAuth.base.schemas import PageSchema, BasePageOutSchema, BaseOutSchema, RequestWithIdAuditLog, \
    RequestAuditLog, ResponseGetResourceAuditLog
from eAuth.extensions import db

logger = logging.getLogger(__name__)


class ApiQuerySchema(PageSchema):
    url = String(validate=[Length(min=0, max=256), Regexp(regex=r'^[/a-zA-Z0-9\\u4e00-\\u9fff\_\-\.~\{\}]*$')])


class ApiSchema(Schema):
    id = Integer(dump_only=True)
    url = String(required=True,
                 validate=[Length(min=1, max=256), Regexp(regex=r'^(/[a-zA-Z0-9\\u4e00-\\u9fff\_\-\.~\{\}]+)+$')])
    method = String(required=True, validate=[OneOf(("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"))])
    description = String(validate=[Length(max=512)])

    @validates_schema
    def repeat_validate(self, data, **kwargs):
        url = data.get("url")
        method = data.get("method")
        api_id = request.view_args.get("api_id")
        if api_id:
            condition = and_(Api.id != api_id, Api.url == url, Api.method == method)
        else:
            condition = and_(Api.url == url, Api.method == method)
        if db.session.query(db.exists().where(condition)).scalar():
            raise ValidationError(f"Duplicate API: {method} {url}.")


class ApiInputSchema(ApiSchema, RequestWithIdAuditLog):
    pass


class ApiWithRolesSchema(ApiSchema):
    roles = List(Nested("RoleSchema"))


class ApiPageOutputSchema(BasePageOutSchema):
    data = List(Nested(ApiWithRolesSchema))


class ApiSingleOutputSchema(BaseOutSchema, ResponseGetResourceAuditLog):
    data = Nested(ApiWithRolesSchema)


class ApiIdListInputSchema(Schema, RequestAuditLog):
    """
    角色绑定API的输入模型
    """
    ids = List(Integer(), validate=[Length(max=1000)])

    @validates_schema
    def exists_validate(self, data, **kwargs):
        ids: list = data.get("ids")
        ids_db = set(item[0] for item in (db.session.query(Api.id).all()))
        for id_ in ids:
            if id_ not in ids_db:
                logger.info(f"[validate role-api] The api_id={id_} is not exists.")
                raise ValidationError(f"The api id `{id_}` from db is not exists.")
