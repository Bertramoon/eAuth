import logging
import logging.config

import click
import yaml
from apiflask import APIFlask, abort
from flask import request, g
from sqlalchemy import inspect
from faker import Faker
import random

from .auth.api import auth_api
from .auth.models import User, Api, Role
from .config.api import config_api
from .log.api import log_api
from .constant import CACHE_TIME_AUTH
from .extensions import db, migrate, cors, cache, scheduler, limiter, mail
from .log.models import OperateLog, SecurityLog
from .schedule.auth import cache_auth
from .settings import config
from .utils.auth import verify_token

logger = logging.getLogger(__name__)
fake = Faker('zh_CN')


def create_app(config_name="base"):
    app = APIFlask("eAuth")
    app.config.from_object(config[config_name])

    with open(app.config.get("LOG_CONFIG_FILE", "log_config.yaml"), "r") as f:
        logging.config.dictConfig(yaml.safe_load(f.read()))

    register_extensions(app)
    register_blueprints(app)
    register_processor(app)
    register_commands(app)

    return app


def register_extensions(app):
    db.init_app(app)
    cors.init_app(app)
    migrate.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    scheduler.init_app(app)
    with app.app_context():
        insp = inspect(db.engine)
        if not insp.has_table(Api.__tablename__, db.engine):
            db.create_all()
    scheduler.start()
    scheduler.add_job("cache_api", cache_auth, trigger='interval', seconds=CACHE_TIME_AUTH)
    scheduler.run_job("cache_api")


def register_blueprints(app):
    app.register_blueprint(auth_api)
    app.register_blueprint(config_api)
    app.register_blueprint(log_api)


def register_processor(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(
            db=db,
            User=User,
            Role=Role,
            Api=Api,
            OperateLog=OperateLog,
            SecurityLog=SecurityLog,
            fake=fake
        )

    @app.error_processor
    def custom_error_processor(error):
        return {
                   "error_message": error.message,
                   "detail": error.detail,
                   "success": False
               }, error.status_code, error.headers

    @app.before_request
    def jwt_auth():
        # options直接放行
        if request.method == 'OPTIONS':
            return
        # 认证
        auth_white_list = app.config.get("AUTH_WHITE_LIST", {"POST /api/auth/login"})
        if f"{request.method.upper()} {request.path}" in auth_white_list:
            return
        jwt_token = request.headers.get("Authorization")
        user = verify_token(jwt_token)
        if user is None:
            abort(401, message="Token error")
        g.user = user

        # 鉴权
        permission_white_list = app.config.get("PERMISSION_WHITE_LIST", {"/api/auth/check"})
        if f"{request.method.upper()} {request.path}" in permission_white_list:
            return
        if user.username == "admin":  # admin直接通过
            logger.info("[verify permission] Admin visitor")
            return
        url = request.path
        method = request.method

        if not user.can(url, method):
            logger.info("[verify permission] Verify permission failed: no permission")
            abort(403, message="No permission")


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='重建数据库（删除并初始化）')
    def initdb(drop):
        """重建数据库"""
        if drop:
            click.confirm('Are you sure to delete the database?', abort=True)
            db.drop_all()
            click.echo('The database is deleted successfully, and the new database is creating...')
        db.create_all()
        click.echo('The database create successfully.')

    @app.cli.command()
    @click.option('--username', prompt=True, help='用户名')
    @click.option('--email', prompt=True, help='邮箱')
    @click.option('--password', prompt=True, hide_input=True, help='密码')
    @click.option('--confirm_password', prompt=True, hide_input=True, help='确认密码')
    def create_user(username, email, password, confirm_password):
        """创建新用户"""
        if password != confirm_password:
            click.echo("The confirm_password not equals to the password. Please check it!")
            return
        roles = Role.query.all()
        role_name_id_map = {role.name: role.id for role in roles}
        role_name = click.prompt("Please choose the role for the user",
                                 type=click.Choice(list(role_name_id_map.keys()) + ["null"], case_sensitive=True))
        roles = [Role.query.get(role_name_id_map.get(role_name))] if role_name_id_map.get(role_name) != "null" else []
        user = User(username=username, email=email, roles=roles)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Create user `{username}` successfully.")

    @app.cli.command()
    def init_role():
        api_reader = [
            Api(url=config_api.url_prefix + "/api", method="GET"),
            Api(url=config_api.url_prefix + "/api/{id}", method="GET"),

            Api(url=config_api.url_prefix + "/role", method="GET"),
            Api(url=config_api.url_prefix + "/role/{id}", method="GET"),

            Api(url=config_api.url_prefix + "/user", method="GET"),
            Api(url=config_api.url_prefix + "/user/{id}", method="GET"),
        ]

        api_operator = [
            Api(url=config_api.url_prefix + "/api", method="POST"),
            Api(url=config_api.url_prefix + "/api/{id}", method="PUT"),
            Api(url=config_api.url_prefix + "/api/{id}", method="DELETE"),

            Api(url=config_api.url_prefix + "/role", method="POST"),
            Api(url=config_api.url_prefix + "/role/{id}", method="PUT"),
            Api(url=config_api.url_prefix + "/role/{id}", method="DELETE"),
            Api(url=config_api.url_prefix + "/role/{id}/api", method="PUT"),
        ]

        role1 = Role(name="reader")
        role2 = Role(name="operator")

        role1.apis = api_reader
        role2.apis = api_reader + api_operator
        db.session.add(role1)
        db.session.add(role2)
        db.session.commit()

    @app.cli.command()
    @click.option('--count', default=200, type=int)
    def fake_api(count):
        methods = [
            "GET", "POST", "PUT", "DELETE", "PATCH"
        ]
        for i in range(count):
            try:
                api = Api(
                    url="/"+fake.uri_path(),
                    method=random.choice(methods),
                    description=fake.sentence()
                )
                db.session.add(api)
                db.session.commit()
            except:
                db.session.rollback()

    @app.cli.command()
    @click.option('--count', default=20, type=int)
    def fake_role(count):
        api_list = Api.query.all()
        for i in range(count):
            try:
                role = Role(
                    name=fake.word(),
                    description=fake.sentence()
                )
                role.apis = random.choices(api_list, k=random.randint(2, 10))
                db.session.add(role)
                db.session.commit()
            except:
                db.session.rollback()
