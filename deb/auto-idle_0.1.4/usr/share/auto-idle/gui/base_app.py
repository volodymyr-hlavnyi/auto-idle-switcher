# ---- UI ----
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QVBoxLayout, QTabWidget, QWidget, QLabel

from config.config import settings
from config.config_service import save_settings
from gui.helpers import icon_path_for_mode, get_current_profile, icon_for_mode, enable_autostart, disable_autostart, \
    set_keyboard_color_for_mode, set_profile, apply_temperature_keyboard_rgb
from gui.tabs import ui_create_tab_settings, ui_create_tab_keyboard, ui_create_tab_temperature, ui_create_tab_about

APP_ICON = icon_path_for_mode(settings.active_mode)


class MainWindowAppGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Auto Idle Settings")
        self.setMinimumSize(350, 400)
        self.setWindowIcon(QIcon(APP_ICON))

        main_layout = QVBoxLayout(self)
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Settings Tab
        ui_create_tab_settings(self, tabs)

        # Keyboard Tab
        ui_create_tab_keyboard(self, tabs)

        # Temperature Tab
        ui_create_tab_temperature(self, tabs)

        # About Tab
        ui_create_tab_about(self, tabs)

        # Signals
        self.autostart_cb.stateChanged.connect(self.mark_dirty)
        self.idle_spin.valueChanged.connect(self.mark_dirty)

        self.kbd_enable_cb.stateChanged.connect(self.mark_dirty)
        self.active_mode.currentTextChanged.connect(self.mark_dirty)
        self.idle_mode.currentTextChanged.connect(self.mark_dirty)

        self.active_mode.currentIndexChanged.connect(self.update_keyboard_preview)
        self.idle_mode.currentIndexChanged.connect(self.update_keyboard_preview)

        self.temp_enable_cb.stateChanged.connect(self.mark_dirty)

        self.kbd_enable_cb.toggled.connect(self.on_keyboard_rgb_toggled)
        self.temp_enable_cb.toggled.connect(self.on_temperature_rgb_toggled)

        self.update_keyboard_preview()
        self.refresh_current_mode_from_system()

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def set_swatch_color(self, swatch: QLabel, hex_str: str):
        hex_str = (hex_str or "").strip().lower()

        if len(hex_str) == 7 and all(c in "#0123456789abcdef" for c in hex_str):
            swatch.setStyleSheet(
                f"background-color: {hex_str}; border: 1px solid #555; border-radius: 4px;"
            )
        else:
            swatch.setStyleSheet(
                "background-color: transparent; border: 1px dashed #555; border-radius: 4px;"
            )

    def mark_dirty(self):
        for name in (
                "autostart_cb",
                "apply_btn",
                "kbd_enable_cb",
                "kbd_apply_btn",
                "temp_enable_cb",
                "temp_apply_btn",

        ):
            if hasattr(self, name):
                getattr(self, name).setEnabled(True)

    def update_current_mode(self, mode):
        colors = {
            "power-saver": "green",
            "balanced": "orange",
            "performance": "red",
        }
        self.current_mode_label.setText(f"Current mode: {mode}")
        self.current_mode_label.setStyleSheet(
            f"font-weight: bold; color: {colors.get(mode, 'gray')};"
        )

    def update_keyboard_preview(self):
        mapping = {
            "power-saver": "Green (Low)",
            "balanced": "Yellow / Orange (Med)",
            "performance": "Red (High)",
        }

        self.kbd_preview.setText(
            "Keyboard sync preview:\n"
            f"• When active: {mapping.get(self.active_mode.currentText())}\n"
            f"• When idle: {mapping.get(self.idle_mode.currentText())}"
        )

    def refresh_current_mode_from_system(self):
        profile = get_current_profile()
        if not profile:
            return

        # update label
        self.update_current_mode(profile)

        # sync UI selectors with real system state
        if profile in ("balanced", "performance"):
            self.active_mode.blockSignals(True)
            self.active_mode.setCurrentText(profile)
            self.active_mode.blockSignals(False)

    def on_keyboard_rgb_toggled(self, checked: bool):
        if checked:
            # turn off temperature RGB
            self.temp_enable_cb.blockSignals(True)
            self.temp_enable_cb.setChecked(False)
            self.temp_enable_cb.blockSignals(False)

            settings.keyboard["enabled"] = True
            settings.temperature_rgb["enabled"] = False

        self.mark_dirty()

    def on_temperature_rgb_toggled(self, checked: bool):
        if checked:
            # turn off power-mode RGB
            self.kbd_enable_cb.blockSignals(True)
            self.kbd_enable_cb.setChecked(False)
            self.kbd_enable_cb.blockSignals(False)

            settings.temperature_rgb["enabled"] = True
            settings.keyboard["enabled"] = False

        self.mark_dirty()

    def apply(self):
        settings.idle_minutes = self.idle_spin.value()
        settings.active_mode = self.active_mode.currentText()
        settings.idle_mode = self.idle_mode.currentText()

        settings.keyboard["enabled"] = self.kbd_enable_cb.isChecked()
        for mode, fields in self.kbd_fields.items():
            settings.keyboard["modes"][mode]["color"] = fields["color"].text().lower()
            settings.keyboard["modes"][mode]["brightness"] = fields["brightness"].currentText()

        settings.temperature_rgb["enabled"] = self.temp_enable_cb.isChecked()
        for temp, field in self.temp_fields.items():
            settings.temperature_rgb["points"][temp] = field.text().lower()

        save_settings(settings)

        if self.autostart_cb.isChecked():
            enable_autostart()
        else:
            disable_autostart()

        # apply keyboard immediately
        set_keyboard_color_for_mode(settings.active_mode)
        apply_temperature_keyboard_rgb()

        # apply power profile only if active/idle modes changed
        set_profile(settings.active_mode, idle=0)

        self.apply_btn.setEnabled(False)
        if hasattr(self, "kbd_apply_btn"):
            self.kbd_apply_btn.setEnabled(False)
        print("Settings saved:", settings)
