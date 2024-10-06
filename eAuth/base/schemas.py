from abc import ABC, abstractmethod

from apiflask.fields import Boolean, Integer, Nested, DateTime
from apiflask.schemas import Schema, PaginationSchema
from apiflask.validators import Range
from flask import g
from marshmallow import pre_load, post_dump


class BaseOutSchema(Schema):
    success: bool = Boolean(default=True)


class BasePageOutSchema(BaseOutSchema):
    pagination = Nested(PaginationSchema)


class PageSchema(Schema):
    page = Integer(load_default=1, validate=Range(min=1))  # 设置默认页面为 1
    # 将默认值设置为 20，并确保该值不超过 100
    per_page = Integer(load_default=20, validate=Range(min=1, max=200))


class DatetimeSchema(Schema):
    start_datetime = DateTime(format='%Y-%m-%d %H:%M:%S', load_only=True)
    end_datetime = DateTime(format='%Y-%m-%d %H:%M:%S', load_only=True)


class AuditLogInterface(ABC):
    """
    审计日志接口。需要注意的是，每个接口只能有一个input和output schema实现该接口，否则出现多个schema相互覆盖的情况就可能会得到不符合预期的结果
    """
    @abstractmethod
    def get_request_data(self, data: dict, **kwargs) -> dict:
        pass

    @abstractmethod
    def get_resource_id(self, data: dict, **kwargs) -> int:
        pass

    @abstractmethod
    def get_response_data(self, data: dict, **kwargs) -> dict:
        pass

    @staticmethod
    def get_data_by_keys(data: dict, keys: tuple):
        result = {}
        for key in keys:
            if key in data:
                result[key] = data[key]
        return result

    @pre_load
    def _set_request_data(self, data: dict, **kwargs) -> dict:
        request_data = self.get_request_data(data, **kwargs)
        if request_data:
            g.request_data = request_data

        resource_id = self.get_resource_id(data, **kwargs)
        if resource_id:
            g.resource_id = resource_id
        return data

    @post_dump
    def _set_response_data(self, data: dict, **kwargs) -> dict:
        response_data = self.get_response_data(data, **kwargs)
        if response_data:
            g.response_data = response_data

        resource_id = self.get_resource_id(data, **kwargs)
        if resource_id:
            g.resource_id = resource_id
        return data


class RequestAuditLog(AuditLogInterface):
    def get_request_data(self, data: dict, **kwargs) -> dict:
        return data

    def get_resource_id(self, data: dict, **kwargs) -> int:
        pass

    def get_response_data(self, data: dict, **kwargs) -> dict:
        pass


class RequestWithIdAuditLog(RequestAuditLog):
    def get_resource_id(self, data: dict, **kwargs) -> int:
        return data.get("id")


class ResponseGetResourceAuditLog(AuditLogInterface):
    def get_request_data(self, data: dict, **kwargs) -> dict:
        pass

    def get_resource_id(self, data: dict, **kwargs) -> int:
        if data.get("success") is True and isinstance(data.get("data"), dict):
            id_ = data.get("data").get("id")
            if id_ is not None:
                return id_

    def get_response_data(self, data: dict, **kwargs) -> dict:
        pass
