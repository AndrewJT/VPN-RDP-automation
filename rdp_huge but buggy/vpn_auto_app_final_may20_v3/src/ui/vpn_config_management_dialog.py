import sys
import os
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QListWidgetItem, QSplitter, QWidget, QLabel, 
    QMessageBox, QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QTabWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

# Import VPNProfileEditDialog from its own module instead of main_window
try:
    from .vpn_profile_edit_dialog import VPNProfileEditDialog
except ImportError as e:
    print(f"Warning: Could not import VPNProfileEditDialog: {e}. Using placeholder.")
    class VPNProfileEditDialog(QDialog):
        def __init__(self, parent=None, profile_data=None, vpn_manager_instance=None, model_manager_instance=None, icon_storage_dir=None):
            super().__init__(parent)
            self.setWindowTitle("VPN Profile Editor (Unavailable)")
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("VPN Profile Editor is not available due to import errors."))
            self.ok_button = QPushButton("OK")
            self.ok_button.clicked.connect(self.accept)
            layout.addWidget(self.ok_button)
        def get_data(self) -> Optional[Dict[str, Any]]: return None

class VPNConfigManagementDialog(QDialog):
    """A comprehensive dialog for managing VPN profiles."""
    
    def __init__(self, vpn_manager, model_manager=None, icon_dir=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VPN Configuration Management")
        self.setMinimumSize(800, 600)
        
        self.vpn_manager = vpn_manager
        self.model_manager = model_manager
        self.icon_dir = icon_dir or os.path.join(os.path.expanduser("~"), ".vpn_auto_app_icons")
        
        # Ensure icon directory exists
        if not os.path.exists(self.icon_dir):
            os.makedirs(self.icon_dir, exist_ok=True)
        
        self.current_profile = None
        
        main_layout = QVBoxLayout(self)
        
        # Splitter for list and details
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Left side: Profile list with search
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search box (placeholder for future enhancement)
        # self.search_edit = QLineEdit()
        # self.search_edit.setPlaceholderText("Search profiles...")
        # self.search_edit.textChanged.connect(self._filter_profiles)
        # left_layout.addWidget(self.search_edit)
        
        # Profile list
        self.profile_list = QListWidget()
        self.profile_list.setIconSize(QSize(24, 24))
        self.profile_list.itemSelectionChanged.connect(self._on_profile_selected)
        left_layout.addWidget(QLabel("<b>VPN Profiles:</b>"))
        left_layout.addWidget(self.profile_list)
        
        # List controls
        list_controls_layout = QHBoxLayout()
        self.new_profile_button = QPushButton("New Profile...")
        self.edit_profile_button = QPushButton("Edit Profile...")
        self.delete_profile_button = QPushButton("Delete Profile")
        self.duplicate_profile_button = QPushButton("Duplicate Profile...")
        
        self.new_profile_button.clicked.connect(self._new_profile)
        self.edit_profile_button.clicked.connect(self._edit_profile)
        self.delete_profile_button.clicked.connect(self._delete_profile)
        self.duplicate_profile_button.clicked.connect(self._duplicate_profile)
        
        list_controls_layout.addWidget(self.new_profile_button)
        list_controls_layout.addWidget(self.edit_profile_button)
        list_controls_layout.addWidget(self.delete_profile_button)
        list_controls_layout.addWidget(self.duplicate_profile_button)
        left_layout.addLayout(list_controls_layout)
        
        # Right side: Profile details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Profile details view
        self.details_tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        self.profile_name_label = QLabel("")
        self.profile_type_label = QLabel("")
        self.profile_icon_label = QLabel("")
        self.profile_icon_label.setFixedSize(QSize(32, 32))
        self.profile_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.profile_icon_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        
        general_layout.addRow("<b>Profile Name:</b>", self.profile_name_label)
        general_layout.addRow("<b>VPN Type:</b>", self.profile_type_label)
        general_layout.addRow("<b>Icon:</b>", self.profile_icon_label)
        
        # VPN Connection tab
        vpn_tab = QWidget()
        vpn_layout = QFormLayout(vpn_tab)
        
        self.vpn_server_label = QLabel("")
        self.vpn_username_label = QLabel("")
        self.vpn_group_label = QLabel("")
        self.vpn_model_label = QLabel("")
        
        vpn_layout.addRow("<b>Server:</b>", self.vpn_server_label)
        vpn_layout.addRow("<b>Username:</b>", self.vpn_username_label)
        vpn_layout.addRow("<b>Group:</b>", self.vpn_group_label)
        vpn_layout.addRow("<b>VPN Model:</b>", self.vpn_model_label)
        
        # Model-specific parameters group
        self.model_params_group = QGroupBox("Model-Specific Parameters")
        self.model_params_layout = QFormLayout(self.model_params_group)
        vpn_layout.addRow(self.model_params_group)
        self.model_params_group.setVisible(False)
        
        # Automation tab
        automation_tab = QWidget()
        automation_layout = QVBoxLayout(automation_tab)
        
        self.automation_summary_label = QLabel("No automation sequence configured.")
        automation_layout.addWidget(self.automation_summary_label)
        
        # Placeholder for future enhancement: automation sequence visualization
        self.automation_details = QTextEdit()
        self.automation_details.setReadOnly(True)
        self.automation_details.setPlaceholderText("Automation sequence details will be shown here.")
        automation_layout.addWidget(self.automation_details)
        
        # Remote Access tab
        remote_tab = QWidget()
        remote_layout = QFormLayout(remote_tab)
        
        self.ra_type_label = QLabel("")
        self.ra_hostname_label = QLabel("")
        self.ra_username_label = QLabel("")
        self.ra_url_label = QLabel("")
        
        remote_layout.addRow("<b>Remote Access Type:</b>", self.ra_type_label)
        remote_layout.addRow("<b>RDP Hostname:</b>", self.ra_hostname_label)
        remote_layout.addRow("<b>RDP Username:</b>", self.ra_username_label)
        remote_layout.addRow("<b>Browser URL:</b>", self.ra_url_label)
        
        # Add tabs to tab widget
        self.details_tabs.addTab(general_tab, "General")
        self.details_tabs.addTab(vpn_tab, "VPN Connection")
        self.details_tabs.addTab(automation_tab, "Automation")
        self.details_tabs.addTab(remote_tab, "Remote Access")
        
        right_layout.addWidget(QLabel("<b>Profile Details:</b>"))
        right_layout.addWidget(self.details_tabs)
        
        # Add widgets to splitter
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([300, 500])
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)
        
        # Initial UI state
        self._load_profiles()
        self._update_ui_state()
    
    def _load_profiles(self):
        """Load profiles from VPN manager and populate the list."""
        self.profile_list.clear()
        
        if not self.vpn_manager:
            QMessageBox.warning(self, "Error", "VPN Manager not available. Cannot load profiles.")
            return
        
        try:
            # Get profiles from VPN manager
            profiles = self.vpn_manager.list_profiles() if hasattr(self.vpn_manager, "list_profiles") else []
            
            for profile in profiles:
                profile_name = profile.get("name", "Unnamed Profile")
                item = QListWidgetItem(profile_name)
                
                # Set icon if available
                icon_path = profile.get("config", {}).get("icon_path")
                if icon_path and os.path.exists(icon_path):
                    item.setIcon(QIcon(icon_path))
                
                # Store profile data
                item.setData(Qt.ItemDataRole.UserRole, profile)
                self.profile_list.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load profiles: {e}")
    
    def _on_profile_selected(self):
        """Handle profile selection change."""
        selected_items = self.profile_list.selectedItems()
        if selected_items:
            self.current_profile = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self._display_profile_details()
        else:
            self.current_profile = None
            self._clear_profile_details()
        
        self._update_ui_state()
    
    def _display_profile_details(self):
        """Display details of the selected profile."""
        if not self.current_profile:
            self._clear_profile_details()
            return
        
        # General tab
        self.profile_name_label.setText(self.current_profile.get("name", ""))
        self.profile_type_label.setText(self.current_profile.get("type", ""))
        
        # Icon
        icon_path = self.current_profile.get("config", {}).get("icon_path")
        if icon_path and os.path.exists(icon_path):
            self.profile_icon_label.setPixmap(QIcon(icon_path).pixmap(QSize(32, 32)))
        else:
            self.profile_icon_label.setText("No Icon")
            self.profile_icon_label.setPixmap(None)
        
        # VPN Connection tab
        vpn_params = self.current_profile.get("config", {}).get("vpn_params", {})
        self.vpn_server_label.setText(vpn_params.get("server", ""))
        self.vpn_username_label.setText(vpn_params.get("username", ""))
        self.vpn_group_label.setText(vpn_params.get("group", ""))
        
        # VPN Model
        model_id = self.current_profile.get("config", {}).get("selected_vpn_model_id")
        if model_id and self.model_manager:
            try:
                model = self.model_manager.load_model(model_id)
                if model:
                    self.vpn_model_label.setText(f"{model.model_name} ({model.model_id})")
                    
                    # Display model-specific parameters
                    self._display_model_params(model, vpn_params)
                else:
                    self.vpn_model_label.setText(f"Unknown Model ({model_id})")
                    self.model_params_group.setVisible(False)
            except Exception as e:
                self.vpn_model_label.setText(f"Error loading model: {e}")
                self.model_params_group.setVisible(False)
        else:
            self.vpn_model_label.setText("None")
            self.model_params_group.setVisible(False)
        
        # Automation tab
        automation_sequence = self.current_profile.get("config", {}).get("automation_sequence", [])
        mapped_sequence = self.current_profile.get("config", {}).get("mapped_automation_sequence", [])
        
        if model_id and mapped_sequence:
            self.automation_summary_label.setText(f"{len(mapped_sequence)} mapped automation steps configured.")
            self._display_automation_details(mapped_sequence)
        elif automation_sequence:
            self.automation_summary_label.setText(f"{len(automation_sequence)} automation steps configured.")
            self._display_automation_details(automation_sequence)
        else:
            self.automation_summary_label.setText("No automation sequence configured.")
            self.automation_details.clear()
        
        # Remote Access tab
        remote_access = self.current_profile.get("config", {}).get("remote_access", {})
        ra_type = remote_access.get("type", "None")
        self.ra_type_label.setText(ra_type)
        
        # Get RDP details if available
        rdp_details = remote_access.get("rdp_details", {})
        self.ra_hostname_label.setText(rdp_details.get("hostname", ""))
        self.ra_username_label.setText(rdp_details.get("username", ""))
        
        # Get browser details if available
        browser_details = remote_access.get("browser_details", {})
        self.ra_url_label.setText(browser_details.get("url", ""))
        
        # Show/hide fields based on remote access type
        is_rdp = (ra_type == "RDP")
        is_browser = (ra_type == "Browser")
        
        self.ra_hostname_label.setVisible(is_rdp)
        self.ra_username_label.setVisible(is_rdp)
        self.ra_url_label.setVisible(is_browser)
    
    def _display_model_params(self, model, vpn_params):
        """Display model-specific parameters."""
        # Clear existing parameters
        while self.model_params_layout.count():
            item = self.model_params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new parameters
        if hasattr(model, "logical_fields") and model.logical_fields:
            for field in model.logical_fields:
                field_id = field.get("field_id", "")
                field_name = field.get("field_name", field_id)
                field_value = vpn_params.get(field_id, "")
                
                value_label = QLabel(str(field_value))
                self.model_params_layout.addRow(f"{field_name}:", value_label)
            
            self.model_params_group.setVisible(True)
        else:
            self.model_params_group.setVisible(False)
    
    def _display_automation_details(self, sequence):
        """Display automation sequence details."""
        if not sequence:
            self.automation_details.clear()
            return
        
        details = ""
        for i, step in enumerate(sequence):
            action = step.get("action", "Unknown Action")
            details_str = ", ".join(f"{k}: {v}" for k, v in step.items() if k != "action")
            details += f"{i+1}. {action} - {details_str}\n"
        
        self.automation_details.setText(details)
    
    def _clear_profile_details(self):
        """Clear all profile details."""
        # General tab
        self.profile_name_label.clear()
        self.profile_type_label.clear()
        self.profile_icon_label.clear()
        
        # VPN Connection tab
        self.vpn_server_label.clear()
        self.vpn_username_label.clear()
        self.vpn_group_label.clear()
        self.vpn_model_label.clear()
        self.model_params_group.setVisible(False)
        
        # Automation tab
        self.automation_summary_label.setText("No profile selected.")
        self.automation_details.clear()
        
        # Remote Access tab
        self.ra_type_label.clear()
        self.ra_hostname_label.clear()
        self.ra_username_label.clear()
        self.ra_url_label.clear()
    
    def _update_ui_state(self):
        """Update UI state based on current selection."""
        has_selection = self.current_profile is not None
        self.edit_profile_button.setEnabled(has_selection)
        self.delete_profile_button.setEnabled(has_selection)
        self.duplicate_profile_button.setEnabled(has_selection)
    
    def _new_profile(self):
        """Create a new VPN profile."""
        dialog = VPNProfileEditDialog(
            parent=self,
            vpn_manager_instance=self.vpn_manager,
            model_manager_instance=self.model_manager,
            icon_storage_dir=self.icon_dir
        )
        
        if dialog.exec():
            # Use get_profile_data instead of get_data
            try:
                profile_data = dialog.get_profile_data()
                if not profile_data:
                    QMessageBox.warning(self, "Error", "No profile data returned from dialog.")
                    return
                
                success = self.vpn_manager.save_profile(
                    profile_data["name"],
                    profile_data["type"],
                    profile_data["config"]
                )
                
                if success:
                    self._load_profiles()
                    # Select the new profile
                    for i in range(self.profile_list.count()):
                        item = self.profile_list.item(i)
                        if item.text() == profile_data["name"]:
                            self.profile_list.setCurrentItem(item)
                            break
                else:
                    QMessageBox.warning(self, "Error", "Failed to save profile.")
            except AttributeError:
                # Fallback if get_profile_data doesn't exist
                QMessageBox.warning(self, "Error", "Could not retrieve profile data from dialog.")
                return
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error retrieving profile data: {e}")
                return
                        for i in range(self.profile_list.count()):
                            item = self.profile_list.item(i)
                            if item.text() == profile_data["name"]:
                                self.profile_list.setCurrentItem(item)
                                break
                    else:
                        QMessageBox.warning(self, "Error", "Failed to save profile.")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to save profile: {e}")
    
    def _edit_profile(self):
        """Edit the selected VPN profile."""
        if not self.current_profile:
            QMessageBox.warning(self, "Error", "No profile selected.")
            return
        
        dialog = VPNProfileEditDialog(
            parent=self,
            profile_data=self.current_profile,
            vpn_manager_instance=self.vpn_manager,
            model_manager_instance=self.model_manager,
            icon_storage_dir=self.icon_dir
        )
        
        if dialog.exec():
            # Use get_profile_data instead of get_data
            try:
                profile_data = dialog.get_profile_data()
                if not profile_data:
                    QMessageBox.warning(self, "Error", "No profile data returned from dialog.")
                    return
                    
                # If name changed, delete old profile first
                old_name = self.current_profile["name"]
                if old_name != profile_data["name"]:
                    self.vpn_manager.delete_profile(old_name)
                
                success = self.vpn_manager.save_profile(
                    profile_data["name"],
                    profile_data["type"],
                    profile_data["config"]
                )
            except AttributeError:
                # Fallback if get_profile_data doesn't exist
                QMessageBox.warning(self, "Error", "Could not retrieve profile data from dialog.")
                return
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error retrieving profile data: {e}")
                return
                    
                    if success:
                        self._load_profiles()
                        # Select the edited profile
                        for i in range(self.profile_list.count()):
                            item = self.profile_list.item(i)
                            if item.text() == profile_data["name"]:
                                self.profile_list.setCurrentItem(item)
                                break
                    else:
                        QMessageBox.warning(self, "Error", "Failed to save profile.")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to save profile: {e}")
    
    def _delete_profile(self):
        """Delete the selected VPN profile."""
        if not self.current_profile:
            QMessageBox.warning(self, "Error", "No profile selected.")
            return
        
        profile_name = self.current_profile["name"]
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the profile '{profile_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.vpn_manager.delete_profile(profile_name)
                
                if success:
                    self._load_profiles()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete profile.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete profile: {e}")
    
    def _duplicate_profile(self):
        """Duplicate the selected VPN profile."""
        if not self.current_profile:
            QMessageBox.warning(self, "Error", "No profile selected.")
            return
        
        # Create a copy of the profile data
        profile_data = self.current_profile.copy()
        
        # Modify the name
        original_name = profile_data["name"]
        profile_data["name"] = f"{original_name} (Copy)"
        
        # Open the edit dialog with the duplicated profile
        dialog = VPNProfileEditDialog(
            parent=self,
            profile_data=profile_data,
            vpn_manager_instance=self.vpn_manager,
            model_manager_instance=self.model_manager,
            icon_storage_dir=self.icon_dir
        )
        
        if dialog.exec():
            new_profile_data = dialog.get_data()
            if new_profile_data:
                try:
                    success = self.vpn_manager.save_profile(
                        new_profile_data["name"],
                        new_profile_data["type"],
                        new_profile_data["config"]
                    )
                    
                    if success:
                        self._load_profiles()
                        # Select the new profile
                        for i in range(self.profile_list.count()):
                            item = self.profile_list.item(i)
                            if item.text() == new_profile_data["name"]:
                                self.profile_list.setCurrentItem(item)
                                break
                    else:
                        QMessageBox.warning(self, "Error", "Failed to save duplicated profile.")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to save duplicated profile: {e}")

if __name__ == "__main__":
    app = QApplication([])
    
    # Dummy classes for testing
    class DummyVPNManager:
        def list_profiles(self):
            return [
                {
                    "name": "Test Profile 1",
                    "type": "forticlient",
                    "config": {
                        "vpn_params": {
                            "server": "vpn.example.com",
                            "username": "testuser",
                            "group": "testgroup"
                        }
                    }
                },
                {
                    "name": "Test Profile 2",
                    "type": "globalprotect",
                    "config": {
                        "vpn_params": {
                            "server": "vpn2.example.com",
                            "username": "testuser2"
                        },
                        "remote_access": {
                            "type": "RDP",
                            "rdp_details": {
                                "hostname": "rdp.example.com",
                                "port": 3389,
                                "username": "rdpuser"
                            }
                        }
                    }
                }
            ]
        
        def save_profile(self, name, type, config):
            print(f"Saving profile: {name}, {type}")
            return True
        
        def delete_profile(self, name):
            print(f"Deleting profile: {name}")
            return True
    
    dialog = VPNConfigManagementDialog(vpn_manager=DummyVPNManager())
    dialog.exec()
