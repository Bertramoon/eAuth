from apiflask.fields import String
from apiflask.schemas import Schema

from eAuth.base.schemas import BaseOutSchema, AuditLogInterface


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
