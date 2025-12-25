import json
import os
from typing import TYPE_CHECKING

from config.config import CONFIG_FILE, CONFIG_DIR, Settings

if TYPE_CHECKING:
    from config import Settings


def load_settings() -> Settings:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            return Settings(**data)
        except Exception as e:
            print("Failed to load config, using defaults:", e)

    return Settings()


def save_settings(settings: Settings) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        # json.dump(settings.model_dump(), f, indent=2)
        json.dump(settings.dict(), f, indent=2)
