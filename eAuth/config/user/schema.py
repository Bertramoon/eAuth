from apiflask import Schema
from flask import g
from marshmallow import validates_schema, ValidationError, validates
from marshmallow.fields import String, Integer, Boolean, List, Nested
from marshmallow.validate import Length, Email
from sqlalchemy import or_

from eAuth.base.schemas import PageSchema, BasePageOutSchema, BaseOutSchema, RequestAuditLog, \
    ResponseGetResourceAuditLog
from eAuth.extensions import db
from eAuth.models import User


class UserSchema(Schema):
    id = Integer(dump_only=True)
    username = String(required=True, validate=[Length(min=1, max=20)], dump_only=True)
    email = String(validate=[Email()])
    locked = Boolean()


class UserInputSchema(UserSchema, RequestAuditLog):
    pass


class UserWithRolesSchema(UserSchema):
    roles = List(Nested("RoleSchema"))


class UserQuerySchema(PageSchema):
    username = String(validate=[Length(min=0, max=20)])


class UserPageOutputSchema(BasePageOutSchema):
    data = List(Nested(UserWithRolesSchema))


class UserSingleOutputSchema(BaseOutSchema, ResponseGetResourceAuditLog):
    data = Nested(UserWithRolesSchema)


class RegisterInputSchema(Schema, RequestAuditLog):
    username = String(required=True)
    email = String(required=True, validate=[Email(), Length(max=320)])

    @validates_schema
    def validate(self, data, **kwargs):
        if db.session.query(db.exists().where(
                or_(User.username == data.get('username'), User.email == data.get('email')))).scalar():
            raise ValidationError("The username or email exists.")


class ResetPasswordInputSchema(Schema, RequestAuditLog):
    email = String(required=True, validate=[Email(), Length(max=320)])

    @validates('email')
    def validate_email(self, value):
        if not db.session.query(db.exists().where(User.email == value)).scalar():
            raise ValidationError("The email hasn't been registered.")


class ChangePasswordInputSchema(Schema):
    password = String(required=True)
    new_password = String(required=True)
    new_password_confirm = String(required=True)

    @validates_schema
    def validate(self, data, **kwargs):
        new_password: str = data.get("new_password")
        new_password_confirm: str = data.get("new_password_confirm")
        if new_password != new_password_confirm:
            raise ValidationError("The confirmed password is different from the password.")

        user = g.get('user')
        password: str = data.get("password")
        if not (user and user.validate_password(password)):
            raise ValidationError("The password is incorrect.")
