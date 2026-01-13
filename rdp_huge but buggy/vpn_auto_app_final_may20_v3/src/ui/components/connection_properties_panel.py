import os
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout,
    QPushButton, QTabWidget, QSpinBox, QCheckBox, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap

class ConnectionPropertiesPanel(QWidget):
    """Side panel for viewing and editing connection properties without dialogs."""
    
    property_changed = pyqtSignal(str, str, object)  # property_name, connection_id, new_value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_connection = None
        self.inherited_properties = set()  # Track which properties are inherited
        
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        self.header_label = QLabel("Connection Properties")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.header_label)
        
        # Tabs for different property categories
        self.tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Connection name")
        self.name_edit.editingFinished.connect(lambda: self._emit_property_change("name", self.name_edit.text()))
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description")
        self.description_edit.editingFinished.connect(lambda: self._emit_property_change("description", self.description_edit.text()))
        
        general_layout.addRow(self._create_property_label("Name:"), self.name_edit)
        general_layout.addRow(self._create_property_label("Description:"), self.description_edit)
        
        # VPN tab
        vpn_tab = QWidget()
        vpn_layout = QFormLayout(vpn_tab)
        
        self.vpn_type_combo = QComboBox()
        self.vpn_type_combo.addItems(["forticlient", "globalprotect", "custom"])
        self.vpn_type_combo.currentTextChanged.connect(lambda text: self._emit_property_change("vpn_type", text))
        
        self.vpn_server_edit = QLineEdit()
        self.vpn_server_edit.setPlaceholderText("VPN server address")
        self.vpn_server_edit.editingFinished.connect(lambda: self._emit_property_change("vpn_server", self.vpn_server_edit.text()))
        
        self.vpn_username_edit = QLineEdit()
        self.vpn_username_edit.setPlaceholderText("VPN username")
        self.vpn_username_edit.editingFinished.connect(lambda: self._emit_property_change("vpn_username", self.vpn_username_edit.text()))
        
        vpn_layout.addRow(self._create_property_label("VPN Type:"), self.vpn_type_combo)
        vpn_layout.addRow(self._create_property_label("Server:"), self.vpn_server_edit)
        vpn_layout.addRow(self._create_property_label("Username:"), self.vpn_username_edit)
        
        # RDP tab
        rdp_tab = QWidget()
        rdp_layout = QFormLayout(rdp_tab)
        
        self.rdp_hostname_edit = QLineEdit()
        self.rdp_hostname_edit.setPlaceholderText("RDP hostname/IP")
        self.rdp_hostname_edit.editingFinished.connect(lambda: self._emit_property_change("rdp_hostname", self.rdp_hostname_edit.text()))
        
        self.rdp_port_spin = QSpinBox()
        self.rdp_port_spin.setRange(1, 65535)
        self.rdp_port_spin.setValue(3389)
        self.rdp_port_spin.valueChanged.connect(lambda value: self._emit_property_change("rdp_port", value))
        
        self.rdp_username_edit = QLineEdit()
        self.rdp_username_edit.setPlaceholderText("RDP username")
        self.rdp_username_edit.editingFinished.connect(lambda: self._emit_property_change("rdp_username", self.rdp_username_edit.text()))
        
        self.rdp_password_edit = QLineEdit()
        self.rdp_password_edit.setPlaceholderText("RDP password")
        self.rdp_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.rdp_password_edit.editingFinished.connect(lambda: self._emit_property_change("rdp_password", self.rdp_password_edit.text()))
        
        rdp_layout.addRow(self._create_property_label("Hostname:"), self.rdp_hostname_edit)
        rdp_layout.addRow(self._create_property_label("Port:"), self.rdp_port_spin)
        rdp_layout.addRow(self._create_property_label("Username:"), self.rdp_username_edit)
        rdp_layout.addRow(self._create_property_label("Password:"), self.rdp_password_edit)
        
        # Add tabs
        self.tabs.addTab(general_tab, "General")
        self.tabs.addTab(vpn_tab, "VPN")
        self.tabs.addTab(rdp_tab, "RDP")
        
        main_layout.addWidget(self.tabs)
        
        # Inheritance controls
        inheritance_group = QGroupBox("Inheritance")
        inheritance_layout = QVBoxLayout(inheritance_group)
        
        self.inherit_checkbox = QCheckBox("Inherit properties from parent")
        self.inherit_checkbox.toggled.connect(self._toggle_inheritance)
        inheritance_layout.addWidget(self.inherit_checkbox)
        
        self.override_button = QPushButton("Override Selected Property")
        self.override_button.clicked.connect(self._override_selected_property)
        inheritance_layout.addWidget(self.override_button)
        
        main_layout.addWidget(inheritance_group)
        
        # Apply button
        self.apply_button = QPushButton("Apply Changes")
        self.apply_button.clicked.connect(self._apply_changes)
        main_layout.addWidget(self.apply_button)
        
        # Initially disable all controls
        self._set_controls_enabled(False)
        
    def _create_property_label(self, text):
        """Create a label for a property that can show inheritance status."""
        label = QLabel(text)
        return label
        
    def _set_controls_enabled(self, enabled):
        """Enable or disable all property controls."""
        self.name_edit.setEnabled(enabled)
        self.description_edit.setEnabled(enabled)
        self.vpn_type_combo.setEnabled(enabled)
        self.vpn_server_edit.setEnabled(enabled)
        self.vpn_username_edit.setEnabled(enabled)
        self.rdp_hostname_edit.setEnabled(enabled)
        self.rdp_port_spin.setEnabled(enabled)
        self.rdp_username_edit.setEnabled(enabled)
        self.rdp_password_edit.setEnabled(enabled)
        self.inherit_checkbox.setEnabled(enabled)
        self.override_button.setEnabled(enabled)
        self.apply_button.setEnabled(enabled)
        
    def _toggle_inheritance(self, checked):
        """Toggle inheritance of properties from parent."""
        if not self.current_connection:
            return
            
        # In a real implementation, this would update the connection's inheritance settings
        # and refresh the display to show inherited properties
        
    def _override_selected_property(self):
        """Override the currently selected property with a custom value."""
        # In a real implementation, this would determine which property is selected
        # and remove it from the inherited properties set
        
    def _apply_changes(self):
        """Apply all changes to the connection."""
        # In a real implementation, this would save all changes to the connection
        
    def _emit_property_change(self, property_name, value):
        """Emit a signal when a property is changed."""
        if self.current_connection:
            self.property_changed.emit(property_name, self.current_connection.get("id", ""), value)
            
    def set_connection(self, connection_data):
        """Set the connection to display/edit."""
        self.current_connection = connection_data
        
        if connection_data:
            self._set_controls_enabled(True)
            self._populate_fields(connection_data)
            self.header_label.setText(f"Connection Properties: {connection_data.get('name', 'Unnamed')}")
        else:
            self._set_controls_enabled(False)
            self._clear_fields()
            self.header_label.setText("Connection Properties")
            
    def _populate_fields(self, connection_data):
        """Populate fields with connection data."""
        # General tab
        self.name_edit.setText(connection_data.get("name", ""))
        self.description_edit.setText(connection_data.get("description", ""))
        
        # VPN tab
        vpn_config = connection_data.get("config", {}).get("vpn_params", {})
        self.vpn_type_combo.setCurrentText(connection_data.get("type", "custom"))
        self.vpn_server_edit.setText(vpn_config.get("server", ""))
        self.vpn_username_edit.setText(vpn_config.get("username", ""))
        
        # RDP tab
        rdp_config = connection_data.get("config", {}).get("remote_access", {}).get("rdp_details", {})
        self.rdp_hostname_edit.setText(rdp_config.get("hostname", ""))
        self.rdp_port_spin.setValue(rdp_config.get("port", 3389))
        self.rdp_username_edit.setText(rdp_config.get("username", ""))
        self.rdp_password_edit.setText(rdp_config.get("password", ""))
        
        # Inheritance
        self.inherit_checkbox.setChecked(connection_data.get("inherit_from_parent", False))
        
        # Mark inherited properties
        self.inherited_properties = set(connection_data.get("inherited_properties", []))
        self._update_inheritance_indicators()
        
    def _clear_fields(self):
        """Clear all fields."""
        # General tab
        self.name_edit.clear()
        self.description_edit.clear()
        
        # VPN tab
        self.vpn_type_combo.setCurrentIndex(0)
        self.vpn_server_edit.clear()
        self.vpn_username_edit.clear()
        
        # RDP tab
        self.rdp_hostname_edit.clear()
        self.rdp_port_spin.setValue(3389)
        self.rdp_username_edit.clear()
        self.rdp_password_edit.clear()
        
        # Inheritance
        self.inherit_checkbox.setChecked(False)
        self.inherited_properties.clear()
        
    def _update_inheritance_indicators(self):
        """Update visual indicators for inherited properties."""
        # In a real implementation, this would style the labels of inherited properties
        # to indicate they are inherited from a parent
        pass
