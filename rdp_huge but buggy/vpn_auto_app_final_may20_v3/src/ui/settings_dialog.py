import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTabWidget, QWidget, QFormLayout, QLabel, QComboBox, 
    QLineEdit, QFileDialog, QGroupBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".vpn_auto_app_settings.json")
DEFAULT_PROFILE_DIR = os.path.join(os.path.expanduser("~"), ".vpn_auto_app_profiles")
DEFAULT_ICON_DIR = os.path.join(os.path.expanduser("~"), ".vpn_auto_app_icons")

class SettingsDialog(QDialog):
    """Dialog for managing application-wide settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setMinimumSize(500, 400)

        self.settings = self._load_settings()

        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_appearance_tab()
        self._create_behavior_tab()
        self._create_about_help_tab()

        # Dialog buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Settings")
        self.cancel_button = QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        # Connect signals
        self.save_button.clicked.connect(self._save_and_accept)
        self.cancel_button.clicked.connect(self.reject)
        
        # Apply the current theme to this dialog
        self._apply_theme(self.settings.get("theme", "dark"))

    def _load_settings(self) -> dict:
        """Load settings from the configuration file.""" 
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        # Return defaults if file doesn't exist or is corrupted
        return {
            "theme": "dark",
            "profile_dir": DEFAULT_PROFILE_DIR,
            "icon_dir": DEFAULT_ICON_DIR,
            "check_for_updates": False
        }

    def _save_settings(self):
        """Save current settings to the configuration file."""
        # Update self.settings from UI elements before saving
        # Appearance Tab
        if self.light_theme_radio.isChecked():
            self.settings["theme"] = "light"
        else:
            self.settings["theme"] = "dark"
        
        # Behavior Tab
        self.settings["profile_dir"] = self.profile_dir_edit.text()
        self.settings["icon_dir"] = self.icon_dir_edit.text()

        try:
            # Ensure directories exist if specified
            if not os.path.exists(self.settings["profile_dir"]):
                os.makedirs(self.settings["profile_dir"], exist_ok=True)
            if not os.path.exists(self.settings["icon_dir"]):
                os.makedirs(self.settings["icon_dir"], exist_ok=True)

            with open(CONFIG_FILE, "w") as f:
                json.dump(self.settings, f, indent=4)
            print("Settings saved.")
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def _create_appearance_tab(self):
        appearance_widget = QWidget()
        layout = QVBoxLayout(appearance_widget)

        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        self.theme_button_group = QButtonGroup(self)
        self.light_theme_radio = QRadioButton("Light Mode")
        self.dark_theme_radio = QRadioButton("Dark Mode")
        self.theme_button_group.addButton(self.light_theme_radio)
        self.theme_button_group.addButton(self.dark_theme_radio)
        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        theme_group.setLayout(theme_layout)

        if self.settings.get("theme", "dark") == "light":
            self.light_theme_radio.setChecked(True)
        else:
            self.dark_theme_radio.setChecked(True)
            
        # Connect theme change to live preview
        self.light_theme_radio.toggled.connect(self._on_theme_toggled)
        self.dark_theme_radio.toggled.connect(self._on_theme_toggled)

        layout.addWidget(theme_group)
        layout.addStretch()

        self.tab_widget.addTab(appearance_widget, "Appearance")

    def _create_behavior_tab(self):
        behavior_widget = QWidget()
        layout = QVBoxLayout(behavior_widget)
        form_layout = QFormLayout()

        # Profile Directory
        self.profile_dir_edit = QLineEdit(self.settings.get("profile_dir", DEFAULT_PROFILE_DIR))
        browse_profile_dir_button = QPushButton("Browse...")
        browse_profile_dir_button.clicked.connect(lambda: self._browse_directory(self.profile_dir_edit))
        profile_dir_layout = QHBoxLayout()
        profile_dir_layout.addWidget(self.profile_dir_edit)
        profile_dir_layout.addWidget(browse_profile_dir_button)
        form_layout.addRow("Default Profile Directory:", profile_dir_layout)

        # Icon Directory
        self.icon_dir_edit = QLineEdit(self.settings.get("icon_dir", DEFAULT_ICON_DIR))
        browse_icon_dir_button = QPushButton("Browse...")
        browse_icon_dir_button.clicked.connect(lambda: self._browse_directory(self.icon_dir_edit))
        icon_dir_layout = QHBoxLayout()
        icon_dir_layout.addWidget(self.icon_dir_edit)
        icon_dir_layout.addWidget(browse_icon_dir_button)
        form_layout.addRow("Default Icon Directory:", icon_dir_layout)
        
        layout.addLayout(form_layout)
        layout.addStretch()

        self.tab_widget.addTab(behavior_widget, "Paths")

    def _create_about_help_tab(self):
        about_widget = QWidget()
        layout = QVBoxLayout(about_widget)
        
        # Application info
        app_info_group = QGroupBox("Application Information")
        app_info_layout = QVBoxLayout()
        app_info_layout.addWidget(QLabel("VPN Automation Application"))
        app_info_layout.addWidget(QLabel("Version: 1.0.0"))
        app_info_layout.addWidget(QLabel("© 2025 All Rights Reserved"))
        app_info_group.setLayout(app_info_layout)
        
        # Help info
        help_group = QGroupBox("Help")
        help_layout = QVBoxLayout()
        help_layout.addWidget(QLabel("For assistance, please contact support."))
        help_layout.addWidget(QLabel("Email: support@example.com"))
        help_group.setLayout(help_layout)
        
        layout.addWidget(app_info_group)
        layout.addWidget(help_group)
        layout.addStretch()
        
        self.tab_widget.addTab(about_widget, "About / Help")

    def _browse_directory(self, line_edit_widget: QLineEdit):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", line_edit_widget.text())
        if directory:
            line_edit_widget.setText(directory)

    def _on_theme_toggled(self):
        """Live preview of theme changes"""
        theme = "light" if self.light_theme_radio.isChecked() else "dark"
        self._apply_theme(theme)

    def _apply_theme(self, theme):
        """Apply the selected theme to this dialog and all child widgets"""
        if theme == "light":
            # Set palette for light theme
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor("#f0f0f0"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#e0e0e0"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#e0e0e0"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#000000"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#0057ae"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#308cc6"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            
            # Apply palette to this dialog
            self.setPalette(palette)
            
            # Apply stylesheet for light theme
            self.setStyleSheet("""
                QDialog, QTabWidget, QWidget {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QTabWidget::pane {
                    border: 1px solid #c0c0c0;
                    background-color: #f0f0f0;
                }
                QTabBar::tab {
                    background-color: #e0e0e0;
                    color: #000000;
                    padding: 8px 12px;
                    border: 1px solid #c0c0c0;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #f0f0f0;
                    border-bottom: 1px solid #f0f0f0;
                }
                QGroupBox {
                    background-color: #f0f0f0;
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                    margin-top: 1ex;
                    padding-top: 10px;
                    color: #000000;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 3px;
                    color: #000000;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                    padding: 6px 12px;
                    color: #000000;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QPushButton:pressed {
                    background-color: #c0c0c0;
                }
                QLineEdit {
                    background-color: #ffffff;
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                    padding: 4px;
                    color: #000000;
                }
                QRadioButton {
                    color: #000000;
                    background-color: transparent;
                }
                QLabel {
                    color: #000000;
                    background-color: transparent;
                }
                QFormLayout {
                    background-color: #f0f0f0;
                }
            """)
            
            # Force update for all child widgets
            for tab_index in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(tab_index)
                tab.setStyleSheet("background-color: #f0f0f0; color: #000000;")
                
                # Update all child widgets recursively
                self._update_widget_theme(tab, theme)
                
        else:  # dark theme
            # Set palette for dark theme
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor("#2d2d2d"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#3d3d3d"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#444444"))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2d2d2d"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#3d3d3d"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.Link, QColor("#4c9be8"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#308cc6"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            
            # Apply palette to this dialog
            self.setPalette(palette)
            
            # Apply stylesheet for dark theme
            self.setStyleSheet("""
                QDialog, QTabWidget, QWidget {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #444444;
                    background-color: #2d2d2d;
                }
                QTabBar::tab {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    padding: 8px 12px;
                    border: 1px solid #444444;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #2d2d2d;
                    border-bottom: 1px solid #2d2d2d;
                }
                QGroupBox {
                    background-color: #2d2d2d;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    margin-top: 1ex;
                    padding-top: 10px;
                    color: #ffffff;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 3px;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3d3d3d;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    padding: 6px 12px;
                    color: #ffffff;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
                QPushButton:pressed {
                    background-color: #5d5d5d;
                }
                QLineEdit {
                    background-color: #3d3d3d;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    padding: 4px;
                    color: #ffffff;
                }
                QRadioButton {
                    color: #ffffff;
                    background-color: transparent;
                }
                QLabel {
                    color: #ffffff;
                    background-color: transparent;
                }
                QFormLayout {
                    background-color: #2d2d2d;
                }
            """)
            
            # Force update for all child widgets
            for tab_index in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(tab_index)
                tab.setStyleSheet("background-color: #2d2d2d; color: #ffffff;")
                
                # Update all child widgets recursively
                self._update_widget_theme(tab, theme)

    def _update_widget_theme(self, widget, theme):
        """Recursively update theme for all child widgets"""
        # Apply theme to all child widgets
        for child in widget.findChildren(QWidget):
            if theme == "light":
                if isinstance(child, QGroupBox):
                    child.setStyleSheet("background-color: #f0f0f0; color: #000000; border: 1px solid #c0c0c0;")
                elif isinstance(child, QPushButton):
                    child.setStyleSheet("background-color: #e0e0e0; color: #000000; border: 1px solid #c0c0c0;")
                elif isinstance(child, QLineEdit):
                    child.setStyleSheet("background-color: #ffffff; color: #000000; border: 1px solid #c0c0c0;")
                elif isinstance(child, QRadioButton) or isinstance(child, QLabel):
                    child.setStyleSheet("color: #000000; background-color: transparent;")
                else:
                    child.setStyleSheet("background-color: #f0f0f0; color: #000000;")
            else:  # dark theme
                if isinstance(child, QGroupBox):
                    child.setStyleSheet("background-color: #2d2d2d; color: #ffffff; border: 1px solid #444444;")
                elif isinstance(child, QPushButton):
                    child.setStyleSheet("background-color: #3d3d3d; color: #ffffff; border: 1px solid #444444;")
                elif isinstance(child, QLineEdit):
                    child.setStyleSheet("background-color: #3d3d3d; color: #ffffff; border: 1px solid #444444;")
                elif isinstance(child, QRadioButton) or isinstance(child, QLabel):
                    child.setStyleSheet("color: #ffffff; background-color: transparent;")
                else:
                    child.setStyleSheet("background-color: #2d2d2d; color: #ffffff;")

    def _save_and_accept(self):
        if self._save_settings():
            # Apply theme to parent window if available
            if self.parent() and hasattr(self.parent(), "_set_theme"):
                self.parent()._set_theme(self.settings["theme"])
            self.accept()

    def get_settings(self) -> dict:
        """Return the current settings dictionary."""
        # Ensure settings are up-to-date from UI before returning
        current_theme = "light" if self.light_theme_radio.isChecked() else "dark"
        return {
            "theme": current_theme,
            "profile_dir": self.profile_dir_edit.text(),
            "icon_dir": self.icon_dir_edit.text(),
        }

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = SettingsDialog()
    if dialog.exec():
        print("Settings Dialog Accepted. Current settings:", dialog.get_settings())
    else:
        print("Settings Dialog Cancelled.")
    sys.exit(app.exec())
