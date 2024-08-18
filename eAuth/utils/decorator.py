import json
import logging
from functools import wraps
from typing import Optional

from flask import g, Response, request

from ..extensions import get_ipaddr, db
from ..log.models import OperateLog, SecurityLog

logger = logging.getLogger(__name__)


def operate_log(func):
    """
    记得装饰器必须装饰在input和output装饰器上面，在route下面

    e.g.
    ```
    @app.post('/api/<int:api_id>')
    @operate_log  # 注意位置
    @app.input(ApiInputSchema, location='json', arg_name='data')
    @app.output(ApiOutputSchema, status_code=201)
    def add_api(api_id: int, data: dict):
        ...
    ```

    :param func:
    :return:
    """
    @wraps(func)
    def decorator(*args, **kwargs):
        exception = None
        response: tuple = None
        try:
            response = func(*args, **kwargs)
        except Exception as e:
            exception = e
        if exception:
            raise exception

        if not isinstance(response, tuple) or len(response) != 2:
            return response
        response_obj: Response
        status_code: int
        response_obj, status_code = response
        if response_obj.is_json and response_obj.json.get("success") is True:
            success = True
        else:
            success = False

        username = g.user.username if g.get("user") else None
        ip_addr = get_ipaddr()
        operate_type = request.method
        operate_api = request.url_rule.rule
        request_data: dict = g.get("request_data")
        resource_id: str = g.get("resource_id")
        response_data: dict = g.get("response_data")
        if resource_id is None and request.url_rule.arguments:
            # 获取第一个路径参数
            url_rule = request.url_rule.rule
            left = url_rule.find('<')
            right = url_rule.find('>')
            first_arg_name = url_rule[left+1:right]
            if ':' in first_arg_name:
                first_arg_name = first_arg_name.split(':')[1]
            resource_id = request.view_args.get(first_arg_name)

        try:
            log_record = OperateLog(
                username=username,
                ip_addr=ip_addr,
                operate_type=operate_type,
                operate_api=operate_api,
                status_code=status_code,
                resource_id=resource_id,
                success=success
            )
            if request_data:
                log_record.request_data = json.dumps(request_data, ensure_ascii=False)
            if response_data:
                log_record.response_data = json.dumps(response_data, ensure_ascii=False)
            db.session.add(log_record)
            db.session.commit()
            if not response_obj.is_json:
                logger.warning(f"[operate log] Response is not json by log record id: {log_record.id}")
        except:
            db.session.rollback()
            logger.error("[operate log] Insert log record failed", exc_info=True)
        return response
    return decorator


def security_log(operate: str):
    """
    记得装饰器必须装饰在input和output装饰器上面，在route下面

    e.g.
    ```
    @app.post('/login')
    @security_log('login')  # 注意位置
    @app.input(LoginInputSchema, location='json', arg_name='data')
    @app.output(LoginOutputSchema)
    def add_api(api_id: int, data: dict):
        ...
    ```

    :param operate: 操作
    :return:
    """
    def inner(func):
        @wraps(func)
        def decorator(*args, **kwargs):
            exception: Optional[Exception] = None
            response: Optional[tuple] = None
            try:
                response = func(*args, **kwargs)
            except Exception as e:
                exception = e

            username = g.user.username if g.get("user") else None
            if username is None:
                username = request.json.get("username")
            ip_addr = get_ipaddr()
            success = False
            # 成功
            response_obj: Optional[Response] = None
            if not exception and isinstance(response, tuple) and len(response) == 2:
                response_obj: Response = response[0]
                if response_obj.is_json and response_obj.json.get("success") is True:
                    success = True

            try:
                log_record = SecurityLog(
                    username=username,
                    ip_addr=ip_addr,
                    operate=operate,
                    success=success
                )
                db.session.add(log_record)
                db.session.commit()
                if response_obj is not None and not response_obj.is_json:
                    logger.warning(f"[login log] Response is not json by log record id: {log_record.id}")
            except:
                db.session.rollback()
                logger.error("[login log] Insert log record failed", exc_info=True)
            if exception:
                raise exception
            return response
        return decorator
    return inner
