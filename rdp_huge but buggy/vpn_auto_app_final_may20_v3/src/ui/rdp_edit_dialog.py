import os
import shutil
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QFormLayout, QMessageBox, QFileDialog, QSpinBox, QCheckBox, QTabWidget,
    QGroupBox, QComboBox, QGridLayout, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap

# Define ICON_SIZE and a fallback for icon storage directory, similar to other dialogs
ICON_SIZE = QSize(24, 24)
DEFAULT_ICON_STORAGE_DIR = os.path.join(os.path.expanduser("~"), ".vpn_auto_app_icons", "rdp_icons")
if not os.path.exists(DEFAULT_ICON_STORAGE_DIR):
    os.makedirs(DEFAULT_ICON_STORAGE_DIR, exist_ok=True)

class RDPEditDialog(QDialog):
    """Dialog for adding or editing standalone RDP profiles with advanced authentication options."""
    def __init__(self, parent=None, profile_data: Optional[Dict[str, Any]] = None, icon_storage_dir: str = DEFAULT_ICON_STORAGE_DIR):
        super().__init__(parent)
        self.setWindowTitle("Edit RDP Profile" if profile_data else "Add RDP Profile")
        self.setMinimumWidth(550)
        self.setMinimumHeight(500)
        self.icon_storage_dir = icon_storage_dir
        if not os.path.exists(self.icon_storage_dir):
            os.makedirs(self.icon_storage_dir, exist_ok=True)

        self.profile_data = profile_data.copy() if profile_data else {}
        # Ensure all expected keys exist, even if empty, for new profiles
        self.profile_data.setdefault("name", "")
        self.profile_data.setdefault("hostname", "")
        self.profile_data.setdefault("port", 3389)
        self.profile_data.setdefault("username", "")
        self.profile_data.setdefault("domain", "")
        self.profile_data.setdefault("icon_path", None)
        # Password is stored securely and can be pre-filled for editing
        self.profile_data.setdefault("password", "")
        
        # Advanced settings with defaults
        self.profile_data.setdefault("fullscreen", True)
        self.profile_data.setdefault("admin_console", False)
        self.profile_data.setdefault("width", 1024)
        self.profile_data.setdefault("height", 768)
        self.profile_data.setdefault("use_gateway", False)
        self.profile_data.setdefault("gateway_hostname", "")
        self.profile_data.setdefault("gateway_username", "")
        self.profile_data.setdefault("gateway_password", "")
        self.profile_data.setdefault("gateway_domain", "")
        self.profile_data.setdefault("auth_method", "default")  # default, credssp, smartcard
        self.profile_data.setdefault("save_credentials", False)
        self.profile_data.setdefault("use_windows_cred_manager", True)
        self.profile_data.setdefault("redirect_drives", True)
        self.profile_data.setdefault("redirect_printers", True)
        self.profile_data.setdefault("redirect_clipboard", True)
        self.profile_data.setdefault("redirect_smartcards", False)
        self.profile_data.setdefault("redirect_audio", True)

        # Create tab widget for basic and advanced settings
        self.tab_widget = QTabWidget(self)
        
        # Basic settings tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # Basic connection form
        form_layout = QFormLayout()

        self.profile_name_edit = QLineEdit(self.profile_data["name"])
        form_layout.addRow("Profile Name:", self.profile_name_edit)

        self.hostname_edit = QLineEdit(self.profile_data["hostname"])
        form_layout.addRow("Hostname/IP:", self.hostname_edit)

        self.port_spinbox = QSpinBox()
        self.port_spinbox.setRange(1, 65535)
        self.port_spinbox.setValue(self.profile_data["port"])
        form_layout.addRow("Port:", self.port_spinbox)

        self.username_edit = QLineEdit(self.profile_data["username"])
        form_layout.addRow("Username (Optional):", self.username_edit)
        
        self.password_edit = QLineEdit(self.profile_data.get("password", ""))
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password (Optional):", self.password_edit)
        
        self.domain_edit = QLineEdit(self.profile_data["domain"])
        form_layout.addRow("Domain (Optional):", self.domain_edit)

        # Credential storage options
        cred_group = QGroupBox("Credential Storage")
        cred_layout = QVBoxLayout(cred_group)
        
        self.save_creds_checkbox = QCheckBox("Save credentials for this connection")
        self.save_creds_checkbox.setChecked(self.profile_data["save_credentials"])
        cred_layout.addWidget(self.save_creds_checkbox)
        
        self.use_win_cred_checkbox = QCheckBox("Use Windows Credential Manager (recommended)")
        self.use_win_cred_checkbox.setChecked(self.profile_data["use_windows_cred_manager"])
        cred_layout.addWidget(self.use_win_cred_checkbox)
        
        # Icon selection
        icon_layout = QHBoxLayout()
        self.icon_preview_label = QLabel()
        self.icon_preview_label.setFixedSize(ICON_SIZE)
        self.icon_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_preview_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.select_icon_button = QPushButton("Select Icon")
        self.select_icon_button.clicked.connect(self._select_icon)
        self.clear_icon_button = QPushButton("Clear Icon")
        self.clear_icon_button.clicked.connect(self._clear_icon)
        icon_layout.addWidget(self.icon_preview_label)
        icon_layout.addWidget(self.select_icon_button)
        icon_layout.addWidget(self.clear_icon_button)
        form_layout.addRow("Profile Icon:", icon_layout)
        self._update_icon_preview(self.profile_data["icon_path"])

        basic_layout.addLayout(form_layout)
        basic_layout.addWidget(cred_group)
        basic_layout.addStretch()
        
        # Advanced settings tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # Display settings
        display_group = QGroupBox("Display Settings")
        display_layout = QVBoxLayout(display_group)
        
        self.fullscreen_checkbox = QCheckBox("Connect in fullscreen mode")
        self.fullscreen_checkbox.setChecked(self.profile_data["fullscreen"])
        display_layout.addWidget(self.fullscreen_checkbox)
        
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Window size:"))
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(640, 4096)
        self.width_spinbox.setValue(self.profile_data["width"])
        resolution_layout.addWidget(self.width_spinbox)
        resolution_layout.addWidget(QLabel("×"))
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(480, 2160)
        self.height_spinbox.setValue(self.profile_data["height"])
        resolution_layout.addWidget(self.height_spinbox)
        resolution_layout.addStretch()
        display_layout.addLayout(resolution_layout)
        
        self.admin_console_checkbox = QCheckBox("Connect to admin console")
        self.admin_console_checkbox.setChecked(self.profile_data["admin_console"])
        display_layout.addWidget(self.admin_console_checkbox)
        
        # Authentication settings
        auth_group = QGroupBox("Authentication Settings")
        auth_layout = QVBoxLayout(auth_group)
        
        auth_method_layout = QHBoxLayout()
        auth_method_layout.addWidget(QLabel("Authentication method:"))
        self.auth_method_combo = QComboBox()
        self.auth_method_combo.addItem("Default", "default")
        self.auth_method_combo.addItem("CredSSP (Network Level Authentication)", "credssp")
        self.auth_method_combo.addItem("Smart Card", "smartcard")
        
        # Set current auth method
        index = self.auth_method_combo.findData(self.profile_data["auth_method"])
        if index >= 0:
            self.auth_method_combo.setCurrentIndex(index)
        
        auth_method_layout.addWidget(self.auth_method_combo)
        auth_layout.addLayout(auth_method_layout)
        
        # RD Gateway settings
        gateway_group = QGroupBox("Remote Desktop Gateway")
        gateway_layout = QVBoxLayout(gateway_group)
        
        self.use_gateway_checkbox = QCheckBox("Use RD Gateway server")
        self.use_gateway_checkbox.setChecked(self.profile_data["use_gateway"])
        self.use_gateway_checkbox.toggled.connect(self._toggle_gateway_fields)
        gateway_layout.addWidget(self.use_gateway_checkbox)
        
        gateway_form = QFormLayout()
        self.gateway_hostname_edit = QLineEdit(self.profile_data["gateway_hostname"])
        gateway_form.addRow("Gateway server:", self.gateway_hostname_edit)
        
        self.gateway_username_edit = QLineEdit(self.profile_data["gateway_username"])
        gateway_form.addRow("Username:", self.gateway_username_edit)
        
        self.gateway_password_edit = QLineEdit(self.profile_data["gateway_password"])
        self.gateway_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        gateway_form.addRow("Password:", self.gateway_password_edit)
        
        self.gateway_domain_edit = QLineEdit(self.profile_data["gateway_domain"])
        gateway_form.addRow("Domain:", self.gateway_domain_edit)
        
        gateway_layout.addLayout(gateway_form)
        
        # Redirection settings
        redirect_group = QGroupBox("Local Resources")
        redirect_layout = QGridLayout(redirect_group)
        
        self.redirect_drives_checkbox = QCheckBox("Redirect drives")
        self.redirect_drives_checkbox.setChecked(self.profile_data["redirect_drives"])
        redirect_layout.addWidget(self.redirect_drives_checkbox, 0, 0)
        
        self.redirect_printers_checkbox = QCheckBox("Redirect printers")
        self.redirect_printers_checkbox.setChecked(self.profile_data["redirect_printers"])
        redirect_layout.addWidget(self.redirect_printers_checkbox, 0, 1)
        
        self.redirect_clipboard_checkbox = QCheckBox("Redirect clipboard")
        self.redirect_clipboard_checkbox.setChecked(self.profile_data["redirect_clipboard"])
        redirect_layout.addWidget(self.redirect_clipboard_checkbox, 1, 0)
        
        self.redirect_smartcards_checkbox = QCheckBox("Redirect smart cards")
        self.redirect_smartcards_checkbox.setChecked(self.profile_data["redirect_smartcards"])
        redirect_layout.addWidget(self.redirect_smartcards_checkbox, 1, 1)
        
        self.redirect_audio_checkbox = QCheckBox("Redirect audio")
        self.redirect_audio_checkbox.setChecked(self.profile_data["redirect_audio"])
        redirect_layout.addWidget(self.redirect_audio_checkbox, 2, 0)
        
        # Add all groups to advanced tab
        advanced_layout.addWidget(display_group)
        advanced_layout.addWidget(auth_group)
        advanced_layout.addWidget(gateway_group)
        advanced_layout.addWidget(redirect_group)
        advanced_layout.addStretch()
        
        # Initialize gateway fields state
        self._toggle_gateway_fields(self.profile_data["use_gateway"])
        
        # Add tabs to tab widget
        self.tab_widget.addTab(basic_tab, "Basic Settings")
        self.tab_widget.addTab(advanced_tab, "Advanced Settings")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def _toggle_gateway_fields(self, enabled):
        """Enable or disable gateway fields based on checkbox state."""
        self.gateway_hostname_edit.setEnabled(enabled)
        self.gateway_username_edit.setEnabled(enabled)
        self.gateway_password_edit.setEnabled(enabled)
        self.gateway_domain_edit.setEnabled(enabled)

    def _select_icon(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.ico)")
        if file_name:
            base_name = os.path.basename(file_name)
            # Ensure unique name if needed, or just copy
            target_path = os.path.join(self.icon_storage_dir, base_name)
            try:
                shutil.copy(file_name, target_path)
                self.profile_data["icon_path"] = target_path
                self._update_icon_preview(target_path)
            except Exception as e:
                QMessageBox.warning(self, "Icon Error", f"Could not copy icon: {e}")
                self.profile_data["icon_path"] = None

    def _clear_icon(self):
        self.profile_data["icon_path"] = None
        self._update_icon_preview(None)

    def _update_icon_preview(self, icon_path: Optional[str]):
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            self.icon_preview_label.setPixmap(pixmap.scaled(ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.icon_preview_label.setText("No Icon")
            self.icon_preview_label.setPixmap(QPixmap()) # Clear pixmap

    def get_profile_data(self) -> Dict[str, Any]:
        """Returns the edited profile data."""
        # Basic settings
        self.profile_data["name"] = self.profile_name_edit.text().strip()
        self.profile_data["hostname"] = self.hostname_edit.text().strip()
        self.profile_data["port"] = self.port_spinbox.value()
        self.profile_data["username"] = self.username_edit.text().strip()
        self.profile_data["password"] = self.password_edit.text()
        self.profile_data["domain"] = self.domain_edit.text().strip()
        # self.profile_data["icon_path"] is updated by _select_icon/_clear_icon
        
        # Credential storage
        self.profile_data["save_credentials"] = self.save_creds_checkbox.isChecked()
        self.profile_data["use_windows_cred_manager"] = self.use_win_cred_checkbox.isChecked()
        
        # Display settings
        self.profile_data["fullscreen"] = self.fullscreen_checkbox.isChecked()
        self.profile_data["width"] = self.width_spinbox.value()
        self.profile_data["height"] = self.height_spinbox.value()
        self.profile_data["admin_console"] = self.admin_console_checkbox.isChecked()
        
        # Authentication settings
        self.profile_data["auth_method"] = self.auth_method_combo.currentData()
        
        # Gateway settings
        self.profile_data["use_gateway"] = self.use_gateway_checkbox.isChecked()
        self.profile_data["gateway_hostname"] = self.gateway_hostname_edit.text().strip()
        self.profile_data["gateway_username"] = self.gateway_username_edit.text().strip()
        self.profile_data["gateway_password"] = self.gateway_password_edit.text()
        self.profile_data["gateway_domain"] = self.gateway_domain_edit.text().strip()
        
        # Redirection settings
        self.profile_data["redirect_drives"] = self.redirect_drives_checkbox.isChecked()
        self.profile_data["redirect_printers"] = self.redirect_printers_checkbox.isChecked()
        self.profile_data["redirect_clipboard"] = self.redirect_clipboard_checkbox.isChecked()
        self.profile_data["redirect_smartcards"] = self.redirect_smartcards_checkbox.isChecked()
        self.profile_data["redirect_audio"] = self.redirect_audio_checkbox.isChecked()
        
        return self.profile_data

    def accept(self):
        profile_name = self.profile_name_edit.text().strip()
        hostname = self.hostname_edit.text().strip()
        
        # Basic validation
        if not profile_name:
            QMessageBox.warning(self, "Validation Error", "Profile name is required.")
            self.profile_name_edit.setFocus()
            return
            
        if not hostname:
            QMessageBox.warning(self, "Validation Error", "Hostname/IP is required.")
            self.hostname_edit.setFocus()
            return
            
        # Gateway validation if enabled
        if self.use_gateway_checkbox.isChecked() and not self.gateway_hostname_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Gateway server is required when using RD Gateway.")
            self.gateway_hostname_edit.setFocus()
            return
            
        super().accept()
