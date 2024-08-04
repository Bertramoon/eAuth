from flask import request
from flask_caching import Cache
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask_limiter import Limiter
from flask_mail import Mail


def get_ipaddr():
    xff = request.headers.get("X-Forwarded-For", "")
    client_ip = xff.split(",")[-1].strip()
    return client_ip or request.headers.get("X-Real-Ip") or request.remote_addr or '127.0.0.1'


db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
cache = Cache()
scheduler = APScheduler()
limiter = Limiter(key_func=get_ipaddr, default_limits=['5000/day', '1000/hour', '200/minute', '5/second'])
mail = Mail()
