from marshmallow.decorators import validates_schema, validates
from flask import current_app, g
from apiflask.fields import String
from apiflask.validators import Email, Length, ValidationError
from apiflask.schemas import Schema
from sqlalchemy import or_

from eAuth.base.schemas import BaseOutSchema, AuditLogInterface, RequestAuditLog
from eAuth.auth.models import User
from eAuth.extensions import db


class LoginInputSchema(Schema, AuditLogInterface):
    username = String(required=True)
    password = String(required=True)

    def get_request_data(self, data, **kwargs) -> dict:
        return self.get_data_by_keys(data, ("username",))

    def get_resource_id(self, data, **kwargs) -> int:
        pass

    def get_response_data(self, data: dict, **kwargs) -> dict:
        pass


class LoginOutputSchema(BaseOutSchema, AuditLogInterface):
    token = String()

    def get_request_data(self, data: dict, **kwargs) -> dict:
        pass

    def get_resource_id(self, data: dict, **kwargs) -> int:
        pass

    def get_response_data(self, data: dict, **kwargs) -> dict:
        pass


class AuthInputSchema(Schema, AuditLogInterface):
    url = String(required=True)
    method = String(required=True)

    def get_request_data(self, data: dict, **kwargs) -> dict:
        return data

    def get_resource_id(self, data: dict, **kwargs) -> int:
        pass

    def get_response_data(self, data: dict, **kwargs) -> dict:
        pass


class AuthOutputSchema(BaseOutSchema):
    pass


class RegisterInputSchema(Schema, RequestAuditLog):
    username = String(required=True)
    email = String(required=True, validate=[Email(), Length(max=320)])

    @validates_schema
    def validate(self, data, **kwargs):
        domain = current_app.config.get('MAIL_DOMAIN_ONLY')
        email: str = data.get("email", '')
        if domain and email and not (email.count('@') == 1 and email.split('@')[1] == domain):
            raise ValidationError(f"Only support the domain from {domain}.")
        if db.session.query(db.exists().where(
                or_(User.username == data.get('username'), User.email == data.get('email')))).scalar():
            raise ValidationError("The username or email exists.")


class ResetPasswordInputSchema(Schema, RequestAuditLog):
    email = String(required=True, validate=[Email(), Length(max=320)])

    @validates('email')
    def validate_email(self, value):
        domain = current_app.config.get('MAIL_DOMAIN_ONLY')
        if domain and value and not (value.count('@') == 1 and value.split('@')[1] == domain):
            raise ValidationError(f"Only support the domain from {domain}.")
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
