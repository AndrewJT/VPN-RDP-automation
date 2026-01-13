import os
import sys
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QApplication, QMessageBox, QFileDialog, QLabel
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QAction

# Import custom components using absolute imports
try:
    # Add parent directory to path if running as script
    if __name__ == "__main__":
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    
    from vpn_auto_app_final_may20_v3.src.ui.components.enhanced_connection_tree import EnhancedConnectionTree
    from vpn_auto_app_final_may20_v3.src.ui.components.connection_properties_panel import ConnectionPropertiesPanel
    from vpn_auto_app_final_may20_v3.src.ui.components.multi_tab_interface import MultiTabConnectionInterface
    from vpn_auto_app_final_may20_v3.src.ui.components.quick_connect_bar import QuickConnectBar
except ImportError as e:
    print(f"Warning: Could not import custom components: {e}")
    # Placeholder imports for testing
    from vpn_auto_app_final_may20_v3.src.ui.connection_tree_widget import ConnectionTreeWidget as EnhancedConnectionTree
    
    class ConnectionPropertiesPanel(QWidget):
        property_changed = pyqtSignal(str, str, object)
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Connection Properties Panel Placeholder"))
        def set_connection(self, connection_data): pass
        
    class MultiTabConnectionInterface(QWidget):
        connection_opened = pyqtSignal(str, str)
        connection_closed = pyqtSignal(str)
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Multi-tab Interface Placeholder"))
        def open_connection(self, connection_id, connection_type, connection_data): pass
        def get_open_connections(self): return []
        def close_all_tabs(self): pass
        
    class QuickConnectBar(QWidget):
        connection_requested = pyqtSignal(str, str)
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QHBoxLayout(self)
            layout.addWidget(QLabel("Quick Connect Bar Placeholder"))
        def add_recent_connection(self, conn_id, name, conn_type): pass
        def set_connections(self, favorites, recents): pass

class IntegratedMainWindow(QMainWindow):
    """Main window with integrated mRemoteNG-inspired features."""
    
    def __init__(self, connection_manager=None, vpn_manager=None, remote_access_manager=None, model_manager=None, parent=None):
        super().__init__(parent)
        
        # Store managers
        self.connection_manager = connection_manager
        self.vpn_manager = vpn_manager
        self.remote_access_manager = remote_access_manager
        self.model_manager = model_manager
        
        # Initialize RDP profile manager if needed
        self.rdp_profile_manager = None
        try:
            from vpn_auto_app_final_may20_v3.src.core.rdp_profile_manager import RDPProfileManager
            rdp_profiles_dir = os.path.join(os.path.dirname(os.path.expanduser("~/.vpn_auto_app")), "rdp_profiles")
            self.rdp_profile_manager = RDPProfileManager(profiles_dir=rdp_profiles_dir)
        except ImportError as e:
            print(f"Warning: Could not initialize RDP profile manager: {e}")
        
        # Set window properties
        self.setWindowTitle("VPN Automation")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize UI
        self._init_ui()
        self._create_menu_bar()
        
        # Status message
        self.statusBar().showMessage("Application initialized")
        
    def _init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Quick connect bar at top
        self.quick_connect_bar = QuickConnectBar()
        self.quick_connect_bar.connection_requested.connect(self._on_quick_connect_requested)
        main_layout.addWidget(self.quick_connect_bar)
        
        # Main splitter for tree and content
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Connection tree on left
        self.connection_tree = EnhancedConnectionTree()
        self.connection_tree.connection_selected.connect(self._on_connection_selected)
        self.connection_tree.connection_activated.connect(self._on_connection_activated)
        self.main_splitter.addWidget(self.connection_tree)
        
        # Right side with tabs and properties
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Multi-tab interface for connections
        self.tab_interface = MultiTabConnectionInterface()
        right_layout.addWidget(self.tab_interface)
        
        self.main_splitter.addWidget(right_widget)
        
        # Set initial splitter sizes
        self.main_splitter.setSizes([300, 900])
        
        main_layout.addWidget(self.main_splitter)
        
    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        new_connection_action = QAction("New Connection", self)
        new_connection_action.triggered.connect(self._new_connection)
        file_menu.addAction(new_connection_action)
        
        new_folder_action = QAction("New Folder", self)
        new_folder_action.triggered.connect(self._new_folder)
        file_menu.addAction(new_folder_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("Import Connections", self)
        import_action.triggered.connect(self._import_connections)
        file_menu.addAction(import_action)
        
        export_action = QAction("Export Connections", self)
        export_action.triggered.connect(self._export_connections)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._refresh_connections)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        expand_all_action = QAction("Expand All", self)
        expand_all_action.triggered.connect(self._expand_all)
        view_menu.addAction(expand_all_action)
        
        collapse_all_action = QAction("Collapse All", self)
        collapse_all_action.triggered.connect(self._collapse_all)
        view_menu.addAction(collapse_all_action)
        
        # Connection menu
        connection_menu = menu_bar.addMenu("Connection")
        
        connect_action = QAction("Connect", self)
        connect_action.triggered.connect(self._connect_selected)
        connection_menu.addAction(connect_action)
        
        disconnect_action = QAction("Disconnect", self)
        disconnect_action.triggered.connect(self._disconnect_selected)
        connection_menu.addAction(disconnect_action)
        
        connection_menu.addSeparator()
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self._edit_selected)
        connection_menu.addAction(edit_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._delete_selected)
        connection_menu.addAction(delete_action)
        
        # Tools menu
        tools_menu = menu_bar.addMenu("Tools")
        
        options_action = QAction("Options", self)
        options_action.triggered.connect(self._show_options)
        tools_menu.addAction(options_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _on_connection_selected(self, connection_id, connection_type, connection_data):
        """Handle connection selection in the tree."""
        # Store the selected connection data for later use
        self.selected_connection = {
            "id": connection_id,
            "type": connection_type,
            "data": connection_data,
            "name": connection_data.get('name', 'Unnamed')
        }
        
        # Update status bar
        self.statusBar().showMessage(f"Selected {connection_type} connection: {connection_data.get('name', 'Unnamed')}")
        
    def _on_connection_activated(self, connection_id, connection_type, connection_data):
        """Handle connection activation (double-click) in the tree."""
        # Store the selected connection
        self.selected_connection = {
            "id": connection_id,
            "type": connection_type,
            "data": connection_data,
            "name": connection_data.get('name', 'Unnamed')
        }
        
        # Connect to the selected connection
        self._connect_selected()
        
        # Open connection in tab interface
        self.tab_interface.open_connection(connection_id, connection_type, connection_data)
        
        # Add to recent connections
        self.quick_connect_bar.add_recent_connection(
            connection_id, 
            connection_data.get("name", "Unnamed"), 
            connection_type
        )
        
        self.statusBar().showMessage(f"Opened {connection_type} connection: {connection_data.get('name', 'Unnamed')}")
        
    def _on_quick_connect_requested(self, connection_id, connection_type):
        """Handle quick connect request."""
        # Look up the connection data based on type
        connection_data = None
        
        if connection_type == "vpn" and self.vpn_manager:
            connection_data = self.vpn_manager.load_profile(connection_id)
            if connection_data:
                self._connect_vpn(connection_id)
        
        elif connection_type == "rdp" and self.rdp_profile_manager:
            connection_data = self.rdp_profile_manager.get_profile(connection_id)
            if connection_data:
                self._connect_rdp(connection_id)
        
        if connection_data:
            self.statusBar().showMessage(f"Connected to {connection_type}: {connection_id}")
        else:
            self.statusBar().showMessage(f"Failed to connect to {connection_type}: {connection_id}")
        
    def _connect_vpn(self, profile_name):
        """Connect to a VPN using the specified profile."""
        if not self.connection_manager:
            QMessageBox.warning(self, "VPN Not Available", "VPN connection management is not available.")
            return False
            
        try:
            if self.connection_manager.connect_vpn(profile_name):
                self.statusBar().showMessage(f"Connected to VPN: {profile_name}")
                return True
            else:
                QMessageBox.critical(self, "Connection Error", f"Failed to connect to VPN '{profile_name}'.")
                return False
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"An error occurred while connecting to VPN: {e}")
            return False
    
    def _connect_rdp(self, profile_name):
        """Connect to an RDP session using the specified profile."""
        if not self.rdp_profile_manager:
            QMessageBox.warning(self, "RDP Not Available", "RDP connection management is not available.")
            return False
            
        profile = self.rdp_profile_manager.get_profile(profile_name)
        if not profile:
            QMessageBox.warning(self, "Profile Not Found", f"RDP profile '{profile_name}' not found.")
            return False
            
        # Extract all parameters from the profile
        hostname = profile.get("hostname", "")
        port = profile.get("port", 3389)
        username = profile.get("username", "")
        password = profile.get("password", "")
        domain = profile.get("domain", "")
        
        # Connect using the remote access manager
        try:
            if not self.remote_access_manager:
                QMessageBox.warning(self, "Remote Access Not Available", "Remote access management is not available.")
                return False
                
            if self.remote_access_manager.connect_rdp(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                domain=domain
            ):
                self.statusBar().showMessage(f"Connected to RDP: {profile_name}")
                return True
            else:
                QMessageBox.critical(self, "Connection Error", f"Failed to connect to RDP '{profile_name}'.")
                return False
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"An error occurred while connecting to RDP: {e}")
            return False
        
    def _new_connection(self):
        """Create a new connection."""
        # In a real implementation, this would open a dialog to create a new connection
        QMessageBox.information(self, "New Connection", "This would open a dialog to create a new connection.")
        
    def _new_folder(self):
        """Create a new folder."""
        # In a real implementation, this would open a dialog to create a new folder
        QMessageBox.information(self, "New Folder", "This would open a dialog to create a new folder.")
        
    def _import_connections(self):
        """Import connections from file."""
        # In a real implementation, this would open a file dialog and import connections
        QMessageBox.information(self, "Import Connections", "This would open a file dialog to import connections.")
        
    def _export_connections(self):
        """Export connections to file."""
        # In a real implementation, this would open a file dialog and export connections
        QMessageBox.information(self, "Export Connections", "This would open a file dialog to export connections.")
        
    def _refresh_connections(self):
        """Refresh the connection tree."""
        # In a real implementation, this would reload connections from storage
        QMessageBox.information(self, "Refresh Connections", "This would reload connections from storage.")
        
    def _expand_all(self):
        """Expand all items in the connection tree."""
        self.connection_tree.expandAll()
        
    def _collapse_all(self):
        """Collapse all items in the connection tree."""
        self.connection_tree.collapseAll()
        
    def _connect_selected(self):
        """Connect to the selected connection."""
        if not hasattr(self, 'selected_connection'):
            QMessageBox.warning(self, "No Selection", "Please select a connection first.")
            return
            
        connection_type = self.selected_connection.get("type")
        connection_id = self.selected_connection.get("id")
        
        if connection_type == "vpn":
            self._connect_vpn(connection_id)
        elif connection_type == "rdp":
            self._connect_rdp(connection_id)
        else:
            QMessageBox.warning(self, "Unknown Connection Type", f"Unknown connection type: {connection_type}")
        
    def _disconnect_selected(self):
        """Disconnect the selected connection."""
        if not hasattr(self, 'selected_connection'):
            QMessageBox.warning(self, "No Selection", "Please select a connection first.")
            return
            
        connection_type = self.selected_connection.get("type")
        connection_id = self.selected_connection.get("id")
        
        if connection_type == "vpn" and self.connection_manager:
            try:
                if self.connection_manager.disconnect_vpn(connection_id):
                    self.statusBar().showMessage(f"Disconnected from VPN: {connection_id}")
                else:
                    QMessageBox.critical(self, "Disconnection Error", f"Failed to disconnect from VPN '{connection_id}'.")
            except Exception as e:
                QMessageBox.critical(self, "Disconnection Error", f"An error occurred while disconnecting from VPN: {e}")
        else:
            QMessageBox.warning(self, "Disconnect Not Supported", f"Disconnect not supported for {connection_type} connections.")
        
    def _edit_selected(self):
        """Edit the selected connection."""
        if not hasattr(self, 'selected_connection'):
            QMessageBox.warning(self, "No Selection", "Please select a connection first.")
            return
            
        connection_type = self.selected_connection.get("type")
        connection_id = self.selected_connection.get("id")
        connection_data = self.selected_connection.get("data", {})
        
        if connection_type == "vpn":
            # Open VPN profile editor
            try:
                from vpn_auto_app_final_may20_v3.src.ui.vpn_profile_edit_dialog import VPNProfileEditDialog
                dialog = VPNProfileEditDialog(parent=self, profile_data=connection_data)
                if dialog.exec():
                    updated_data = dialog.get_profile_data()
                    # Save updated profile
                    if self.vpn_manager:
                        self.vpn_manager.save_profile(connection_id, updated_data)
                        self.statusBar().showMessage(f"Updated VPN profile: {connection_id}")
                        # Refresh connection tree
                        self._refresh_connections()
                    else:
                        QMessageBox.warning(self, "VPN Manager Not Available", "VPN profile manager is not available.")
            except ImportError as e:
                QMessageBox.critical(self, "Import Error", f"Could not import VPN profile editor: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Edit Error", f"An error occurred while editing VPN profile: {e}")
                
        elif connection_type == "rdp":
            # Open RDP profile editor
            try:
                from vpn_auto_app_final_may20_v3.src.ui.rdp_edit_dialog import RDPEditDialog
                dialog = RDPEditDialog(parent=self, profile_data=connection_data)
                if dialog.exec():
                    updated_data = dialog.get_profile_data()
                    # Save updated profile
                    if self.rdp_profile_manager:
                        self.rdp_profile_manager.save_profile(connection_id, updated_data)
                        self.statusBar().showMessage(f"Updated RDP profile: {connection_id}")
                        # Refresh connection tree
                        self._refresh_connections()
                    else:
                        QMessageBox.warning(self, "RDP Manager Not Available", "RDP profile manager is not available.")
            except ImportError as e:
                QMessageBox.critical(self, "Import Error", f"Could not import RDP profile editor: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Edit Error", f"An error occurred while editing RDP profile: {e}")
        else:
            QMessageBox.warning(self, "Edit Not Supported", f"Edit not supported for {connection_type} connections.")
        
    def _delete_selected(self):
        """Delete the selected connection."""
        if not hasattr(self, 'selected_connection'):
            QMessageBox.warning(self, "No Selection", "Please select a connection first.")
            return
            
        connection_type = self.selected_connection.get("type")
        connection_id = self.selected_connection.get("id")
        connection_name = self.selected_connection.get("name", "Unnamed")
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            f"Are you sure you want to delete the {connection_type} connection '{connection_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if connection_type == "vpn" and self.vpn_manager:
                try:
                    if self.vpn_manager.delete_profile(connection_id):
                        self.statusBar().showMessage(f"Deleted VPN profile: {connection_id}")
                        # Refresh connection tree
                        self._refresh_connections()
                    else:
                        QMessageBox.critical(self, "Deletion Error", f"Failed to delete VPN profile '{connection_id}'.")
                except Exception as e:
                    QMessageBox.critical(self, "Deletion Error", f"An error occurred while deleting VPN profile: {e}")
            elif connection_type == "rdp" and self.rdp_profile_manager:
                try:
                    if self.rdp_profile_manager.delete_profile(connection_id):
                        self.statusBar().showMessage(f"Deleted RDP profile: {connection_id}")
                        # Refresh connection tree
                        self._refresh_connections()
                    else:
                        QMessageBox.critical(self, "Deletion Error", f"Failed to delete RDP profile '{connection_id}'.")
                except Exception as e:
                    QMessageBox.critical(self, "Deletion Error", f"An error occurred while deleting RDP profile: {e}")
            else:
                QMessageBox.warning(self, "Delete Not Supported", f"Delete not supported for {connection_type} connections.")
        
    def _show_options(self):
        """Show options dialog."""
        try:
            from vpn_auto_app_final_may20_v3.src.ui.settings_dialog import SettingsDialog
            dialog = SettingsDialog(parent=self)
            if dialog.exec():
                settings = dialog.get_settings()
                self.statusBar().showMessage("Settings updated")
                # Apply settings
                self._apply_settings(settings)
        except ImportError as e:
            QMessageBox.critical(self, "Import Error", f"Could not import settings dialog: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Settings Error", f"An error occurred while showing settings: {e}")
        
    def _apply_settings(self, settings):
        """Apply settings to the application."""
        # Apply theme
        theme = settings.get("theme", "dark")
        self._set_theme(theme)
        
    def _set_theme(self, theme):
        """Set application theme."""
        # In a real implementation, this would apply the theme to all widgets
        self.statusBar().showMessage(f"Theme set to {theme}")
        
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, 
            "About VPN Automation", 
            "VPN Automation Application\n\nVersion 1.0.0\n\n© 2025 All Rights Reserved"
        )
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Confirm Exit", 
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Close all connections
            self.tab_interface.close_all_tabs()
            
            # Accept the event
            event.accept()
        else:
            # Ignore the event
            event.ignore()

def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    
    # Initialize managers in the correct order
    vpn_manager = None
    connection_manager = None
    remote_access_manager = None
    model_manager = None
    
    try:
        from vpn_auto_app_final_may20_v3.src.vcal.vpn_manager import VPNManager
        vpn_manager = VPNManager()
        print("VPN Manager initialized successfully")
    except ImportError as e:
        print(f"Warning: Could not initialize VPN manager: {e}")
    
    try:
        from vpn_auto_app_final_may20_v3.src.core.connection_manager import ConnectionManager
        # Pass vpn_manager to ConnectionManager as required
        if vpn_manager:
            connection_manager = ConnectionManager(vpn_manager=vpn_manager)
            print("Connection Manager initialized successfully")
        else:
            print("Warning: Cannot initialize ConnectionManager without VPNManager")
    except ImportError as e:
        print(f"Warning: Could not initialize connection manager: {e}")
        
    try:
        from vpn_auto_app_final_may20_v3.src.core.remote_access_manager import RemoteAccessManager
        remote_access_manager = RemoteAccessManager()
        print("Remote Access Manager initialized successfully")
    except ImportError as e:
        print(f"Warning: Could not initialize remote access manager: {e}")
        
    try:
        from vpn_auto_app_final_may20_v3.src.models.vpn_model_manager import VPNModelManager
        model_manager = VPNModelManager()
        print("VPN Model Manager initialized successfully")
    except ImportError as e:
        print(f"Warning: Could not initialize model manager: {e}")
    
    # Create and show the main window
    window = IntegratedMainWindow(
        connection_manager=connection_manager,
        vpn_manager=vpn_manager,
        remote_access_manager=remote_access_manager,
        model_manager=model_manager
    )
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
