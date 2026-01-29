import logging
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, HttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- CONFIGURATION ---
CONFIG_DIR = Path(__file__).resolve().parent
ROOT_DIR = CONFIG_DIR.parent.parent
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "main.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
CONFIG_DIR = Path(__file__).resolve().parent
ENV_FILE_PATH = CONFIG_DIR / "settings.env"

# # --- FAILSAFE ---
# if not ENV_FILE_PATH.exists():
#     with open(ENV_FILE_PATH, "w") as f:
#         f.write(
#             "ENV=dev\n\n"
#             "WEBHOOK_URL=https://discord.com/api/webhooks/...\n"
#             "RSS_FEED_URL=https://...\n"
#             "CHECK_INTERVAL=60\n"
#             "DATA_FILE=data.json\n"
#         )
#     raise RuntimeError(
#         f"Settings file missing.\n"
#         f"Created default at: {ENV_FILE_PATH}\n"
#         "Please edit it with your actual URLs and restart."
#     )


class Settings(BaseSettings):
    env: Literal["dev", "prod"] = Field(..., validation_alias="ENV")
    webhookUrl: HttpUrl = Field(..., validation_alias="WEBHOOK_URL")
    rssFeedUrl: HttpUrl = Field(..., validation_alias="RSS_FEED_URL")

    checkInterval: int = Field(default=60, ge=30, validation_alias="CHECK_INTERVAL")
    dataFile: Path = Field(
        default=Path("cache/data.json"), validation_alias="DATA_FILE"
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH, env_file_encoding="utf-8", extra="ignore"
    )

    @model_validator(mode="before")
    @classmethod
    def checkForDefaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        for key, value in list(data.items()):
            useDefault = isinstance(value, str) and value.strip().lower() == "default"
            if useDefault:
                del data[key]
        return data


def init_data_file(settings: Settings):
    settings.dataFile.parent.mkdir(parents=True, exist_ok=True)
    if not settings.dataFile.exists():
        with open(settings.dataFile, "w", encoding="utf-8") as f:
            f.write("{}")
        logging.info(f"Initialized new data file at: {settings.dataFile}")


try:
    settings = Settings()
    init_data_file(settings)
except Exception as e:
    logging.error(f"Error loading settings from {ENV_FILE_PATH}:\n{e}", exc_info=True)
    sys.exit(1)
