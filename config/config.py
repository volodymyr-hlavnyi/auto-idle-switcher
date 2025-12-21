import os
import sys
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.config_values import DEFAULT_CONFIG, APP_AUTHOR

CONFIG_DIR = os.path.expanduser("~/.config/auto-idle")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
AUTOSTART_FILE = os.path.join(AUTOSTART_DIR, "auto-idle.desktop")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_EXEC = f"{sys.executable} {os.path.join(BASE_DIR, os.path.basename(__file__))}"


class Settings(BaseSettings):
    idle_minutes: int = DEFAULT_CONFIG["idle_minutes"]
    active_mode: Literal["performance", "balanced", "power-saver"] = DEFAULT_CONFIG["active_mode"]
    idle_mode: Literal["performance", "balanced", "power-saver"] = DEFAULT_CONFIG["idle_mode"]

    # IMPORTANT: use default_factory for mutable defaults
    keyboard: dict = Field(default_factory=lambda: DEFAULT_CONFIG["keyboard"].copy())
    temperature_rgb: dict = Field(default_factory=lambda: DEFAULT_CONFIG["temperature_rgb"].copy())
    app_author: dict = Field(default_factory=lambda: APP_AUTHOR.copy())

    # Make it a real field
    last_idle_seconds: int = 0

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
