from apiflask import APIBlueprint

config_api_blueprint = APIBlueprint("config", __name__, url_prefix="/api/config")

from .api.api import config_api
from .role.api import config_role
from .user.api import config_user

config_api_blueprint.register_blueprint(config_api)
config_api_blueprint.register_blueprint(config_role)
config_api_blueprint.register_blueprint(config_user)
