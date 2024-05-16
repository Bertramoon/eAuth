from apiflask.fields import Boolean, Integer
from apiflask.schemas import Schema
from apiflask.validators import Range


class BaseOutSchema(Schema):
    success: bool = Boolean(default=True)


class PageSchema(Schema):
    page = Integer(load_default=1)  # 设置默认页面为 1
    # 将默认值设置为 20，并确保该值不超过 50
    per_page = Integer(load_default=20, validate=Range(max=50))
