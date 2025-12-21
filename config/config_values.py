# ---- Config and paths ----
APP_NAME = "Auto Idle Power Switcher"
APP_VERSION = "0.1.2"
APP_AUTHOR = "Volodymyr Hlavnyi"
APP_YEAR = "2025"
APP_GITHUB = "https://github.com/volodymyr-hlavnyi"
APP_LINKEDIN = "https://www.linkedin.com/in/volodymyr-hlavnyi/"

last_idle_seconds = 0

APP_AUTHOR = {
    "app_name": APP_NAME,
    "app_version": APP_VERSION,
    "app_author": APP_AUTHOR,
    "app_year": APP_YEAR,
    "app_github": APP_GITHUB,
    "app_linkedin": APP_LINKEDIN,
}

DEFAULT_CONFIG = {
    "idle_minutes": 20,
    "active_mode": "balanced",
    "idle_mode": "power-saver",

    "keyboard": {
        "enabled": True,
        "modes": {
            "power-saver": {"color": "#00ff00", "brightness": "low"},
            "balanced": {"color": "#e61e00", "brightness": "med"},
            "performance": {"color": "#ff0000", "brightness": "high"},
        },
    },

    "temperature_rgb": {
        "enabled": False,
        "points": {
            "30": "#00ff00",
            "40": "#66ff00",
            "50": "#ccff00",
            "60": "#ffff00",
            "70": "#ffcc00",
            "80": "#ff9900",
            "90": "#ff6600",
            "100": "#ff3300",
            "110": "#ff0000",
        }
    }
}
