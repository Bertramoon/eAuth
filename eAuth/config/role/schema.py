import logging

from apiflask import Schema
from flask import request
from marshmallow import validates, ValidationError, validates_schema
from marshmallow.fields import String, Integer, List, Nested
from marshmallow.validate import Length
from sqlalchemy import and_

from eAuth.base.schemas import PageSchema, BasePageOutSchema, BaseOutSchema, RequestAuditLog, \
    RequestWithIdAuditLog, ResponseGetResourceAuditLog
from eAuth.extensions import db
from eAuth.models import Role

logger = logging.getLogger(__name__)


class RoleQuerySchema(PageSchema):
    search = String(validate=[Length(max=512)])


class RoleSchema(Schema):
    id = Integer(dump_only=True)
    name = String(required=True, validate=[Length(min=1, max=30)])
    description = String(validate=[Length(max=512)])

    @validates("name")
    def name_exists_validate(self, value):
        role_id = request.view_args.get("role_id")
        if role_id:
            condition = and_(Role.id != role_id, Role.name == value)
        else:
            condition = (Role.name == value)
        if db.session.query(db.exists().where(condition)).scalar():
            raise ValidationError(f"Duplicate name: {value}.")


class RoleInputSchema(RoleSchema, RequestWithIdAuditLog):
    pass


class RoleWithApisSchema(RoleSchema):
    apis = List(Nested("ApiSchema"))


class RolePageOutputSchema(BasePageOutSchema):
    data = List(Nested(RoleWithApisSchema))


class RoleSingleOutputSchema(BaseOutSchema, ResponseGetResourceAuditLog):
    data = Nested(RoleWithApisSchema)


class RoleLightSchema(Schema):
    id = Integer()
    name = String()


class RoleLightOutputSchema(BaseOutSchema):
    data = List(Nested(RoleLightSchema))


class RoleIdListInputSchema(Schema, RequestAuditLog):
    """
    用户绑定角色的输入模型
    """
    ids = List(Integer(), validate=[Length(max=1000)])

    @validates_schema
    def exists_validate(self, data, **kwargs):
        ids: list = data.get("ids")
        ids_db = set(item[0] for item in (db.session.query(Role.id).all()))
        for id_ in ids:
            if id_ not in ids_db:
                logger.info(f"[validate user-role] The role_id={id_} is not exists.")
                raise ValidationError(f"The role id `{id_}` from db is not exists.")
