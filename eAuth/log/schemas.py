from apiflask import Schema
from apiflask.fields import String, Integer, Boolean, DateTime, List, Nested
from apiflask.validators import Length, Regexp, OneOf, Range

from ..base.schemas import BasePageOutSchema
from ..base.validators import IP
from ..constant import HTTP_METHODS


class OperateLogSchema(Schema):
    id = Integer(dump_only=True)
    username = String(validate=[Regexp(r'^[a-zA-Z0-9\-_]+$', error='Invalid username'), Length(max=32)])
    ip_addr = String(validate=[IP()])
    operate_type = String(validate=[OneOf(HTTP_METHODS)])
    operate_api = String(
        validate=[Regexp(regex=r'^(/[a-zA-Z0-9\\u4e00-\\u9fff\_\-\.~\<\>\:]+)+$', error='Invalid operate_api'),
                  Length(max=256)])
    status_code = Integer(validate=[Range(min=100, max=599)])
    resource_id = Integer()
    request_data = String(dump_only=True)
    response_data = String(dump_only=True)
    success = Boolean()
    operate_datetime = DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)


class OperateLogPageOutputSchema(BasePageOutSchema):
    data = List(Nested(OperateLogSchema))


class SecurityLogSchema(Schema):
    id = Integer(dump_only=True)
    username = String(validate=[Regexp(r'^[a-zA-Z0-9\-_]+$', error='Invalid username'), Length(max=32)])
    ip_addr = String(validate=[IP()])
    operate = String(validate=[Length(max=32)])
    success = Boolean()
    operate_datetime = DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)


class SecurityLogPageOutputSchema(BasePageOutSchema):
    data = List(Nested(SecurityLogSchema))
