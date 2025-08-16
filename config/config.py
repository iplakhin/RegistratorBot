import logging
import os
from dataclasses import dataclass
from environs import Env


logger = logging.getLogger(__name__)

@dataclass
class DBSettings:
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str


@dataclass
class BotSettings:
    token: str
    admin_ids: list[int]

@dataclass
class LoggSettings:
    level: str
    format: str


@dataclass
class Config:
    bot: BotSettings
    db: str
    log: LoggSettings


def load_config(path: str | None = None) -> Config:
    env = Env()

    if path:
        if not os.path.exists(path):
            logger.warning(".env file not found at '%s', skipping...", path)
        else:
            logger.info("Loading .env from '%s'", path)

    env.read_env(path)

    token = env("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN must not be empty")

    raw_ids = env.list("ADMIN_IDS", default=[])

    try:
        admin_ids = [int(x) for x in raw_ids]
    except ValueError as e:
        raise ValueError(f"ADMIN_IDS must be integers, got: {raw_ids}") from e

    db = DBSettings(
        DB_USER=env("DB_USER"),
        DB_PASS=env("DB_PASS"),
        DB_HOST=env("DB_HOST"),
        DB_PORT=env.int("DB_PORT"),
        DB_NAME=env("DB_NAME"),
    )

    logg_settings = LoggSettings(
        level=env("LOG_LEVEL"),
        format=env("LOG_FORMAT")
    )

    logger.info("Configuration loaded successfully")

    return Config(
        bot=BotSettings(token=token, admin_ids=admin_ids),
        db=f"postgresql+asyncpg://{db.DB_USER}:{db.DB_PASS}@{db.DB_HOST}:{db.DB_PORT}/{db.DB_NAME}",
        log=logg_settings
    )

settings = load_config()
