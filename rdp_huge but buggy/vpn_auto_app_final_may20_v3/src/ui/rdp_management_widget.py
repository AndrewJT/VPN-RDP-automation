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
    from ..core.rdp_profile_manager import RDPProfileManager
    from ..core.remote_access_manager import RemoteAccessManager # For launching RDP
    from .rdp_edit_dialog import RDPEditDialog, DEFAULT_ICON_STORAGE_DIR as RDP_ICON_DIR
except ImportError as e:
    print(f"Warning (RDPManagementWidget): Could not import backend/UI modules: {e}. Using placeholders.")
    # Dummy classes for standalone UI testing or when imports fail
    class RDPProfileManager:
        def __init__(self, profiles_dir: str):
            self.profiles_dir = profiles_dir
        def list_profiles(self) -> List[Dict[str, Any]]: return []
        def save_profile(self, profile_data: Dict[str, Any]) -> bool: return False
        def delete_profile(self, name: str) -> bool: return False
        def get_profile(self, name: str) -> Optional[Dict[str, Any]]: return None

    class RemoteAccessManager:
        def initiate_access(self, access_type: str, details: Dict[str, Any]) -> tuple[bool, str]:
            print(f"Dummy RemoteAccessManager: Initiate {access_type} with {details}")
            return True, "Dummy access initiated."

    class RDPEditDialog(QWidget): # QWidget to avoid QApplication issues in dummy
        def __init__(self, parent=None, profile_data=None, icon_storage_dir=None):
            super().__init__(parent)
            self.profile_data = profile_data
        def exec(self) -> bool: return False # Simulate QDialog.exec()
        def get_profile_data(self) -> Dict[str, Any]: return self.profile_data or {}

    RDP_ICON_DIR = os.path.join(os.path.expanduser("~"), ".vpn_auto_app_icons", "rdp_icons_dummy")

ICON_SIZE = QSize(24, 24)

class RDPManagementWidget(QWidget):
    """Widget for managing RDP profiles, designed to be embedded in the main window."""
    def __init__(self, rdp_profile_manager: RDPProfileManager, remote_access_manager: RemoteAccessManager, icon_storage_dir: str = RDP_ICON_DIR, parent=None):
        super().__init__(parent)
        self.rdp_manager = rdp_profile_manager
        self.remote_manager = remote_access_manager
        self.icon_storage_dir = icon_storage_dir
        if not os.path.exists(self.icon_storage_dir):
            os.makedirs(self.icon_storage_dir, exist_ok=True)

        self._init_ui()
        self.load_rdp_profiles()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0) # Ensure it fits well when embedded

        # Title Label
        title_label = QLabel("Manage RDP Connection Profiles")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Profile List Area
        self.profile_list_widget = QListWidget()
        self.profile_list_widget.setIconSize(ICON_SIZE)
        self.profile_list_widget.itemDoubleClicked.connect(self.edit_selected_profile)
        main_layout.addWidget(self.profile_list_widget)

        # Buttons Layout
        button_layout = QHBoxLayout()
        self.new_button = QPushButton(QIcon.fromTheme("document-new", QIcon(":/qt-project.org/styles/commonstyle/images/newdirectory-32.png")), "New") # Placeholder icon
        self.edit_button = QPushButton(QIcon.fromTheme("document-properties", QIcon(":/qt-project.org/styles/commonstyle/images/file-32.png")), "Edit")
        self.delete_button = QPushButton(QIcon.fromTheme("edit-delete", QIcon(":/qt-project.org/styles/commonstyle/images/delete-32.png")), "Delete")
        self.duplicate_button = QPushButton(QIcon.fromTheme("edit-copy"), "Duplicate") # Placeholder icon
        self.connect_button = QPushButton(QIcon.fromTheme("network-wired"), "Connect") # Placeholder icon

        self.new_button.clicked.connect(self.add_new_profile)
        self.edit_button.clicked.connect(self.edit_selected_profile)
        self.delete_button.clicked.connect(self.delete_selected_profile)
        self.duplicate_button.clicked.connect(self.duplicate_selected_profile)
        self.connect_button.clicked.connect(self.connect_selected_profile)

        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.duplicate_button)
        button_layout.addStretch()
        button_layout.addWidget(self.connect_button)
        main_layout.addLayout(button_layout)

    def load_rdp_profiles(self):
        self.profile_list_widget.clear()
        try:
            profiles = self.rdp_manager.list_profiles()
            for profile in profiles:
                item = QListWidgetItem(profile.get("name", "Unnamed RDP Profile"))
                item.setData(Qt.ItemDataRole.UserRole, profile.get("name")) # Store profile name for retrieval
                icon_path = profile.get("icon_path")
                if icon_path and os.path.exists(icon_path):
                    item.setIcon(QIcon(icon_path))
                else:
                    item.setIcon(QIcon.fromTheme("network-workgroup", QIcon(":/qt-project.org/styles/commonstyle/images/network-32.png"))) # Placeholder
                self.profile_list_widget.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load RDP profiles: {e}")
            print(f"Error loading RDP profiles: {e}")

    def add_new_profile(self):
        dialog = RDPEditDialog(parent=self, icon_storage_dir=self.icon_storage_dir)
        if dialog.exec():
            new_profile_data = dialog.get_profile_data()
            if self.rdp_manager.get_profile(new_profile_data["name"]):
                QMessageBox.warning(self, "Save Error", f"An RDP profile with the name \t'{new_profile_data['name']}\t' already exists.")
                return
            if self.rdp_manager.save_profile(new_profile_data):
                self.load_rdp_profiles()
            else:
                QMessageBox.warning(self, "Save Error", "Failed to save the new RDP profile.")

    def edit_selected_profile(self):
        selected_item = self.profile_list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Selection Required", "Please select an RDP profile to edit.")
            return
        profile_name = selected_item.data(Qt.ItemDataRole.UserRole)
        profile_data = self.rdp_manager.get_profile(profile_name)
        if not profile_data:
            QMessageBox.warning(self, "Error", f"Could not load profile data for 	'{profile_name}	'. It may have been deleted.")
            self.load_rdp_profiles() # Refresh list
            return

        dialog = RDPEditDialog(parent=self, profile_data=profile_data, icon_storage_dir=self.icon_storage_dir)
        if dialog.exec():
            updated_profile_data = dialog.get_profile_data()
            # If name changed, check for conflict with existing names (excluding current one if it was renamed)
            original_name = profile_name
            new_name = updated_profile_data["name"]
            if original_name != new_name and self.rdp_manager.get_profile(new_name):
                 QMessageBox.warning(self, "Save Error", f"An RDP profile with the name 	'{new_name}	' already exists.")
                 return
            
            if self.rdp_manager.save_profile(updated_profile_data):
                # If name changed, we might need to delete the old entry if save_profile doesn't handle renaming by key
                if original_name != new_name:
                    self.rdp_manager.delete_profile(original_name) # Delete old if name changed
                self.load_rdp_profiles()
            else:
                QMessageBox.warning(self, "Save Error", "Failed to save the updated RDP profile.")

    def delete_selected_profile(self):
        selected_item = self.profile_list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Selection Required", "Please select an RDP profile to delete.")
            return
        profile_name = selected_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete the RDP profile 	'{profile_name}	'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.rdp_manager.delete_profile(profile_name):
                self.load_rdp_profiles()
            else:
                QMessageBox.warning(self, "Delete Error", f"Failed to delete RDP profile 	'{profile_name}	'.")

    def duplicate_selected_profile(self):
        selected_item = self.profile_list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Selection Required", "Please select an RDP profile to duplicate.")
            return
        profile_name = selected_item.data(Qt.ItemDataRole.UserRole)
        original_profile = self.rdp_manager.get_profile(profile_name)
        if not original_profile:
            QMessageBox.warning(self, "Error", f"Could not load profile data for 	'{profile_name}	' to duplicate.")
            return

        new_name = f"{original_profile['name']} (Copy)"
        counter = 1
        while self.rdp_manager.get_profile(new_name):
            counter += 1
            new_name = f"{original_profile['name']} (Copy {counter})"
        
        duplicated_profile = original_profile.copy()
        duplicated_profile["name"] = new_name
        # If icon_path exists, it's already a path to a stored icon, so it can be reused.

        if self.rdp_manager.save_profile(duplicated_profile):
            self.load_rdp_profiles()
        else:
            QMessageBox.warning(self, "Duplicate Error", f"Failed to save duplicated RDP profile 	'{new_name}	'.")
    def connect_selected_profile(self):
        selected_item = self.profile_list_widget.currentItem()
        if not selected_item:
            QMessageBox.information(self, "Selection Required", "Please select an RDP profile to connect.")
            return
        profile_name = selected_item.data(Qt.ItemDataRole.UserRole)
        profile_data = self.rdp_manager.get_profile(profile_name)
        if not profile_data:
            QMessageBox.warning(self, "Error", f"Could not load profile data for '{profile_name}' to connect.")
            return
        
        # Use connect_rdp method directly for better parameter handling
        hostname = profile_data.get("hostname", "")
        port = profile_data.get("port", 3389)
        username = profile_data.get("username", "")
        password = profile_data.get("password", "")
        domain = profile_data.get("domain", "")
        
        try:
            success = self.remote_manager.connect_rdp(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                domain=domain
            )
            
            if success:
                QMessageBox.information(self, "RDP Initiated", f"RDP connection to {hostname} initiated successfully.")
            else:
                QMessageBox.critical(self, "RDP Error", f"Failed to connect to RDP server {hostname}.")
        except Exception as e:
            QMessageBox.critical(self, "RDP Error", f"Error connecting to RDP: {str(e)}")
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # Create dummy managers for testing
    test_rdp_profiles_dir = "./temp_rdp_profiles_widget_test"
    if not os.path.exists(test_rdp_profiles_dir):
        os.makedirs(test_rdp_profiles_dir)
    
    dummy_rdp_manager = RDPProfileManager(profiles_dir=test_rdp_profiles_dir)
    dummy_remote_manager = RemoteAccessManager()
    
    # Pre-populate with some data for testing
    dummy_rdp_manager.save_profile({"name": "Test Server 1", "hostname": "server1.example.com", "username": "admin"})
    dummy_rdp_manager.save_profile({"name": "Dev Machine", "hostname": "192.168.1.50"})

    widget = RDPManagementWidget(dummy_rdp_manager, dummy_remote_manager, icon_storage_dir=os.path.join(test_rdp_profiles_dir, "icons"))
    widget.setWindowTitle("RDP Management Widget Test")
    widget.setGeometry(100, 100, 600, 400)
    widget.show()

    exit_code = app.exec()
    
    # Cleanup test directory
    if os.path.exists(test_rdp_profiles_dir):
        import shutil
        shutil.rmtree(test_rdp_profiles_dir)
    sys.exit(exit_code)

