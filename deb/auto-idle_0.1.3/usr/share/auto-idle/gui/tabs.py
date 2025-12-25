from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QSpinBox, QComboBox, QPushButton,
    QCheckBox, QHBoxLayout, QLineEdit, QMenu, QSystemTrayIcon
)

from PyQt6.QtCore import Qt

from config.config import settings
from gui.helpers import (
    is_autostart_enabled, is_asusctl_available,
    get_status_message, show_status_message
)


def ui_show_info_not_found_asusctl(self, current_layout):
    warn = QLabel(
        "Keyboard RGB control is unavailable.\n\n"
        "The tool <b>asusctl</b> was not found on your system.\n\n"
        "Please install it to enable keyboard lighting control."
    )
    warn.setWordWrap(True)
    warn.setAlignment(Qt.AlignCenter)
    warn.setStyleSheet("color: orange;")

    install_hint = QLabel(
        "<code>sudo apt install asusctl</code>"
    )
    install_hint.setAlignment(Qt.AlignCenter)
    install_hint.setStyleSheet("color: gray;")

    current_layout.addStretch()
    current_layout.addWidget(warn)
    current_layout.addSpacing(8)
    current_layout.addWidget(install_hint)
    current_layout.addStretch()


def ui_create_tab_settings(self, tabs):
    settings_tab = QWidget()
    settings_layout = QVBoxLayout(settings_tab)

    self.current_mode_label = QLabel("Current mode: unknown")
    self.current_mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.current_mode_label.setStyleSheet("font-weight: bold;")
    settings_layout.addWidget(self.current_mode_label)

    self.autostart_cb = QCheckBox("Start automatically on login")
    self.autostart_cb.setChecked(is_autostart_enabled())
    settings_layout.addWidget(self.autostart_cb)

    settings_layout.addWidget(QLabel("Switch to idle mode after:"))

    idle_row = QHBoxLayout()
    self.idle_spin = QSpinBox()
    self.idle_spin.setRange(1, 120)
    self.idle_spin.setValue(settings.idle_minutes)
    idle_row.addWidget(self.idle_spin)
    idle_row.addWidget(QLabel("minutes"))
    idle_row.addStretch()
    settings_layout.addLayout(idle_row)

    settings_layout.addSpacing(6)
    settings_layout.addWidget(QLabel("Power profiles:"))

    profiles_layout = QVBoxLayout()

    active_row = QHBoxLayout()
    active_row.addWidget(QLabel("When active:"))
    self.active_mode = QComboBox()
    self.active_mode.addItems(["balanced", "performance"])
    self.active_mode.setCurrentText(settings.active_mode)
    active_row.addWidget(self.active_mode)
    profiles_layout.addLayout(active_row)

    idle_row = QHBoxLayout()
    idle_row.addWidget(QLabel("When idle:"))
    self.idle_mode = QComboBox()
    self.idle_mode.addItems(["power-saver", "balanced"])
    self.idle_mode.setCurrentText(settings.idle_mode)
    idle_row.addWidget(self.idle_mode)
    profiles_layout.addLayout(idle_row)

    settings_layout.addLayout(profiles_layout)

    self.kbd_preview = QLabel()
    self.kbd_preview.setStyleSheet("color: gray;")
    settings_layout.addWidget(self.kbd_preview)

    settings_layout.addStretch()

    ui_add_kbd_buttons_apply_close(self, settings_layout, "apply_btn")
    tabs.addTab(settings_tab, "Settings")


def ui_create_tab_keyboard(self, tabs):
    kbd_tab = QWidget()
    kbd_layout = QVBoxLayout(kbd_tab)

    if not is_asusctl_available():
        ui_show_info_not_found_asusctl(self, kbd_layout)

    else:
        self.kbd_enable_cb = QCheckBox(
            f"Enable power-mode based "
            f"keyboard RGB "
            f"(overrides cpu temperature RGB)"

        )
        self.kbd_enable_cb.setChecked(settings.keyboard["enabled"])

        kbd_layout.addWidget(self.kbd_enable_cb)

        kbd_layout.addWidget(QLabel("Keyboard RGB settings (HEX):"))
        self.kbd_fields = {}

        ui_add_kbd_row(self, kbd_layout, "Power-saver:", "power-saver")
        ui_add_kbd_row(self, kbd_layout, "Balanced:", "balanced")
        ui_add_kbd_row(self, kbd_layout, "Performance:", "performance")

        kbd_layout.addStretch()
        kbd_btn_layout = QHBoxLayout()
        kbd_btn_layout.addStretch()

        for fields in self.kbd_fields.values():
            fields["color"].textChanged.connect(self.mark_dirty)
            fields["brightness"].currentIndexChanged.connect(self.mark_dirty)

    ui_add_kbd_buttons_apply_close(self, kbd_layout, "kbd_apply_btn")
    tabs.addTab(kbd_tab, "Keyboard")


def ui_create_tab_temperature(self, tabs):
    temp_tab = QWidget()
    temp_layout = QVBoxLayout(temp_tab)

    title = QLabel("Keyboard RGB by CPU temperature")
    title.setStyleSheet("font-weight: bold;")
    temp_layout.addWidget(title)

    self.temp_enable_cb = QCheckBox(
        f"Enable temperature-based "
        f"keyboard RGB "
        f"(overrides power-mode RGB)"

    )
    self.temp_enable_cb.setChecked(settings.temperature_rgb["enabled"])

    temp_layout.addWidget(self.temp_enable_cb)

    temp_layout.addSpacing(8)
    temp_layout.addWidget(QLabel("Color scale (HEX):"))

    self.temp_fields = {}

    points_layout = QVBoxLayout()
    for temp in settings.temperature_rgb["points"]:
        ui_add_temp_row(self, points_layout, temp, temp)

    temp_layout.addLayout(points_layout)
    temp_layout.addStretch()

    ui_add_kbd_buttons_apply_close(self, temp_layout, "temp_apply_btn")
    tabs.addTab(temp_tab, "Temperature")


def ui_create_tab_about(self, tabs):
    about_tab = QWidget()
    about_layout = QVBoxLayout(about_tab)

    title = QLabel(f"<b>{settings.app_author["app_name"]}</b>")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)

    subtitle = QLabel("Automatic power profile switching")
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle.setStyleSheet("color: gray;")

    version = QLabel(f"Version {settings.app_author["app_version"]}")
    version.setAlignment(Qt.AlignmentFlag.AlignCenter)

    author = QLabel(f'© {settings.app_author["app_year"]} '
                    f'<a href="{settings.app_author["app_linkedin"]}">'
                    f'{settings.app_author["app_author"]}</a>')
    author.setAlignment(Qt.AlignmentFlag.AlignCenter)
    author.setOpenExternalLinks(True)

    link = QLabel(f'<a href="{settings.app_author["app_github"]}">GitHub repository</a>')
    link.setAlignment(Qt.AlignmentFlag.AlignCenter)
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


def ui_add_kbd_row(self, kbd_layout, label, key):
    row = QHBoxLayout()
    text_label = QLabel(label)
    text_label.setFixedWidth(130)
    row.addWidget(text_label)

    color_input = QLineEdit()
    color_input.setMaxLength(7)
    color_input.setText(settings.keyboard["modes"][key]["color"])
    row.addWidget(color_input)

    swatch = QLabel()
    swatch.setFixedSize(22, 22)
    self.set_swatch_color(swatch, color_input.text())
    row.addWidget(swatch)

    brightness = QComboBox()
    brightness.addItems(["off", "low", "med", "high"])
    brightness.setCurrentText(settings.keyboard["modes"][key]["brightness"])
    row.addWidget(brightness)

    color_input.textChanged.connect(
        lambda text, s=swatch: self.set_swatch_color(s, text)
    )

    self.kbd_fields[key] = {
        "color": color_input,
        "brightness": brightness,
    }

    kbd_layout.addLayout(row)


def ui_add_temp_row(self, layout, temp, key):
    row = QHBoxLayout()
    text_label = QLabel(f"{temp}°C")
    text_label.setFixedWidth(50)
    row.addWidget(text_label)

    hex_input = QLineEdit()
    hex_input.setMaxLength(7)
    hex_input.setText(settings.temperature_rgb["points"][temp])
    row.addWidget(hex_input)

    swatch = QLabel()
    swatch.setFixedSize(22, 22)
    self.set_swatch_color(swatch, hex_input.text())
    row.addWidget(swatch)

    hex_input.textChanged.connect(
        lambda text, s=swatch: self.set_swatch_color(s, text)
    )
    hex_input.textChanged.connect(self.mark_dirty)

    self.temp_fields[temp] = hex_input

    layout.addLayout(row)


def ui_add_kbd_buttons_apply_close(self, current_layout, attr_name):
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()

    btn = QPushButton("Apply")
    btn.setEnabled(False)
    btn.setDefault(True)
    btn.clicked.connect(self.apply)
    setattr(self, attr_name, btn)

    close_btn = QPushButton("Close")
    close_btn.clicked.connect(self.close)

    btn_layout.addWidget(btn)
    btn_layout.addWidget(close_btn)
    current_layout.addLayout(btn_layout)


def ui_setup_tray_menu(window_settings, tray, app):
    menu = QMenu()
    menu.addAction(get_status_message(), window_settings.show)
    menu.addSeparator()
    menu.addAction("Settings", window_settings.show)
    menu.addAction("Quit", app.quit)

    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: show_status_message(tray)
        if reason == QSystemTrayIcon.Trigger else None
    )
