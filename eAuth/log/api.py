import logging

from apiflask import APIBlueprint

from .models import OperateLog, SecurityLog
from .schemas import OperateLogPageOutputSchema, OperateLogSchema, SecurityLogSchema, SecurityLogPageOutputSchema
from ..base.schemas import PageSchema, DatetimeSchema
from ..utils.model import get_page

log_api = APIBlueprint("log", __name__, url_prefix="/api/log")
logger = logging.getLogger(__name__)


@log_api.get('/operate-log')
@log_api.input(OperateLogSchema, location="query", arg_name="operate_log")
@log_api.input(DatetimeSchema, location='query', arg_name='between')
@log_api.input(PageSchema, location="query", arg_name="page")
@log_api.output(OperateLogPageOutputSchema)
def query_operate_log(operate_log: dict, between: dict, page: dict):
    query = OperateLog.query.order_by(OperateLog.operate_datetime.desc())
    start_datetime = between.get("start_datetime")
    end_datetime = between.get("end_datetime")
    if start_datetime:
        query = query.filter(OperateLog.operate_datetime >= start_datetime)
    if end_datetime:
        query = query.filter(OperateLog.operate_datetime <= end_datetime)
    # 精确查询
    like_query_fields = ("username", "ip_addr", "operate_api")
    equal_query_condition = {k: v for k, v in operate_log.items() if k not in like_query_fields}
    # 模糊查询
    for field in like_query_fields:
        if operate_log.get(field):
            query = query.filter(getattr(OperateLog, field).like(f"%{operate_log.get(field)}%"))
    return get_page(query, equal_query_condition, page["page"], page["per_page"])


@log_api.get("/security-log")
@log_api.input(SecurityLogSchema, location="query", arg_name="security_log")
@log_api.input(DatetimeSchema, location="query", arg_name="between")
@log_api.input(PageSchema, location="query", arg_name="page")
@log_api.output(SecurityLogPageOutputSchema)
def query_security_log(security_log: dict, between: dict, page: dict):
    query = SecurityLog.query
    start_datetime = between.get("start_datetime")
    end_datetime = between.get("end_datetime")
    if start_datetime:
        query = query.filter(SecurityLog.operate_datetime >= start_datetime)
    if end_datetime:
        query = query.filter(SecurityLog.operate_datetime <= end_datetime)
    # 精确查询
    like_query_fields = ("username", "ip_addr", "operate")
    equal_query_condition = {k: v for k, v in security_log.items() if k not in like_query_fields}
    # 模糊查询
    for field in like_query_fields:
        if security_log.get(field):
            query = query.filter(getattr(SecurityLog, field).like(f"%{security_log.get(field)}%"))
    return get_page(query, equal_query_condition, page["page"], page["per_page"])
