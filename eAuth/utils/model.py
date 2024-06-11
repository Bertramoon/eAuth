from apiflask import abort, pagination_builder
from flask_sqlalchemy.query import Query


def get_page(query: Query, filter_condition: dict, page: int, per_page: int):
    """
    根据条件查询数据，并返回分页后的数据

    :param query: 模型查询
    :param filter_condition: 查询条件
    :param page: 页数
    :param per_page: 每页数据数
    :return:
    """
    effect_filter_condition = {}
    for k, v in filter_condition.items():
        if v is not None:
            effect_filter_condition[k] = v
    pagination = query.filter_by(**effect_filter_condition).paginate(
        page=page,
        per_page=per_page
    )
    data = pagination.items
    if not data:
        abort(404)
    return {
        "data": data,
        "pagination": pagination_builder(pagination)
    }