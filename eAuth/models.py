import logging
import re
import time
from urllib.parse import urlparse

from authlib.jose import jwt
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from eAuth.constant import CACHE_PREFIX_USER_TO_ROLE, CACHE_TIME_USER, CACHE_PREFIX_ROLE_TO_API, CACHE_PREFIX_API
from eAuth.extensions import db, cache

logger = logging.getLogger(__name__)

roles_apis = db.Table(
    'roles_apis',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id', ondelete='CASCADE')),
    db.Column('api_id', db.Integer, db.ForeignKey('api.id', ondelete='CASCADE'))
)

users_roles = db.Table(
    'users_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)


class Api(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(256), nullable=False)
    method = db.Column(db.String(8), nullable=False)
    description = db.Column(db.String(512))
    roles = db.relationship('Role', secondary=roles_apis, back_populates='apis')

    __table_args__ = (
        db.UniqueConstraint('url', 'method', name='uix_url_method'),
    )


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False, index=True)
    description = db.Column(db.String(512))
    apis = db.relationship('Api', secondary=roles_apis, back_populates='roles')
    users = db.relationship('User', secondary=users_roles, back_populates='roles')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256))
    locked = db.Column(db.Boolean, default=False)  # 账号是否被锁定/冻结
    login_incorrect = db.Column(db.Integer, default=0)  # 登录错误次数
    email = db.Column(db.String(320), unique=True, nullable=False)

    # 关联角色
    roles = db.relationship('Role', secondary=users_roles, back_populates='users')

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def auth_token(self):
        header = {"alg": "HS256"}
        now = int(time.time())
        payload = {
            "uid": self.id,
            "username": self.username,
            "iat": now,
            "exp": now + current_app.config.get("TOKEN_EXPIRED", 60 * 60)
        }
        return jwt.encode(header, payload, current_app.config["SECRET_KEY"]).decode()

    def lock(self):
        try:
            self.locked = True
            db.session.commit()
        except:
            db.session.rollback()

    def unlock(self):
        try:
            self.locked = False
            db.session.commit()
        except:
            db.session.rollback()

    @property
    def is_locked(self):
        return self.locked

    def can(self, url: str, method: str):
        """
        鉴权

        :param url:
        :param method:
        :return:
        """
        # 获取user对应的role列表
        role_ids = cache.get(f"{CACHE_PREFIX_USER_TO_ROLE}_{self.id}")
        if role_ids is None:
            logger.info(f"[can] Get cache for user {self.id}->{self.username}")
            # 无缓存，读数据库并加入缓存
            role_ids = set(role.id for role in self.roles)
            cache.set(f"{CACHE_PREFIX_USER_TO_ROLE}_{self.id}", role_ids, CACHE_TIME_USER)
        logger.info(f"[can] Get role_ids: `{role_ids}`")

        # 从role列表中提取api列表
        api_set: set[int] = set()
        for role_id in role_ids:
            apis = cache.get(f"{CACHE_PREFIX_ROLE_TO_API}_{role_id}")
            if apis:
                api_set.update(apis)
        logger.info(f"[can] Get api_ids: `{api_set}`")
        # 匹配api，鉴权
        for api_id in api_set:
            api = cache.get(f"{CACHE_PREFIX_API}_{api_id}")
            if not api:
                continue
            if method.upper() == api.method and url_match(url, api.url):
                return True
        return False


def url_match(request_url: str, allowed_url: str):
    parsed_url = urlparse(request_url)
    request_url = parsed_url.path
    logger.debug(f"[url match] request_url: `{request_url}`, allowed_url: {allowed_url}")

    # 将{xx}替换为正则
    pattern = re.sub(r'{[^}]*?}', r'[a-zA-Z0-9\\u4e00-\\u9fff\_\-\.~]+', allowed_url)

    if re.match(f"^{pattern}$", request_url):
        return True
    return False
