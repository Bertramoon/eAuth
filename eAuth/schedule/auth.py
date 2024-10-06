import logging

from eAuth.models import Api, Role
from ..constant import CACHE_PREFIX_API, CACHE_TIME_AUTH, CACHE_TIME_AUTH_DELAY, CACHE_PREFIX_ROLE_TO_API
from ..extensions import scheduler, cache

logger = logging.getLogger(__name__)


def cache_auth():
    """
    缓存api、role与api的映射
    :return:
    """
    with scheduler.app.app_context():
        apis = Api.query.all()
        for api in apis:
            cache.set(f"{CACHE_PREFIX_API}_{api.id}", api, CACHE_TIME_AUTH + CACHE_TIME_AUTH_DELAY)
            logger.debug("[cache] Set api cache success")
        roles = Role.query.all()
        for role in roles:
            cache.set(f"{CACHE_PREFIX_ROLE_TO_API}_{role.id}", [api.id for api in role.apis],
                      CACHE_TIME_AUTH + CACHE_TIME_AUTH_DELAY)
            logger.debug("[cache] Set role cache success")
