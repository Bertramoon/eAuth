CACHE_PREFIX_ROLE = "cache_role"
CACHE_PREFIX_API = "cache_api"
CACHE_PREFIX_ROLE_TO_API = "cache_role_to_api"
CACHE_PREFIX_USER_TO_ROLE = "cache_user_to_role"
# 注销缓存
CACHE_PREFIX_LOGOUT = "cache_logout"
CACHE_TIME_LOGOUT_DELAY = 30

# 缓存设置
CACHE_TIME_AUTH = 10 * 60
CACHE_TIME_AUTH_DELAY = 30
CACHE_TIME_USER = 5 * 60

# 支持的HTTP方法
HTTP_METHODS = (
    'GET',
    'POST',
    'PUT',
    'DELETE',
    'OPTIONS',
)
