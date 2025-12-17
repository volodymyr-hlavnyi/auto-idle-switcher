import sys
import subprocess
import time

import json
import os

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget,
    QVBoxLayout, QLabel, QSpinBox, QComboBox, QPushButton, QCheckBox, QHBoxLayout,
    QTabWidget
)
from PySide6.QtGui import QIcon, QDesktopServices, QPixmap, QPainter, QColor
from PySide6.QtCore import QTimer, Qt, QUrl

# ---- Config and paths ----
APP_NAME = "Auto Idle Power Switcher"
APP_VERSION = "0.1.0"
APP_AUTHOR = "Volodymyr Hlavnyi"
APP_YEAR = "2025"
APP_GITHUB = "https://github.com/volodymyr-hlavnyi"
APP_LINKEDIN = "https://www.linkedin.com/in/volodymyr-hlavnyi/"

CONFIG_DIR = os.path.expanduser("~/.config/auto-idle")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
AUTOSTART_FILE = os.path.join(AUTOSTART_DIR, "auto-idle.desktop")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_EXEC = f"{sys.executable} {os.path.join(BASE_DIR, os.path.basename(__file__))}"

last_idle_seconds = 0


def is_autostart_enabled():
    return os.path.exists(AUTOSTART_FILE)


def format_tooltip(profile, idle_seconds):
    mins = idle_seconds // 60
    return (
        "Auto Idle Power Switcher\n"
        f"Mode: {profile}\n"
        f"Idle: {mins} min"
    )


def show_status_message():
    profile = get_current_profile() or "unknown"
    mins = last_idle_seconds // 60

    tray.showMessage(
        "Auto Idle Power Switcher",
        f"Mode: {profile}\nIdle: {mins} min",
        QSystemTrayIcon.Information,
        3000
    )


def get_status_message():
    profile = get_current_profile() or "unknown"

    return f"Mode: {profile}"


def get_current_profile():
    try:
        out = subprocess.check_output(
            ["powerprofilesctl", "get"],
            text=True
        ).strip()
        return out
    except Exception as e:
        print("Failed to get current profile:", e)
        return None


def enable_autostart():
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    with open(AUTOSTART_FILE, "w") as f:
        f.write(
            f"""[Desktop Entry]
            Type=Application
            Name=Auto Idle Power Switcher
            Comment=Automatically switch power profiles based on idle time
            Exec={APP_EXEC}
            Icon={APP_ICON}
            Terminal=false
            X-GNOME-Autostart-enabled=true
            """)
    print("Autostart enabled")


def disable_autostart():
    if os.path.exists(AUTOSTART_FILE):
        os.remove(AUTOSTART_FILE)
        print("Autostart disabled")


def icon_path_for_mode(mode):
    ICON_GREEN = os.path.join(BASE_DIR, "icons", "battery_green.svg")
    ICON_YELLOW = os.path.join(BASE_DIR, "icons", "battery_yellow.svg")
    ICON_RED = os.path.join(BASE_DIR, "icons", "battery_red.svg")

    icons_path = {
        "power-saver": ICON_GREEN,
        "balanced": ICON_YELLOW,
        "performance": ICON_RED,
    }
    return icons_path.get(mode)


def icon_for_mode(mode):
    path = icon_path_for_mode(mode)
    if path and os.path.exists(path):
        return QIcon(path)
    return QIcon()


# def icon_for_mode(mode):
#     color_map = {
#         "power-saver": QColor("green"),
#         "balanced": QColor("yellow"),
#         "performance": QColor("red"),
#     }
#
#     pixmap = QPixmap(24, 24)
#     pixmap.fill(Qt.transparent)
#
#     painter = QPainter(pixmap)
#     painter.setRenderHint(QPainter.Antialiasing)
#     painter.setBrush(color_map.get(mode, QColor("gray")))
#     painter.setPen(Qt.NoPen)
#     painter.drawEllipse(2, 2, 20, 20)
#     painter.end()
#
#     return QIcon(pixmap)


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print("Failed to load config:", e)
    return {
        "idle_minutes": 20,
        "active_mode": "balanced",
        "idle_mode": "power-saver",
    }


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


# ---- System helpers ----
def get_idle_seconds():
    try:
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
        # expected format like "(uint64 12345,)"
        parts = out.split()
        if len(parts) >= 2:
            ms = int(parts[1].strip(",)"))
            return ms // 1000
    except Exception as e:
        print("get_idle_seconds failed:", e)
    return 0


def set_profile(profile, idle):
    global current_profile
    if current_profile == profile:
        return

    try:
        subprocess.run(
            ["powerprofilesctl", "set", profile],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("Failed to set profile:", e)
        return

    current_profile = profile

    icon = icon_for_mode(profile)

    # update tray icon
    if tray:
        tray.setIcon(icon)

    # update app + window icons
    app.setWindowIcon(icon)
    settings.setWindowIcon(icon)

    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] Switched to {profile} (idle {idle}s)")


# ---- UI ----
class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Auto Idle Settings")
        self.setFixedSize(340, 280)
        self.setWindowIcon(QIcon(APP_ICON))

        main_layout = QVBoxLayout(self)

        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # =========================
        # Settings Tab
        # =========================
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)

        self.current_mode_label = QLabel("Current mode: unknown")
        self.current_mode_label.setAlignment(Qt.AlignCenter)
        self.current_mode_label.setStyleSheet("font-weight: bold;")

        settings_layout.addWidget(self.current_mode_label)

        # Autostart
        self.autostart_cb = QCheckBox("Start automatically on login")
        self.autostart_cb.setChecked(is_autostart_enabled())
        settings_layout.addWidget(self.autostart_cb)

        # Idle time
        settings_layout.addWidget(QLabel("Switch to idle mode after:"))

        idle_row = QHBoxLayout()
        self.idle_spin = QSpinBox()
        self.idle_spin.setRange(1, 120)
        self.idle_spin.setValue(config["idle_minutes"])
        idle_row.addWidget(self.idle_spin)
        idle_row.addWidget(QLabel("minutes"))
        idle_row.addStretch()

        settings_layout.addLayout(idle_row)

        # Power profiles
        settings_layout.addSpacing(6)
        settings_layout.addWidget(QLabel("Power profiles:"))

        profiles_layout = QVBoxLayout()

        active_row = QHBoxLayout()
        active_row.addWidget(QLabel("When active:"))
        self.active_mode = QComboBox()
        self.active_mode.addItems(["balanced", "performance"])
        active_row.addWidget(self.active_mode)
        profiles_layout.addLayout(active_row)

        idle_profile_row = QHBoxLayout()
        idle_profile_row.addWidget(QLabel("When idle:"))
        self.idle_mode = QComboBox()
        self.idle_mode.addItems(["power-saver", "balanced"])
        idle_profile_row.addWidget(self.idle_mode)
        profiles_layout.addLayout(idle_profile_row)

        settings_layout.addLayout(profiles_layout)

        # Buttons
        settings_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setDefault(True)
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.apply)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)

        self.autostart_cb.stateChanged.connect(self.mark_dirty)
        self.idle_spin.valueChanged.connect(self.mark_dirty)
        self.active_mode.currentIndexChanged.connect(self.mark_dirty)
        self.idle_mode.currentIndexChanged.connect(self.mark_dirty)

        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.close_btn)

        settings_layout.addLayout(btn_layout)

        tabs.addTab(settings_tab, "Settings")

        # =========================
        # About Tab
        # =========================
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)

        title = QLabel(f"<b>{APP_NAME}</b>")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Automatic power profile switching")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray;")

        version = QLabel(f"Version {APP_VERSION}")
        version.setAlignment(Qt.AlignCenter)

        author = QLabel(f'© {APP_YEAR} <a href="{APP_LINKEDIN}">{APP_AUTHOR}</a>')
        author.setAlignment(Qt.AlignCenter)
        author.setOpenExternalLinks(True)

        link = QLabel(f'<a href="{APP_GITHUB}">GitHub repository</a>')
        link.setAlignment(Qt.AlignCenter)
        link.setOpenExternalLinks(True)

        about_layout.addStretch()
        about_layout.addWidget(title)
        about_layout.addWidget(subtitle)
        about_layout.addSpacing(8)
        about_layout.addWidget(version)
        about_layout.addWidget(author)
        about_layout.addSpacing(8)
        about_layout.addWidget(link)
        about_layout.addStretch()

        tabs.addTab(about_tab, "About")

    def mark_dirty(self):
        self.apply_btn.setEnabled(True)

    def update_current_mode(self, mode):
        colors = {
            "power-saver": "green",
            "balanced": "orange",
            "performance": "red",
        }
        color = colors.get(mode, "gray")
        self.current_mode_label.setText(f"Current mode: {mode}")
        self.current_mode_label.setStyleSheet(
            f"font-weight: bold; color: {color};"
        )

    def refresh_current_mode_from_system(self):
        profile = get_current_profile()
        if profile:
            self.update_current_mode(profile)
            tray.setIcon(icon_for_mode(profile))

    def apply(self):
        config["idle_minutes"] = self.idle_spin.value()
        config["active_mode"] = self.active_mode.currentText()
        config["idle_mode"] = self.idle_mode.currentText()
        save_config(config)

        if self.autostart_cb.isChecked():
            enable_autostart()
        else:
            disable_autostart()

        # Immediately apply active profile
        set_profile(config["active_mode"], idle=0)

        self.apply_btn.setEnabled(False)
        print("Settings saved:", config)


# ---- Shared state ----
config = load_config()
current_profile = None
APP_ICON = icon_path_for_mode(config["active_mode"])

# ---- App ----
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
if APP_ICON:
    app.setWindowIcon(QIcon(APP_ICON))

settings = SettingsWindow()
settings.update_current_mode(config["active_mode"])

# tray = QSystemTrayIcon(QIcon.fromTheme("battery"))
# tray = QSystemTrayIcon(icon_for_mode(config["active_mode"]))
tray = QSystemTrayIcon(QIcon(APP_ICON) if APP_ICON else icon_for_mode(config["active_mode"]))
tray.setToolTip("Auto Idle Power Switcher")

menu = QMenu()
menu.addAction(get_status_message(), settings.show)
menu.addSeparator()
menu.addAction("Settings", settings.show)
menu.addAction("Quit", app.quit)
tray.setContextMenu(menu)
tray.activated.connect(
    lambda reason: show_status_message()
    if reason == QSystemTrayIcon.Trigger else None
)

tray.show()


# ---- Background timer ----
def tick():
    global last_idle_seconds

    idle = get_idle_seconds()
    last_idle_seconds = idle
    limit = config["idle_minutes"] * 60

    if idle >= limit:
        set_profile(config["idle_mode"], idle)
    else:
        set_profile(config["active_mode"], idle)

    # keep UI in sync with real system state
    settings.refresh_current_mode_from_system()

    # update tray tooltip from real state
    current = get_current_profile()
    if current:
        tray.setToolTip(format_tooltip(current, idle))


timer = QTimer()
timer.timeout.connect(tick)
timer.start(5000)  # every 5 seconds

sys.exit(app.exec())
