from apiflask.fields import String
from apiflask.schemas import Schema

from eAuth.base.schemas import BaseOutSchema


class LoginInputSchema(Schema):
    username = String(required=True)
    password = String(required=True)


class LoginOutputSchema(BaseOutSchema):
    token = String()


class AuthInputSchema(Schema):
    url = String(required=True)
    method = String(required=True)


class AuthOutputSchema(BaseOutSchema):
    pass
