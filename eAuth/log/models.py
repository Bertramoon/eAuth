from datetime import datetime

from ..extensions import db


class OperateLog(db.Model):
    """
    操作日志
    """
    id = db.Column(db.Integer, primary_key=True)
    # 操作人
    username = db.Column(db.String(32), index=True)
    # 客户端标识
    ip_addr = db.Column(db.String(64), index=True)
    # 操作类型 GET/POST/...
    operate_type = db.Column(db.String(16))
    # 访问接口
    operate_api = db.Column(db.String(256))
    # 响应码
    status_code = db.Column(db.Integer)
    # 操作对象id
    resource_id = db.Column(db.Integer)
    # 请求参数内容
    request_data = db.Column(db.Text)
    # 响应内容
    response_data = db.Column(db.Text)
    # 响应结果
    success = db.Column(db.Boolean)
    # 操作时间
    operate_datetime = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class SecurityLog(db.Model):
    """
    安全日志
    """
    id = db.Column(db.Integer, primary_key=True)
    # 登录用户
    username = db.Column(db.String(32), index=True)
    # 客户端标识
    ip_addr = db.Column(db.String(64), index=True)
    # 操作
    operate = db.Column(db.String(32))
    # 结果
    success = db.Column(db.Boolean)
    # 操作时间
    operate_datetime = db.Column(db.DateTime, default=datetime.utcnow, index=True)
