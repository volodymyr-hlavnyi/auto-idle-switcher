import sys
import subprocess
import time

import json
import os

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget,
    QVBoxLayout, QLabel, QSpinBox, QComboBox, QPushButton
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer

CONFIG_DIR = os.path.expanduser("~/.config/auto-idle")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "idle_minutes": 20,
        "active_mode": "balanced",
        "idle_mode": "power-saver",
    }

def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


# ---- Shared state ----
config = load_config()

current_profile = None


# ---- System helpers ----
def get_idle_seconds():
    out = subprocess.check_output(
        [
            "gdbus", "call",
            "--session",
            "--dest", "org.gnome.Mutter.IdleMonitor",
            "--object-path", "/org/gnome/Mutter/IdleMonitor/Core",
            "--method", "org.gnome.Mutter.IdleMonitor.GetIdletime"
        ],
        text=True
    ).strip()

    ms = int(out.split()[1].strip(",)"))
    return ms // 1000


def set_profile(profile, idle):
    global current_profile
    if current_profile == profile:
        return

    subprocess.run(
        ["powerprofilesctl", "set", profile],
        check=True
    )

    current_profile = profile
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] Switched to {profile} (idle {idle}s)")


# ---- UI ----
class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Idle Settings")
        self.setFixedSize(300, 220)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Idle time (minutes):"))
        self.idle_spin = QSpinBox()
        self.idle_spin.setRange(1, 120)
        self.idle_spin.setValue(config["idle_minutes"])
        layout.addWidget(self.idle_spin)

        layout.addWidget(QLabel("Mode when active:"))
        self.active_mode = QComboBox()
        self.active_mode.addItems(["balanced", "performance"])
        layout.addWidget(self.active_mode)

        layout.addWidget(QLabel("Mode when idle:"))
        self.idle_mode = QComboBox()
        self.idle_mode.addItems(["power-saver", "balanced"])
        layout.addWidget(self.idle_mode)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply)
        layout.addWidget(self.apply_btn)

        self.setLayout(layout)

    def apply(self):
        config["idle_minutes"] = self.idle_spin.value()
        config["active_mode"] = self.active_mode.currentText()
        config["idle_mode"] = self.idle_mode.currentText()
        print("Settings applied:", config)


# ---- App ----
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

settings = SettingsWindow()

tray = QSystemTrayIcon(QIcon.fromTheme("battery"))
tray.setToolTip("Auto Idle Power Switcher")

menu = QMenu()
menu.addAction("Settings", settings.show)
menu.addAction("Quit", app.quit)
tray.setContextMenu(menu)
tray.show()


# ---- Background timer ----
def tick():
    idle = get_idle_seconds()
    limit = config["idle_minutes"] * 60

    if idle >= limit:
        set_profile(config["idle_mode"], idle)
    else:
        set_profile(config["active_mode"], idle)


timer = QTimer()
timer.timeout.connect(tick)
timer.start(5000)  # every 5 seconds

sys.exit(app.exec())
