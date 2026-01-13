import os
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap

# Attempt to import backend modules and other UI dialogs
try:
    from ..vcal.vpn_manager import VPNManager
    from ..models.vpn_model_manager import VPNModelManager # For VPNProfileEditDialog
    from .vpn_profile_edit_dialog import VPNProfileEditDialog # For editing/creating profiles
    # Assuming icon directory might be needed from settings or a default
    from .settings_dialog import DEFAULT_ICON_DIR as APP_DEFAULT_ICON_DIR 
except ImportError as e:
    print(f"Warning (VPNManagementWidget): Could not import backend/UI modules: {e}. Using placeholders.")
    # Dummy classes for standalone UI testing or when imports fail
    class VPNManager:
        def __init__(self, config_dir: str):
            self.config_dir = config_dir
        def get_all_profiles(self) -> List[Dict[str, Any]]: return []  # Changed from list_profiles to get_all_profiles
        def save_profile(self, name: str, type: str, config: Dict[str, Any], icon_path: Optional[str] = None) -> bool: return False # Adjusted signature based on typical use
        def delete_profile(self, name: str) -> bool: return False
        def load_profile(self, name: str) -> Optional[Dict[str, Any]]: return None

    class VPNModelManager: # Dummy for VPNProfileEditDialog
        def __init__(self, models_dir: str):
            pass
        def list_models(self) -> List[Any]: return []
        def load_model(self, model_id: str) -> Optional[Any]: return None

    class VPNProfileEditDialog(QWidget): # QWidget to avoid QApplication issues in dummy
        def __init__(self, parent=None, profile_data=None, vpn_manager_instance=None, model_manager_instance=None, icon_storage_dir=None):
            super().__init__(parent)
            self.profile_data = profile_data
        def exec(self) -> bool: return False # Simulate QDialog.exec()
        def get_profile_data(self) -> Dict[str, Any]: return self.profile_data or {}

    APP_DEFAULT_ICON_DIR = os.path.join(os.path.expanduser("~"), ".vpn_auto_app_icons_dummy")

ICON_SIZE = QSize(24, 24)

class VPNManagementWidget(QWidget):
    """Widget for managing VPN profiles, designed to be embedded in the main window."""
    def __init__(self, vpn_manager: VPNManager, model_manager: Optional[VPNModelManager], icon_storage_dir: str = APP_DEFAULT_ICON_DIR, parent=None):
        super().__init__(parent)
        self.vpn_manager = vpn_manager
        self.model_manager = model_manager # Passed to VPNProfileEditDialog
        self.icon_storage_dir = icon_storage_dir
        if not os.path.exists(self.icon_storage_dir):
            os.makedirs(self.icon_storage_dir, exist_ok=True)

        self._init_ui()
        self.load_vpn_profiles()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0) # Ensure it fits well when embedded

        title_label = QLabel("Manage VPN Connection Profiles")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        self.profile_list_widget = QListWidget()
        self.profile_list_widget.setIconSize(ICON_SIZE)
        self.profile_list_widget.itemDoubleClicked.connect(self.edit_selected_profile)
        main_layout.addWidget(self.profile_list_widget)

        button_layout = QHBoxLayout()
        self.new_button = QPushButton(QIcon.fromTheme("document-new"), "New")
        self.edit_button = QPushButton(QIcon.fromTheme("document-properties"), "Edit")
        self.delete_button = QPushButton(QIcon.fromTheme("edit-delete"), "Delete")
        self.duplicate_button = QPushButton(QIcon.fromTheme("edit-copy"), "Duplicate")
        # No direct "Connect" button here as connection is handled by main window's dashboard view

        self.new_button.clicked.connect(self.add_new_profile)
        self.edit_button.clicked.connect(self.edit_selected_profile)
        self.delete_button.clicked.connect(self.delete_selected_profile)
        self.duplicate_button.clicked.connect(self.duplicate_selected_profile)

        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.duplicate_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def load_vpn_profiles(self):
        self.profile_list_widget.clear()
        try:
            profiles = self.vpn_manager.get_all_profiles()  # Changed from list_profiles to get_all_profiles
            for profile in profiles:
                profile_name = profile.get("name", "Unnamed VPN Profile")
                item = QListWidgetItem(profile_name)
                item.setData(Qt.ItemDataRole.UserRole, profile_name) # Store profile name for retrieval
                
                icon_path = profile.get("config", {}).get("icon_path")
                if icon_path and os.path.exists(icon_path):
                    item.setIcon(QIcon(icon_path))
                else:
                    item.setIcon(QIcon.fromTheme("network-vpn", QIcon(":/qt-project.org/styles/commonstyle/images/network-32.png"))) # Placeholder
                self.profile_list_widget.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load VPN profiles: {e}")
            print(f"Error loading VPN profiles: {e}")

    def add_new_profile(self):
        # VPNProfileEditDialog is expected to be a QDialog
        dialog = VPNProfileEditDialog(parent=self,
                                      vpn_manager_instance=self.vpn_manager,
                                      model_manager_instance=self.model_manager,
                                      icon_storage_dir=self.icon_storage_dir)
        if dialog.exec():
            new_profile_data = dialog.get_profile_data()
            profile_name = new_profile_data.get("name")
            profile_type = new_profile_data.get("type")
            config = new_profile_data.get("config", {})
            icon_path = config.get("icon_path") # Extract icon_path from config

            if self.vpn_manager.load_profile(profile_name): # Check if profile name exists
                QMessageBox.warning(self, "Save Error", f"A VPN profile with the name \t'{profile_name}\t' already exists.")
                return
            
            # The VPNManager.save_profile might need adjustment if its signature is different
            # For now, assuming it takes name, type, config, and icon_path separately or icon_path is within config
            if self.vpn_manager.save_profile(name=profile_name, type=profile_type, config=config):
                self.load_vpn_profiles()
            else:
                QMessageBox.warning(self, "Save Error", "Failed to save the new VPN profile.")

    def edit_selected_profile(self):
        selected_item = self.profile_list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Selection Required", "Please select a VPN profile to edit.")
            return
        profile_name = selected_item.data(Qt.ItemDataRole.UserRole)
        profile_data = self.vpn_manager.load_profile(profile_name)
        if not profile_data:
            QMessageBox.warning(self, "Error", f"Could not load profile data for \t'{profile_name}\t'. It may have been deleted.")
            self.load_vpn_profiles() # Refresh list
            return

        dialog = VPNProfileEditDialog(parent=self, 
                                      profile_data=profile_data, 
                                      vpn_manager_instance=self.vpn_manager,
                                      model_manager_instance=self.model_manager,
                                      icon_storage_dir=self.icon_storage_dir)
        if dialog.exec():
            updated_profile_data = dialog.get_profile_data()
            new_name = updated_profile_data.get("name")
            new_type = updated_profile_data.get("type")
            new_config = updated_profile_data.get("config", {})
            
            # If name changed, check for conflict with existing names (excluding current one if it was renamed)
            if profile_name != new_name and self.vpn_manager.load_profile(new_name):
                 QMessageBox.warning(self, "Save Error", f"A VPN profile with the name \t'{new_name}\t' already exists.")
                 return

            if self.vpn_manager.save_profile(name=new_name, type=new_type, config=new_config):
                if profile_name != new_name: # If name changed, delete the old profile
                    self.vpn_manager.delete_profile(profile_name)
                self.load_vpn_profiles()
            else:
                QMessageBox.warning(self, "Save Error", "Failed to save the updated VPN profile.")

    def delete_selected_profile(self):
        selected_item = self.profile_list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Selection Required", "Please select a VPN profile to delete.")
            return
        profile_name = selected_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete the VPN profile \t'{profile_name}\t'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.vpn_manager.delete_profile(profile_name):
                self.load_vpn_profiles()
            else:
                QMessageBox.warning(self, "Delete Error", f"Failed to delete VPN profile \t'{profile_name}\t'.")

    def duplicate_selected_profile(self):
        selected_item = self.profile_list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Selection Required", "Please select a VPN profile to duplicate.")
            return
        profile_name = selected_item.data(Qt.ItemDataRole.UserRole)
        original_profile = self.vpn_manager.load_profile(profile_name)
        if not original_profile:
            QMessageBox.warning(self, "Error", f"Could not load profile data for \t'{profile_name}\t' to duplicate.")
            return

        new_name = f"{original_profile.get('name', 'Profile')} (Copy)"
        counter = 1
        while self.vpn_manager.load_profile(new_name):
            counter += 1
            new_name = f"{original_profile.get('name', 'Profile')} (Copy {counter})"
        
        duplicated_profile = original_profile.copy()
        duplicated_profile["name"] = new_name
        # The config (including icon_path) is part of the duplicated_profile dictionary

        # save_profile expects name, type, config
        profile_type = duplicated_profile.get("type")
        config = duplicated_profile.get("config", {})

        if self.vpn_manager.save_profile(name=new_name, type=profile_type, config=config):
            self.load_vpn_profiles()
        else:
            QMessageBox.warning(self, "Duplicate Error", f"Failed to save duplicated VPN profile \t'{new_name}\t'.")

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # Create dummy managers for testing
    test_vpn_profiles_dir = "./temp_vpn_profiles_widget_test"
    if not os.path.exists(test_vpn_profiles_dir):
        os.makedirs(test_vpn_profiles_dir)
    
    dummy_vpn_manager = VPNManager(config_dir=test_vpn_profiles_dir)
    dummy_model_manager = VPNModelManager(models_dir="./dummy_models") # Dummy path
    
    # Pre-populate with some data for testing
    dummy_vpn_manager.save_profile(name="Work VPN", type="forticlient", config={"server": "vpn.work.com", "username": "user"})
    dummy_vpn_manager.save_profile(name="Home VPN", type="globalprotect", config={"server": "vpn.home.net"})

    widget = VPNManagementWidget(dummy_vpn_manager, dummy_model_manager, icon_storage_dir=os.path.join(test_vpn_profiles_dir, "icons"))
    widget.setWindowTitle("VPN Management Widget Test")
    widget.setGeometry(100, 100, 600, 400)
    widget.show()

    exit_code = app.exec()
    
    # Cleanup test directory
    if os.path.exists(test_vpn_profiles_dir):
        import shutil
        shutil.rmtree(test_vpn_profiles_dir)
    sys.exit(exit_code)
