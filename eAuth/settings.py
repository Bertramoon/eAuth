import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

validation_error_detail_schema = {
    'type': 'object',
    'properties': {
        '<location>': {
            'type': 'object',
            'properties': {
                '<field_name>': {
                    'type': 'array',
                    'items': {
                        'type': 'string'
                    }
                }
            }
        }
    }
}

# schema for validation error response
validation_error_schema = {
    'properties': {
        'detail': validation_error_detail_schema,
        'message': {
            'type': 'string'
        },
        # 'success': {
        #     'type': 'boolean',
        #     'value': 'false',
        # }
    },
    'type': 'object'
}

# schema for generic error response
http_error_schema = {
    'properties': {
        'detail': {
            'type': 'object'
        },
        'message': {
            'type': 'string'
        },
        # 'success': {
        #     'type': 'boolean',
        #     'default': 'false',
        # }
    },
    'type': 'object'
}

security_schemes = {
    'Authorization': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
    }
}


class BaseConfig(object):
    SECRET_KEY = "cc9a532b90c98f03c9f35259f45d5faad8b5bfd16c85e9b1fb8daff1a795d781"

    # sql数据库
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # json中文显示
    JSON_AS_ASCII = False

    # api文档设置
    VALIDATION_ERROR_SCHEMA = validation_error_schema
    HTTP_ERROR_SCHEMA = http_error_schema
    SECURITY_SCHEMES = security_schemes

    # SQL打印
    SQLALCHEMY_ECHO = True

    # 缓存设置
    DEBUG = True
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    # 开启缓存鉴权
    CACHE_AUTH_SWITCH = True

    # token有效期
    TOKEN_EXPIRED = 60 * 60 * 3

    # 登录失败防暴力破解
    SHORT_MAX_LOGIN_INCORRECT = 5  # 短期最大登录失败次数
    SHORT_MAX_LOGIN_DELAY = 1  # 短期最大登录失败后能够再次登录的时间间隔（小时）
    MAX_LOGIN_INCORRECT = 15  # 最大登录失败次数

    # 日志存放位置
    LOG_CONFIG_FILE = os.path.join(BASE_DIR, "log_config.yaml")

    # 不认证不鉴权接口
    AUTH_WHITE_LIST = {"POST /api/auth/login", "GET /docs", "GET /openapi.json"}

    # 不鉴权接口
    PERMISSION_WHITE_LIST = {"POST /api/auth/check"}

    # 邮件设置
    MAIL_USE_SSL = True
    MAIL_PORT = 465
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = (os.getenv("MAIL_NAME"), MAIL_USERNAME)
    MAIL_DOMAIN_ONLY = os.getenv("MAIL_DOMAIN", None)


class Production(BaseConfig):
    SECRET_KEY = secrets.token_hex(32)
    # 数据库
    SQLALCHEMY_DATABASE_URI = ('mysql+pymysql://'
                               + os.getenv("db_username", 'root') + ":" + os.getenv("db_password", 'root')
                               + "@" + os.getenv("db_url", "127.0.0.1:3306") + "/" + os.getenv("database", 'eauth')) \
                              + "?charset=utf8"

    TOKEN_EXPIRED = 60 * 60 * 2
    SHORT_MAX_LOGIN_INCORRECT = 3
    SHORT_MAX_LOGIN_DELAY = 3
    MAX_LOGIN_INCORRECT = 9

    # 缓存设置
    DEBUG = False

    # 邮件约束
    MAIL_DOMAIN_ONLY = os.getenv("MAIL_DOMAIN", None)


class Testing(Production):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    'base': BaseConfig,
    'production': Production,
    'test': Testing
}
