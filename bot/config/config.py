from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str
    GLOBAL_CONFIG_PATH: str = "TG_FARM"

    FIX_CERT: bool = False

    REF_ID: str = "s5XexnShM18Ftejz"

    PERFORM_QUESTS: bool = True
    CHANNEL_SUBSCRIBE_TASKS: bool = True
    UPGRADE_CARDS: bool = True
    SPIN_THE_WHEEL: bool = True
    AUTO_TAP: bool = True

    RANDOM_SLEEP_TIME: list[int] = [3600, 10800]

    RANDOM_SESSION_START_DELAY: int = 30

    SESSIONS_PER_PROXY: int = 1
    USE_PROXY_FROM_FILE: bool = True
    DISABLE_PROXY_REPLACE: bool = False
    USE_PROXY_CHAIN: bool = False

    DEVICE_PARAMS: bool = False

    DEBUG_LOGGING: bool = False


settings = Settings()
