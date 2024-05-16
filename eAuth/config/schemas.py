from marshmallow.decorators import validates, validates_schema
from sqlalchemy import and_

from apiflask.fields import String, Integer, List, Nested, Boolean
from apiflask.validators import Length, Regexp, OneOf, ValidationError
from apiflask.schemas import Schema

from ..auth.models import Role, Api
from ..extensions import db


class ApiSchema(Schema):
    id = Integer(dump_only=True)
    url = String(required=True,
                 validate=[Length(min=1, max=256), Regexp(regex=r'(/[a-zA-Z0-9\\u4e00-\\u9fff\_\-\.~\{\}]+)+')])
    method = String(required=True, validate=[OneOf(("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"))])
    description = String(validate=[Length(max=512)])

    @validates_schema
    def repeat_validate(self, data, **kwargs):
        url = data.get("url")
        method = data.get("method")
        if db.session.query(db.exists().where(and_(Api.url == url, Api.method == method))).scalar():
            raise ValidationError(f"Duplicate API: {method} {url}")


class RoleSchema(Schema):
    id = Integer(dump_only=True)
    name = String(required=True, validate=[Length(min=1, max=30)])
    description = String(validate=[Length(max=512)])

    @validates("name")
    def name_exists_validate(self, value):
        if db.session.query(db.exists().where(Role.name == value)).scalar():
            raise ValidationError(f"Duplicate name: {value}")


class UserSchema(Schema):
    username = String(required=True, validate=[Length(min=1, max=20)])
    locked = Boolean()


class ApiOutputSchema(ApiSchema):
    roles = List(Nested(RoleSchema))


class RoleOutputSchema(RoleSchema):
    apis = List(Nested(ApiSchema))


class UserOutputSchema(UserSchema):
    roles = List(Nested(RoleSchema))
