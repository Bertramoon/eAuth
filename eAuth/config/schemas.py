import logging
from marshmallow.decorators import validates, validates_schema, pre_load
from sqlalchemy import and_

from apiflask.fields import String, Integer, List, Nested, Boolean
from apiflask.validators import Length, Regexp, OneOf, ValidationError
from apiflask.schemas import Schema

from ..auth.models import Role, Api
from ..base.schemas import BasePageOutSchema, BaseOutSchema, AuditLogInterface
from ..extensions import db

logger = logging.getLogger(__name__)


class ApiSchema(Schema, AuditLogInterface):
    id = Integer(dump_only=True)
    url = String(required=True,
                 validate=[Length(min=1, max=256), Regexp(regex=r'^(/[a-zA-Z0-9\\u4e00-\\u9fff\_\-\.~\{\}]+)+$')])
    method = String(required=True, validate=[OneOf(("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"))])
    description = String(validate=[Length(max=512)])

    @validates_schema
    def repeat_validate(self, data, **kwargs):
        url = data.get("url")
        method = data.get("method")
        if db.session.query(db.exists().where(and_(Api.url == url, Api.method == method))).scalar():
            raise ValidationError(f"Duplicate API: {method} {url}.")

    def get_request_data(self, data: dict, **kwargs) -> dict:
        return data

    def get_resource_id(self, data: dict, **kwargs) -> int:
        return data.get("id")

    def get_response_data(self, data: dict, **kwargs) -> dict:
        pass


class RoleSchema(Schema, AuditLogInterface):
    id = Integer(dump_only=True)
    name = String(required=True, validate=[Length(min=1, max=30)])
    description = String(validate=[Length(max=512)])

    @validates("name")
    def name_exists_validate(self, value):
        if db.session.query(db.exists().where(Role.name == value)).scalar():
            raise ValidationError(f"Duplicate name: {value}")

    def get_request_data(self, data: dict, **kwargs) -> dict:
        return data

    def get_resource_id(self, data: dict, **kwargs) -> int:
        return data.get("id")

    def get_response_data(self, data: dict, **kwargs) -> dict:
        pass


class UserSchema(Schema):
    username = String(required=True, validate=[Length(min=1, max=20)])
    locked = Boolean()


class ApiOutputSchema(ApiSchema):
    roles = List(Nested(RoleSchema))


class ApiPageOutputSchema(BasePageOutSchema):
    data = List(Nested(ApiOutputSchema))


class ApiSingleOutputSchema(BaseOutSchema):
    data = Nested(ApiOutputSchema)


class RoleOutputSchema(RoleSchema):
    apis = List(Nested(ApiSchema))


class RolePageOutputSchema(BasePageOutSchema):
    data = List(Nested(RoleOutputSchema))


class RoleSingleOutputSchema(BaseOutSchema):
    data = Nested(RoleOutputSchema)


class UserOutputSchema(UserSchema):
    roles = List(Nested(RoleSchema))


class UserPageOutputSchema(BasePageOutSchema):
    data = List(Nested(UserOutputSchema))


class ApiIdListSchema(Schema, AuditLogInterface):
    """
    角色绑定API的输入模型
    """
    ids = List(Integer())

    @validates_schema
    def exists_validate(self, data, **kwargs):
        ids: list = data.get("ids")
        ids_db = set(item[0] for item in (db.session.query(Api.id).all()))
        for id_ in ids:
            if id_ not in ids_db:
                logger.info(f"[validate role-api] The api_id={id_} is not exists.")
                raise ValidationError(f"The id `{id_}` from db is not exists.")

    def get_request_data(self, data: dict, **kwargs) -> dict:
        return data

    def get_resource_id(self, data: dict, **kwargs) -> int:
        pass

    def get_response_data(self, data: dict, **kwargs) -> dict:
        pass
