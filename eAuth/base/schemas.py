from apiflask.fields import Boolean, Integer, Nested
from apiflask.schemas import Schema, PaginationSchema
from apiflask.validators import Range


class BaseOutSchema(Schema):
    success: bool = Boolean(default=True)


class BasePageOutSchema(BaseOutSchema):
    pagination = Nested(PaginationSchema)


class PageSchema(Schema):
    page = Integer(load_default=1, validate=Range(min=1))  # 设置默认页面为 1
    # 将默认值设置为 20，并确保该值不超过 100
    per_page = Integer(load_default=20, validate=Range(min=1, max=100))
