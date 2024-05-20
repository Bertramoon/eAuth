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

    TOKEN_EXPIRED = 60 * 60 * 3
    MAX_LOGIN_INCORRECT = 5

    # 日志存放位置
    LOG_CONFIG_FILE = os.path.join(BASE_DIR, "log_config.yaml")


class Production(BaseConfig):
    SECRET_KEY = secrets.token_hex(32)
    # 数据库
    SQLALCHEMY_DATABASE_URI = ('mysql+mysqlconnector://'
                               + os.getenv("db_username", 'root') + ":" + os.getenv("db_password", 'root')
                               + "@" + os.getenv("db_url", "127.0.0.1:3306") + "/" + os.getenv("database", 'root'))

    TOKEN_EXPIRED = 60 * 60 * 2
    MAX_LOGIN_INCORRECT = 3

    # 缓存设置
    DEBUG = False


config = {
    'base': BaseConfig,
    'production': Production,
}
