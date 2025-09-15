import os


def get_supported_env_variables():

    return {
        "CCAT_CORE_HOST": "localhost",
        "CCAT_CORE_PORT": "1865",
        "CCAT_CORE_USE_SECURE_PROTOCOLS": "", # TODOV2: conflate these 3 envs into one: http://localhost:1865
        "CCAT_ADMIN_CREDENTIALS": "admin:admin",
        "CCAT_API_KEY": "meow",
        "CCAT_DEBUG": "true",
        "CCAT_LOG_LEVEL": "INFO",
        "CCAT_CORS_ALLOWED_ORIGINS": None,
        "CCAT_SQL": "sqlite+aiosqlite:///data/sqlite/core.db", # TODOV2: db could be encrypted by default # postgresql+asyncpg://user:password@localhost/dbname
        "CCAT_JWT_SECRET": "meow_jwt",
        "CCAT_JWT_ALGORITHM": "HS256",
        "CCAT_JWT_EXPIRE_MINUTES": str(60 * 24),  # JWT expires after 1 day
        "CCAT_HTTPS_PROXY_MODE": "false",
        "CCAT_CORS_FORWARDED_ALLOW_IPS": "*",
        "CCAT_CORS_ENABLED": "true",

        # TODOV2: manage cache via factory
        "CCAT_CACHE_TYPE": "in_memory",
        "CCAT_CACHE_DIR": "/tmp", # TODOV2: will it break on winzozz?
    }


def get_env(name) -> str | None:
    """Utility to get an environment variable value. To be used only for supported Cat envs.
    - covers default supported variables and their default value
    - automagically handles legacy env variables missing the prefix "CCAT_"
    """

    cat_default_env_variables = get_supported_env_variables()

    if name in cat_default_env_variables:
        default = cat_default_env_variables[name]
    else:
        default = None

    return os.getenv(name, default)
