import os
from typing import Optional, List, Dict, Any, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QMessageBox, QLabel, QComboBox, QToolBar, QMenu,
    QInputDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QAction

# Attempt to import backend modules and other UI dialogs
try:
    from ..vcal.vpn_manager import VPNManager
    from ..models.vpn_model_manager import VPNModelManager
    from ..core.rdp_profile_manager import RDPProfileManager
    from ..core.remote_access_manager import RemoteAccessManager
    from .vpn_profile_edit_dialog import VPNProfileEditDialog
    from .rdp_edit_dialog import RDPEditDialog
    from .settings_dialog import DEFAULT_ICON_DIR as APP_DEFAULT_ICON_DIR
except ImportError as e:
    print(f"Warning (ConnectionTreeWidget): Could not import backend/UI modules: {e}. Using placeholders.")
    # Dummy classes for standalone UI testing or when imports fail
    class VPNManager:
        def __init__(self, config_dir: str):
            self.config_dir = config_dir
        def get_all_profiles(self) -> List[Dict[str, Any]]: return []
        def save_profile(self, profile_name: str, vpn_type: str, vpn_config: Dict[str, Any], icon_path: Optional[str] = None) -> bool: return False
        def delete_profile(self, name: str) -> bool: return False
        def load_profile(self, name: str) -> Optional[Dict[str, Any]]: return None

    class VPNModelManager:
        def __init__(self, models_dir: str): pass
        def list_models(self) -> List[Any]: return []
        def load_model(self, model_id: str) -> Optional[Any]: return None
        
    class RDPProfileManager:
        def __init__(self, profiles_dir: str): pass
        def list_profiles(self) -> List[Dict[str, Any]]: return []
        def get_profile(self, name: str) -> Optional[Dict[str, Any]]: return None
        def save_profile(self, profile_data: Dict[str, Any]) -> bool: return False
        def delete_profile(self, name: str) -> bool: return False
        
    class RemoteAccessManager:
        def __init__(self): pass
        def connect_rdp(self, hostname, port=3389, username=None, password=None, domain=None, **kwargs): return True
        def initiate_access(self, access_type: str, details: Dict[str, Any]): return True, "Success"

    class VPNProfileEditDialog(QWidget):
        def __init__(self, parent=None, profile_data=None, vpn_manager_instance=None, model_manager_instance=None, icon_storage_dir=None):
            super().__init__(parent)
            self.profile_data = profile_data
        def exec(self) -> bool: return False
        def get_profile_data(self) -> Dict[str, Any]: return self.profile_data or {}
        
    class RDPEditDialog(QWidget):
        def __init__(self, parent=None, profile_data=None, icon_storage_dir=None):
            super().__init__(parent)
            self.profile_data = profile_data
        def exec(self) -> bool: return False
        def get_profile_data(self) -> Dict[str, Any]: return self.profile_data or {}

    APP_DEFAULT_ICON_DIR = os.path.join(os.path.expanduser("~"), ".vpn_auto_app_icons_dummy")

ICON_SIZE = QSize(24, 24)
FOLDER_TYPE = "folder"
VPN_CONNECTION_TYPE = "vpn"
RDP_CONNECTION_TYPE = "rdp"

class ConnectionTreeWidget(QWidget):
    """Tree widget for managing VPN and RDP connections with folder organization."""
    connection_selected = pyqtSignal(str, str, dict)  # Emits (connection_name, connection_type, connection_details)
    
    def __init__(self, vpn_manager: VPNManager, model_manager: Optional[VPNModelManager], 
                 rdp_profile_manager: Optional[RDPProfileManager] = None,
                 remote_access_manager: Optional[RemoteAccessManager] = None,
                 icon_storage_dir: str = APP_DEFAULT_ICON_DIR, parent=None):
        super().__init__(parent)
        self.vpn_manager = vpn_manager
        self.model_manager = model_manager
        self.rdp_profile_manager = rdp_profile_manager
        self.remote_access_manager = remote_access_manager or RemoteAccessManager()
        self.icon_storage_dir = icon_storage_dir
        if not os.path.exists(self.icon_storage_dir):
            os.makedirs(self.icon_storage_dir, exist_ok=True)
            
        # Store recent and favorite connections
        self.recent_connections = []
        self.favorite_connections = []
        
        self._init_ui()
        self.load_connections()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Quick Connect Bar
        quick_connect_layout = QHBoxLayout()
        quick_connect_layout.setContentsMargins(5, 5, 5, 5)
        
        self.quick_connect_combo = QComboBox()
        self.quick_connect_combo.setMinimumWidth(200)
        self.quick_connect_combo.setEditable(True)
        self.quick_connect_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.quick_connect_combo.lineEdit().returnPressed.connect(self._quick_connect)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._quick_connect)
        
        self.favorite_button = QPushButton("☆")  # Start with unfilled star
        self.favorite_button.setToolTip("Add to Favorites")
        self.favorite_button.clicked.connect(self._toggle_favorite)
        
        quick_connect_layout.addWidget(QLabel("Quick Connect:"))
        quick_connect_layout.addWidget(self.quick_connect_combo)
        quick_connect_layout.addWidget(self.connect_button)
        quick_connect_layout.addWidget(self.favorite_button)
        
        main_layout.addLayout(quick_connect_layout)
        
        # Connection Tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Connections"])
        self.tree_widget.setIconSize(ICON_SIZE)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree_widget.itemClicked.connect(self._on_item_clicked)
        main_layout.addWidget(self.tree_widget)
        
        # Button Bar
        button_layout = QHBoxLayout()
        
        self.new_connection_button = QPushButton("New Connection")
        self.new_folder_button = QPushButton("New Folder")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.connect_selected_button = QPushButton("Connect")
        
        self.new_connection_button.clicked.connect(self._new_connection)
        self.new_folder_button.clicked.connect(self._new_folder)
        self.edit_button.clicked.connect(self._edit_selected)
        self.delete_button.clicked.connect(self._delete_selected)
        self.connect_selected_button.clicked.connect(self._connect_selected)
        
        button_layout.addWidget(self.new_connection_button)
        button_layout.addWidget(self.new_folder_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.connect_selected_button)
        
        main_layout.addLayout(button_layout)
    
    def load_connections(self):
        """Load all connections and organize them into the tree."""
        self.tree_widget.clear()
        
        # Create root folders for organization
        vpn_folder = self._create_folder_item("VPN Connections")
        rdp_folder = self._create_folder_item("RDP Connections")
        
        # Add root folders to tree
        self.tree_widget.addTopLevelItem(vpn_folder)
        self.tree_widget.addTopLevelItem(rdp_folder)
        
        # Load VPN connections
        try:
            vpn_profiles = self.vpn_manager.get_all_profiles()
            for profile in vpn_profiles:
                profile_name = profile.get("name", "Unnamed VPN Profile")
                item = self._create_connection_item(profile_name, VPN_CONNECTION_TYPE, profile)
                
                # Set icon if available
                icon_path = profile.get("icon_path")
                if icon_path and os.path.exists(icon_path):
                    item.setIcon(0, QIcon(icon_path))
                else:
                    item.setIcon(0, QIcon.fromTheme("network-vpn", QIcon(":/qt-project.org/styles/commonstyle/images/network-32.png")))
                
                vpn_folder.addChild(item)
        except Exception as e:
            logging.error(f"Error loading VPN profiles: {e}")
            error_item = QTreeWidgetItem(vpn_folder, ["Error loading VPN profiles"])
            error_item.setForeground(0, Qt.GlobalColor.red)
        
        # Load RDP connections if RDP profile manager is available
        if self.rdp_profile_manager:
            try:
                rdp_profiles = self.rdp_profile_manager.list_profiles()
                for profile in rdp_profiles:
                    profile_name = profile.get("name", "Unnamed RDP Profile")
                    item = self._create_connection_item(profile_name, RDP_CONNECTION_TYPE, profile)
                    
                    # Set icon if available
                    icon_path = profile.get("icon_path")
                    if icon_path and os.path.exists(icon_path):
                        item.setIcon(0, QIcon(icon_path))
                    else:
                        item.setIcon(0, QIcon.fromTheme("computer", QIcon(":/qt-project.org/styles/commonstyle/images/computer-32.png")))
                    
                    rdp_folder.addChild(item)
            except Exception as e:
                logging.error(f"Error loading RDP profiles: {e}")
                error_item = QTreeWidgetItem(rdp_folder, ["Error loading RDP profiles"])
                error_item.setForeground(0, Qt.GlobalColor.red)
        
        # Expand root folders
        vpn_folder.setExpanded(True)
        rdp_folder.setExpanded(True)
        
        # Update quick connect combo
        self._update_quick_connect_combo()
    
    def _create_folder_item(self, name: str) -> QTreeWidgetItem:
        """Create a folder item for the tree."""
        item = QTreeWidgetItem([name])
        item.setIcon(0, QIcon.fromTheme("folder", QIcon(":/qt-project.org/styles/commonstyle/images/diropen-32.png")))
        item.setData(0, Qt.ItemDataRole.UserRole, {"type": FOLDER_TYPE, "name": name})
        return item
    
    def _create_connection_item(self, name: str, conn_type: str, data: Dict[str, Any]) -> QTreeWidgetItem:
        """Create a connection item for the tree."""
        item = QTreeWidgetItem([name])
        item.setData(0, Qt.ItemDataRole.UserRole, {"type": conn_type, "name": name, "data": data})
        return item
    
    def _update_quick_connect_combo(self):
        """Update the quick connect combo box with recent and favorite connections."""
        self.quick_connect_combo.clear()
        
        # Add recent connections
        for conn in self.recent_connections:
            self.quick_connect_combo.addItem(f"{conn['name']} ({conn['type'].upper()})", conn)
        
        # Add separator if there are both recent and favorite connections
        if self.recent_connections and self.favorite_connections:
            self.quick_connect_combo.insertSeparator(len(self.recent_connections))
        
        # Add favorite connections
        for conn in self.favorite_connections:
            self.quick_connect_combo.addItem(f"★ {conn['name']} ({conn['type'].upper()})", conn)
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click in the tree."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        item_type = data.get("type")
        item_name = data.get("name")
        
        if item_type in [VPN_CONNECTION_TYPE, RDP_CONNECTION_TYPE]:
            # Emit signal with connection details
            item_data = data.get("data", {})
            self.connection_selected.emit(item_name, item_type, item_data)
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item double-click in the tree."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        item_type = data.get("type")
        item_name = data.get("name")
        
        if item_type == FOLDER_TYPE:
            # Toggle folder expansion
            item.setExpanded(not item.isExpanded())
        elif item_type in [VPN_CONNECTION_TYPE, RDP_CONNECTION_TYPE]:
            # Connect to the selected connection
            item_data = data.get("data", {})
            self._connect_to(item_name, item_type, item_data)
    
    def _show_context_menu(self, position):
        """Show context menu for tree items."""
        item = self.tree_widget.itemAt(position)
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        item_type = data.get("type")
        item_name = data.get("name")
        item_data = data.get("data", {})
        
        menu = QMenu()
        
        if item_type == FOLDER_TYPE:
            # Folder context menu
            add_connection_action = menu.addAction("Add Connection")
            add_connection_action.triggered.connect(lambda: self._new_connection(parent_folder=item))
            
            add_subfolder_action = menu.addAction("Add Subfolder")
            add_subfolder_action.triggered.connect(lambda: self._new_folder(parent_folder=item))
            
            menu.addSeparator()
            
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(lambda: self._rename_folder(item))
            
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(lambda: self._delete_folder(item))
        
        elif item_type in [VPN_CONNECTION_TYPE, RDP_CONNECTION_TYPE]:
            # Connection context menu
            connect_action = menu.addAction("Connect")
            connect_action.triggered.connect(lambda: self._connect_to(item_name, item_type, item_data))
            
            menu.addSeparator()
            
            edit_action = menu.addAction("Edit")
            edit_action.triggered.connect(lambda: self._edit_connection(item))
            
            duplicate_action = menu.addAction("Duplicate")
            duplicate_action.triggered.connect(lambda: self._duplicate_connection(item))
            
            menu.addSeparator()
            
            add_to_favorites_action = menu.addAction("Add to Favorites" if not self._is_favorite(item_name, item_type) else "Remove from Favorites")
            add_to_favorites_action.triggered.connect(lambda: self._toggle_favorite_connection(item_name, item_type, item_data))
            
            menu.addSeparator()
            
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(lambda: self._delete_connection(item))
        
        menu.exec(self.tree_widget.viewport().mapToGlobal(position))
    
    def _new_connection(self, parent_folder=None):
        """Create a new connection."""
        # First, determine the connection type
        connection_types = ["VPN", "RDP"]
        if not self.rdp_profile_manager:
            connection_types = ["VPN"]  # Only offer VPN if RDP manager is not available
            
        conn_type, ok = QInputDialog.getItem(
            self, "New Connection", "Select connection type:", connection_types, 0, False
        )
        
        if not ok or not conn_type:
            return
            
        if conn_type == "VPN":
            self._new_vpn_connection(parent_folder)
        elif conn_type == "RDP":
            self._new_rdp_connection(parent_folder)
    
    def _new_vpn_connection(self, parent_folder=None):
        """Create a new VPN connection."""
        dialog = VPNProfileEditDialog(
            parent=self,
            profile_data=None,  # New profile
            vpn_manager_instance=self.vpn_manager,
            model_manager_instance=self.model_manager,
            icon_storage_dir=os.path.join(self.icon_storage_dir, "vpn_icons")
        )
        
        if dialog.exec():
            try:
                profile_data = dialog.get_profile_data()
                profile_name = profile_data.get("name", "")
                profile_type = profile_data.get("type", "")
                
                # Extract icon_path if present
                icon_path = profile_data.get("icon_path")
                
                # Save the profile
                success = False
                if icon_path and os.path.exists(icon_path):
                    success = self.vpn_manager.save_profile(
                        profile_name=profile_name,
                        vpn_type=profile_type,
                        vpn_config=profile_data,
                        icon_path=icon_path
                    )
                else:
                    success = self.vpn_manager.save_profile(
                        profile_name=profile_name,
                        vpn_type=profile_type,
                        vpn_config=profile_data
                    )
                
                if success:
                    # Add to recent connections
                    self._add_to_recent(profile_name, VPN_CONNECTION_TYPE, profile_data)
                    # Reload connections
                    self.load_connections()
                    QMessageBox.information(self, "Success", f"VPN profile '{profile_name}' created successfully.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to create VPN profile '{profile_name}'.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error creating VPN profile: {e}")
    
    def _new_rdp_connection(self, parent_folder=None):
        """Create a new RDP connection."""
        if not self.rdp_profile_manager:
            QMessageBox.warning(self, "Error", "RDP profile manager is not available.")
            return
            
        dialog = RDPEditDialog(
            parent=self,
            profile_data=None,  # New profile
            icon_storage_dir=os.path.join(self.icon_storage_dir, "rdp_icons")
        )
        
        if dialog.exec():
            try:
                profile_data = dialog.get_profile_data()
                profile_name = profile_data.get("name", "")
                
                # Save the profile
                success = self.rdp_profile_manager.save_profile(profile_data)
                
                if success:
                    # Add to recent connections
                    self._add_to_recent(profile_name, RDP_CONNECTION_TYPE, profile_data)
                    # Reload connections
                    self.load_connections()
                    QMessageBox.information(self, "Success", f"RDP profile '{profile_name}' created successfully.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to create RDP profile '{profile_name}'.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error creating RDP profile: {e}")
    
    def _new_folder(self, parent_folder=None):
        """Create a new folder."""
        folder_name, ok = QInputDialog.getText(
            self, "New Folder", "Enter folder name:", QLineEdit.EchoMode.Normal
        )
        
        if not ok or not folder_name:
            return
            
        folder_item = self._create_folder_item(folder_name)
        
        if parent_folder:
            parent_folder.addChild(folder_item)
        else:
            self.tree_widget.addTopLevelItem(folder_item)
    
    def _edit_selected(self):
        """Edit the selected item."""
        item = self.tree_widget.currentItem()
        if not item:
            return
            
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        item_type = data.get("type")
        
        if item_type == FOLDER_TYPE:
            self._rename_folder(item)
        elif item_type in [VPN_CONNECTION_TYPE, RDP_CONNECTION_TYPE]:
            self._edit_connection(item)
    
    def _delete_selected(self):
        """Delete the selected item."""
        item = self.tree_widget.currentItem()
        if not item:
            return
            
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        item_type = data.get("type")
        
        if item_type == FOLDER_TYPE:
            self._delete_folder(item)
        elif item_type in [VPN_CONNECTION_TYPE, RDP_CONNECTION_TYPE]:
            self._delete_connection(item)
    
    def _connect_selected(self):
        """Connect to the selected connection."""
        item = self.tree_widget.currentItem()
        if not item:
            return
            
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        item_type = data.get("type")
        item_name = data.get("name")
        item_data = data.get("data", {})
        
        if item_type in [VPN_CONNECTION_TYPE, RDP_CONNECTION_TYPE]:
            self._connect_to(item_name, item_type, item_data)
    
    def _quick_connect(self):
        """Connect using the quick connect combo."""
        index = self.quick_connect_combo.currentIndex()
        if index >= 0:
            # Get connection from combo box item data
            conn_data = self.quick_connect_combo.itemData(index)
            if conn_data:
                conn_name = conn_data.get("name", "")
                conn_type = conn_data.get("type", "")
                conn_details = conn_data.get("data", {})
                
                if conn_type and conn_name:
                    self._connect_to(conn_name, conn_type, conn_details)
                    return
        
        # Try to connect using the text as a hostname/IP
        text = self.quick_connect_combo.currentText().strip()
        if text:
            # Check if it's an IP address or hostname (direct RDP connection)
            if self._looks_like_hostname_or_ip(text):
                # Create basic details for direct RDP connection
                details = {"hostname": text, "port": 3389}
                # Add to recent connections
                self._add_to_recent(text, RDP_CONNECTION_TYPE, details)
                # Connect
                self._connect_to(text, RDP_CONNECTION_TYPE, details)
                return
                
            # Search in existing connections
            for conn in self.recent_connections + self.favorite_connections:
                if conn.get("name", "").lower() == text.lower():
                    self._connect_to(conn.get("name", ""), conn.get("type", ""), conn.get("data", {}))
                    return
                    
            # Not found, ask user if they want to create a new RDP connection
            if QMessageBox.question(
                self, 
                "New Connection", 
                f"'{text}' is not a recognized connection. Do you want to create a new RDP connection to this host?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                # Create basic details for new RDP connection
                details = {"hostname": text, "port": 3389, "name": text}
                # Add to recent connections
                self._add_to_recent(text, RDP_CONNECTION_TYPE, details)
                # Connect
                self._connect_to(text, RDP_CONNECTION_TYPE, details)
    
    def _looks_like_hostname_or_ip(self, text):
        """Check if text looks like a hostname or IP address."""
        # Simple check for IP or hostname patterns
        return (
            "." in text or  # Has dots like domain or IP
            text.lower() == "localhost" or  # Localhost
            text.isdigit() or  # Numeric only could be an IP without dots
            (text.replace(".", "").isdigit() and text.count(".") <= 3)  # IP-like with dots
        )
    
    def _toggle_favorite(self):
        """Toggle favorite status of the current quick connect entry."""
        index = self.quick_connect_combo.currentIndex()
        if index >= 0:
            # Get connection from combo box item data
            conn_data = self.quick_connect_combo.itemData(index)
            if conn_data:
                conn_name = conn_data.get("name", "")
                conn_type = conn_data.get("type", "")
                conn_details = conn_data.get("data", {})
                
                self._toggle_favorite_connection(conn_name, conn_type, conn_details)
        else:
            # Try to favorite the current text
            text = self.quick_connect_combo.currentText().strip()
            if text and self._looks_like_hostname_or_ip(text):
                # Create basic details for RDP connection
                details = {"hostname": text, "port": 3389, "name": text}
                # Add to favorites
                self._toggle_favorite_connection(text, RDP_CONNECTION_TYPE, details)
    
    def _toggle_favorite_connection(self, name, conn_type, details=None):
        """Toggle favorite status of a connection."""
        # Check if it's already a favorite
        is_favorite = self._is_favorite(name, conn_type)
        
        if is_favorite:
            # Remove from favorites
            self.favorite_connections = [
                conn for conn in self.favorite_connections
                if not (conn.get("name") == name and conn.get("type") == conn_type)
            ]
        else:
            # Add to favorites
            self.favorite_connections.append({
                "name": name,
                "type": conn_type,
                "data": details or {}
            })
            
            # Also add to recent if not already there
            if not any(conn.get("name") == name and conn.get("type") == conn_type for conn in self.recent_connections):
                self._add_to_recent(name, conn_type, details or {})
        
        # Update the combo box
        self._update_quick_connect_combo()
    
    def _is_favorite(self, name, conn_type):
        """Check if a connection is a favorite."""
        return any(
            conn.get("name") == name and conn.get("type") == conn_type
            for conn in self.favorite_connections
        )
    
    def _add_to_recent(self, name, conn_type, details=None):
        """Add a connection to the recent list."""
        # Remove if already in list
        self.recent_connections = [
            conn for conn in self.recent_connections
            if not (conn.get("name") == name and conn.get("type") == conn_type)
        ]
        
        # Add to beginning of list
        self.recent_connections.insert(0, {
            "name": name,
            "type": conn_type,
            "data": details or {}
        })
        
        # Limit to 10 recent connections
        if len(self.recent_connections) > 10:
            self.recent_connections = self.recent_connections[:10]
        
        # Update the combo box
        self._update_quick_connect_combo()
    
    def _connect_to(self, name, conn_type, details=None):
        """Connect to a connection."""
        try:
            if conn_type == VPN_CONNECTION_TYPE:
                self._connect_vpn(name, details)
            elif conn_type == RDP_CONNECTION_TYPE:
                self._connect_rdp(name, details)
            else:
                QMessageBox.warning(self, "Error", f"Unknown connection type: {conn_type}")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Error connecting to {name}: {e}")
    
    def _connect_vpn(self, name, details=None):
        """Connect to a VPN connection."""
        # This would typically call the VPN manager to connect
        QMessageBox.information(self, "VPN Connection", f"Connecting to VPN: {name}")
        
        # Add to recent connections
        self._add_to_recent(name, VPN_CONNECTION_TYPE, details)
    
    def _connect_rdp(self, name, details=None):
        """Connect to an RDP connection using the RemoteAccessManager."""
        if not details:
            # Try to load profile details if available
            if self.rdp_profile_manager:
                details = self.rdp_profile_manager.get_profile(name) or {}
            
            if not details:
                # Fallback to basic details
                details = {"hostname": name, "port": 3389}
        
        # Extract connection parameters
        hostname = details.get("hostname", name)
        port = details.get("port", 3389)
        username = details.get("username", "")
        password = details.get("password", "")
        domain = details.get("domain", "")
        
        # Additional parameters for advanced settings
        fullscreen = details.get("fullscreen", True)
        admin_console = details.get("admin_console", False)
        width = details.get("width", 1024)
        height = details.get("height", 768)
        
        # Authentication settings
        auth_method = details.get("auth_method", "default")
        
        # Gateway settings
        use_gateway = details.get("use_gateway", False)
        gateway_hostname = details.get("gateway_hostname", "")
        gateway_username = details.get("gateway_username", "")
        gateway_password = details.get("gateway_password", "")
        gateway_domain = details.get("gateway_domain", "")
        
        # Redirection settings
        redirect_drives = details.get("redirect_drives", True)
        redirect_printers = details.get("redirect_printers", True)
        redirect_clipboard = details.get("redirect_clipboard", True)
        redirect_smartcards = details.get("redirect_smartcards", False)
        redirect_audio = details.get("redirect_audio", True)
        
        # Credential settings
        save_credentials = details.get("save_credentials", False)
        use_windows_cred_manager = details.get("use_windows_cred_manager", True)
        
        # Generate a connection ID for credential storage
        connection_id = f"rdp_{hostname.replace('.', '_')}_{port}"
        
        try:
            # Connect using RemoteAccessManager
            success = self.remote_access_manager.connect_rdp(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                domain=domain,
                connection_id=connection_id,
                use_saved_credentials=True,
                save_credentials=save_credentials,
                fullscreen=fullscreen,
                admin_console=admin_console,
                width=width,
                height=height
            )
            
            if success:
                # Add to recent connections
                self._add_to_recent(name, RDP_CONNECTION_TYPE, details)
                QMessageBox.information(self, "RDP Connection", f"RDP connection to {hostname} initiated.")
            else:
                QMessageBox.warning(self, "RDP Connection", f"Failed to connect to {hostname}.")
        except Exception as e:
            QMessageBox.critical(self, "RDP Connection Error", f"Error connecting to {hostname}: {e}")
    
    def _rename_folder(self, folder_item):
        """Rename a folder."""
        data = folder_item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != FOLDER_TYPE:
            return
            
        current_name = data.get("name", "")
        
        new_name, ok = QInputDialog.getText(
            self, "Rename Folder", "Enter new folder name:", QLineEdit.EchoMode.Normal, current_name
        )
        
        if ok and new_name:
            folder_item.setText(0, new_name)
            folder_item.setData(0, Qt.ItemDataRole.UserRole, {"type": FOLDER_TYPE, "name": new_name})
    
    def _delete_folder(self, folder_item):
        """Delete a folder."""
        data = folder_item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != FOLDER_TYPE:
            return
            
        folder_name = data.get("name", "")
        
        # Check if folder has children
        if folder_item.childCount() > 0:
            if QMessageBox.question(
                self,
                "Delete Folder",
                f"Folder '{folder_name}' contains items. Delete anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) != QMessageBox.StandardButton.Yes:
                return
        
        # Get parent item
        parent = folder_item.parent()
        
        if parent:
            parent.removeChild(folder_item)
        else:
            index = self.tree_widget.indexOfTopLevelItem(folder_item)
            if index >= 0:
                self.tree_widget.takeTopLevelItem(index)
    
    def _edit_connection(self, connection_item):
        """Edit a connection."""
        data = connection_item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        item_type = data.get("type")
        item_name = data.get("name")
        item_data = data.get("data", {})
        
        if item_type == VPN_CONNECTION_TYPE:
            self._edit_vpn_connection(connection_item, item_name, item_data)
        elif item_type == RDP_CONNECTION_TYPE:
            self._edit_rdp_connection(connection_item, item_name, item_data)
    
    def _edit_vpn_connection(self, item, name, profile_data):
        """Edit a VPN connection."""
        dialog = VPNProfileEditDialog(
            parent=self,
            profile_data=profile_data,
            vpn_manager_instance=self.vpn_manager,
            model_manager_instance=self.model_manager,
            icon_storage_dir=os.path.join(self.icon_storage_dir, "vpn_icons")
        )
        
        if dialog.exec():
            try:
                updated_data = dialog.get_profile_data()
                updated_name = updated_data.get("name", "")
                updated_type = updated_data.get("type", "")
                
                # Extract icon_path if present
                icon_path = updated_data.get("icon_path")
                
                # Delete old profile if name changed
                if updated_name != name:
                    self.vpn_manager.delete_profile(name)
                
                # Save the updated profile
                success = False
                if icon_path and os.path.exists(icon_path):
                    success = self.vpn_manager.save_profile(
                        profile_name=updated_name,
                        vpn_type=updated_type,
                        vpn_config=updated_data,
                        icon_path=icon_path
                    )
                else:
                    success = self.vpn_manager.save_profile(
                        profile_name=updated_name,
                        vpn_type=updated_type,
                        vpn_config=updated_data
                    )
                
                if success:
                    # Update recent and favorite connections if name changed
                    if updated_name != name:
                        self._update_connection_references(name, VPN_CONNECTION_TYPE, updated_name)
                    
                    # Reload connections
                    self.load_connections()
                    QMessageBox.information(self, "Success", f"VPN profile '{updated_name}' updated successfully.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to update VPN profile '{updated_name}'.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error updating VPN profile: {e}")
    
    def _edit_rdp_connection(self, item, name, profile_data):
        """Edit an RDP connection."""
        if not self.rdp_profile_manager:
            QMessageBox.warning(self, "Error", "RDP profile manager is not available.")
            return
            
        dialog = RDPEditDialog(
            parent=self,
            profile_data=profile_data,
            icon_storage_dir=os.path.join(self.icon_storage_dir, "rdp_icons")
        )
        
        if dialog.exec():
            try:
                updated_data = dialog.get_profile_data()
                updated_name = updated_data.get("name", "")
                
                # Delete old profile if name changed
                if updated_name != name:
                    self.rdp_profile_manager.delete_profile(name)
                
                # Save the updated profile
                success = self.rdp_profile_manager.save_profile(updated_data)
                
                if success:
                    # Update recent and favorite connections if name changed
                    if updated_name != name:
                        self._update_connection_references(name, RDP_CONNECTION_TYPE, updated_name)
                    
                    # Reload connections
                    self.load_connections()
                    QMessageBox.information(self, "Success", f"RDP profile '{updated_name}' updated successfully.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to update RDP profile '{updated_name}'.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error updating RDP profile: {e}")
    
    def _update_connection_references(self, old_name, conn_type, new_name):
        """Update connection references in recent and favorite lists when a connection is renamed."""
        # Update recent connections
        for conn in self.recent_connections:
            if conn.get("name") == old_name and conn.get("type") == conn_type:
                conn["name"] = new_name
        
        # Update favorite connections
        for conn in self.favorite_connections:
            if conn.get("name") == old_name and conn.get("type") == conn_type:
                conn["name"] = new_name
    
    def _duplicate_connection(self, connection_item):
        """Duplicate a connection."""
        data = connection_item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        item_type = data.get("type")
        item_name = data.get("name")
        item_data = data.get("data", {}).copy()  # Make a copy to avoid modifying original
        
        # Ask for new name
        new_name, ok = QInputDialog.getText(
            self, "Duplicate Connection", "Enter name for the duplicate:", QLineEdit.EchoMode.Normal, f"Copy of {item_name}"
        )
        
        if not ok or not new_name:
            return
        
        # Update name in data
        item_data["name"] = new_name
        
        if item_type == VPN_CONNECTION_TYPE:
            try:
                # Extract icon_path if present
                icon_path = item_data.get("icon_path")
                vpn_type = item_data.get("type", "")
                
                # Save the new profile
                success = False
                if icon_path and os.path.exists(icon_path):
                    success = self.vpn_manager.save_profile(
                        profile_name=new_name,
                        vpn_type=vpn_type,
                        vpn_config=item_data,
                        icon_path=icon_path
                    )
                else:
                    success = self.vpn_manager.save_profile(
                        profile_name=new_name,
                        vpn_type=vpn_type,
                        vpn_config=item_data
                    )
                
                if success:
                    # Add to recent connections
                    self._add_to_recent(new_name, VPN_CONNECTION_TYPE, item_data)
                    # Reload connections
                    self.load_connections()
                    QMessageBox.information(self, "Success", f"VPN profile '{new_name}' created successfully.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to create VPN profile '{new_name}'.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error creating VPN profile: {e}")
        
        elif item_type == RDP_CONNECTION_TYPE:
            if not self.rdp_profile_manager:
                QMessageBox.warning(self, "Error", "RDP profile manager is not available.")
                return
                
            try:
                # Save the new profile
                success = self.rdp_profile_manager.save_profile(item_data)
                
                if success:
                    # Add to recent connections
                    self._add_to_recent(new_name, RDP_CONNECTION_TYPE, item_data)
                    # Reload connections
                    self.load_connections()
                    QMessageBox.information(self, "Success", f"RDP profile '{new_name}' created successfully.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to create RDP profile '{new_name}'.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error creating RDP profile: {e}")
    
    def _delete_connection(self, connection_item):
        """Delete a connection."""
        data = connection_item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        item_type = data.get("type")
        item_name = data.get("name")
        
        # Confirm deletion
        if QMessageBox.question(
            self,
            "Delete Connection",
            f"Are you sure you want to delete the {item_type.upper()} connection '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        
        success = False
        
        if item_type == VPN_CONNECTION_TYPE:
            try:
                success = self.vpn_manager.delete_profile(item_name)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting VPN profile: {e}")
        
        elif item_type == RDP_CONNECTION_TYPE:
            if not self.rdp_profile_manager:
                QMessageBox.warning(self, "Error", "RDP profile manager is not available.")
                return
                
            try:
                success = self.rdp_profile_manager.delete_profile(item_name)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting RDP profile: {e}")
        
        if success:
            # Remove from recent and favorite connections
            self.recent_connections = [
                conn for conn in self.recent_connections
                if not (conn.get("name") == item_name and conn.get("type") == item_type)
            ]
            
            self.favorite_connections = [
                conn for conn in self.favorite_connections
                if not (conn.get("name") == item_name and conn.get("type") == item_type)
            ]
            
            # Reload connections
            self.load_connections()
            QMessageBox.information(self, "Success", f"{item_type.upper()} profile '{item_name}' deleted successfully.")
        else:
            QMessageBox.warning(self, "Error", f"Failed to delete {item_type.upper()} profile '{item_name}'.")
