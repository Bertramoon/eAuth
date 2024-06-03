import logging.config

from apiflask import APIFlask, abort
import click
from flask import request, g
import yaml

from .auth.api import auth_api
from .config.api import config_api
from .extensions import db, migrate, cors, cache, scheduler, limiter
from .settings import config
from .auth.models import User, Api, Role
from .utils.auth import verify_token
from .schedule.auth import cache_auth
from .constant import CACHE_TIME_AUTH


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
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job("cache_api", cache_auth, trigger='interval', seconds=CACHE_TIME_AUTH)
    scheduler.run_job("cache_api")


def register_blueprints(app):
    app.register_blueprint(auth_api)
    app.register_blueprint(config_api)


def register_processor(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(
            db=db,
            User=User,
            Role=Role,
            Api=Api,
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
        if request.path in ["/api/auth/login", "/docs", "/openapi.json"]:
            return
        jwt_token = request.headers.get("Authorization")
        user = verify_token(jwt_token)
        if user is None:
            abort(401, message="Token error")
        g.user = user


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
    @click.option('--password', prompt=True, hide_input=True, help='密码')
    @click.option('--confirm_password', prompt=True, hide_input=True, help='确认密码')
    def create_user(username, password, confirm_password):
        """创建新用户"""
        if password != confirm_password:
            click.echo("The confirm_password not equals to the password. Please check it!")
            return
        roles = Role.query.all()
        role_name_id_map = {role.name: role.id for role in roles}
        role_name = click.prompt("Please choose the role for the user",
                                 type=click.Choice(list(role_name_id_map.keys()) + ["null"], case_sensitive=True))
        roles = [Role.query.get(role_name_id_map.get(role_name))] if role_name_id_map.get(role_name) != "null" else []
        user = User(username=username, roles=roles)
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



