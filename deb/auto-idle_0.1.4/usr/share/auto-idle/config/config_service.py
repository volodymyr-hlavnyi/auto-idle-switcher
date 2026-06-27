import json
import os

import config.config as cfg
from config.config import CONFIG_FILE, CONFIG_DIR, Settings


def settings_to_dict(settings: Settings) -> dict:
    if hasattr(settings, "model_dump"):
        return settings.model_dump()
    return settings.dict()


def copy_into_global_settings(source: Settings) -> Settings:
    """
    Keep the same global settings object, but update its values.

    Important because other files already do:
        from config.config import settings

    If we replace the object, those modules still keep the old default object.
    """
    for key, value in settings_to_dict(source).items():
        setattr(cfg.settings, key, value)

    return cfg.settings


def load_settings() -> Settings:
    print("Loading config from:", os.path.abspath(CONFIG_FILE))
    print("Config exists:", os.path.exists(CONFIG_FILE))

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                print(f"Loading settings from {CONFIG_FILE}")
                data = json.load(f)

            print("Loaded config data:", data)
            print("Loaded idle_minutes:", data.get("idle_minutes"))

            loaded = Settings(**data)
            return copy_into_global_settings(loaded)

        except Exception as e:
            print("Failed to load config, using defaults:", e)

    print("Using default settings")
    return cfg.settings


def save_settings(settings: Settings) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)

    print("Saving settings to", os.path.abspath(CONFIG_FILE))

    with open(CONFIG_FILE, "w") as f:
        json.dump(settings_to_dict(settings), f, indent=2)