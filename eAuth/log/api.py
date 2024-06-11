import logging

from apiflask import APIBlueprint, abort, pagination_builder


from .schemas import OperateLogPageOutputSchema, OperateLogSchema, LoginLogSchema, LoginLogPageOutputSchema
from ..base.schemas import PageSchema, DatetimeSchema
from ..utils.model import get_page
from .models import OperateLog, LoginLog

log_api = APIBlueprint("log", __name__, url_prefix="/api/log")
logger = logging.getLogger(__name__)


@log_api.get('/operate-log')
@log_api.input(OperateLogSchema, location="query", arg_name="operate_log")
@log_api.input(DatetimeSchema, location='query', arg_name='between')
@log_api.input(PageSchema, location="query", arg_name="page")
@log_api.output(OperateLogPageOutputSchema)
def query_operate_log(operate_log: dict, between: dict, page: dict):
    query = OperateLog.query
    start_datetime = between.get("start_datetime")
    end_datetime = between.get("end_datetime")
    if start_datetime:
        query = query.filter(OperateLog.operator_datetime >= start_datetime)
    if end_datetime:
        query = query.filter(OperateLog.operator_datetime <= end_datetime)
    return get_page(query, operate_log, page["page"], page["per_page"])


@log_api.get("/login-log")
@log_api.input(LoginLogSchema, location="query", arg_name="login_log")
@log_api.input(DatetimeSchema, location="query", arg_name="between")
@log_api.input(PageSchema, location="query", arg_name="page")
@log_api.output(LoginLogPageOutputSchema)
def query_login_log(login_log: dict, between: dict, page: dict):
    query = LoginLog.query
    start_datetime = between.get("start_datetime")
    end_datetime = between.get("end_datetime")
    if start_datetime:
        query = query.filter(LoginLog.operator_datetime >= start_datetime)
    if end_datetime:
        query = query.filter(LoginLog.operator_datetime <= end_datetime)
    return get_page(query, login_log, page["page"], page["per_page"])
