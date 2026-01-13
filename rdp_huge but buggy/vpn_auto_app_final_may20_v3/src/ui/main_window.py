import json
import os
import logging
from typing import Optional, Dict, Any, List, Tuple

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QMessageBox, QDialog, QTabWidget, 
    QStackedWidget, QMenu, QMenuBar, QStatusBar, QFileDialog, QInputDialog,
    QLineEdit, QComboBox, QCheckBox, QGroupBox, QRadioButton, QTextEdit,
    QScrollArea, QSplitter, QFrame, QToolBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QTimer, QSettings, QUrl, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPalette, QColor, QFont, QAction

# Import connection tree widget
try:
    from .connection_tree_widget import ConnectionTreeWidget
    from .settings_dialog import SettingsDialog, CONFIG_FILE as APP_CONFIG_FILE, DEFAULT_PROFILE_DIR, DEFAULT_ICON_DIR
    from .visual_config_dialog import VisualConfigDialog
    from ..core.connection_manager import ConnectionManager
    from ..core.remote_access_manager import RemoteAccessManager
    from ..vcal.vpn_manager import VPNManager
    from ..models.vpn_model_manager import VPNModelManager
    from .components.zoom_control import ZoomManager, ZoomControlWidget
except ImportError as e:
    print(f"Warning: Could not import required modules: {e}")
    # Define placeholder classes for testing UI in isolation
    class ConnectionTreeWidget(QWidget):
        connection_selected = pyqtSignal(str, str)
        def __init__(self, vpn_manager=None, model_manager=None, icon_storage_dir=None, parent=None):
            super().__init__(parent)
            self.setMinimumHeight(300)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Connection Tree Widget Placeholder"))
            
    class SettingsDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            
    class VisualConfigDialog(QDialog):
        def __init__(self, parent=None, profile_data=None, automation_engine=None):
            super().__init__(parent)
            
    class ConnectionManager:
        def __init__(self, vpn_manager=None, remote_access_manager=None):
            pass
        def connect_vpn(self, profile_name):
            return True
        def disconnect_vpn(self):
            return True
            
    class RemoteAccessManager:
        def __init__(self):
            pass
        def connect_rdp(self, hostname, port=3389, username=None, password=None, domain=None):
            return True
            
    class VPNManager:
        def __init__(self, config_dir):
            self.config_dir = config_dir
        def get_all_profiles(self):
            return []
        def get_profile_types(self):
            return ["forticlient", "globalprotect"]
            
    class VPNModelManager:
        def __init__(self, models_dir):
            self.models_dir = models_dir
        def list_models(self):
            return []
            
    class ZoomManager:
        def __init__(self):
            self.zoom_factor = 1.0
        def get_zoom_factor(self):
            return self.zoom_factor
        def set_zoom_factor(self, factor):
            self.zoom_factor = factor
            
    class ZoomControlWidget(QWidget):
        zoom_changed = pyqtSignal(float)
        def __init__(self, parent=None):
            super().__init__(parent)
            
    APP_CONFIG_FILE = "app_config.json"
    DEFAULT_PROFILE_DIR = os.path.expanduser("~/.vpn_auto_app/profiles")
    DEFAULT_ICON_DIR = os.path.expanduser("~/.vpn_auto_app/icons")

# Constants
APP_NAME = "VPN Automation"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Manus AI"
APP_WEBSITE = "https://example.com"
APP_DESCRIPTION = "Automate VPN connections and remote access"

# Main window views
VIEW_DASHBOARD = "dashboard"
VIEW_VPN_MANAGEMENT = "vpn_management"
VIEW_RDP_MANAGEMENT = "rdp_management"
VIEW_SETTINGS = "settings"
VIEW_HELP = "help"

class MainWindow(QMainWindow):
    def __init__(self, connection_manager=None, parent=None):
        super().__init__(parent)
        
        # Initialize managers
        self.connection_manager = connection_manager
        if self.connection_manager:
            self.vpn_manager = self.connection_manager.vpn_manager
            self.remote_access_manager = self.connection_manager.remote_access_manager
        else:
            # Create dummy managers for UI testing
            self.vpn_manager = VPNManager(config_dir=DEFAULT_PROFILE_DIR)
            self.remote_access_manager = RemoteAccessManager()
            self.connection_manager = ConnectionManager(
                vpn_manager=self.vpn_manager,
                remote_access_manager=self.remote_access_manager
            )
            
        # Initialize model manager
        models_dir = os.path.join(os.path.dirname(DEFAULT_PROFILE_DIR), "models")
        os.makedirs(models_dir, exist_ok=True)
        self.model_manager = VPNModelManager(models_dir=models_dir)
        
        # Initialize zoom manager
        self.zoom_manager = ZoomManager()
        
        # Load application settings
        self.app_settings = self._load_app_settings()
        
        # Set up UI
        self.setWindowTitle(APP_NAME)
        self.setGeometry(100, 100, 1000, 700)  # Larger window for tree view
        self.current_theme = self.app_settings.get("theme", "dark")
        
        # Initialize UI components
        self._init_ui()
        self._create_menu_bar()
        self.apply_stylesheet()
        
        # Set theme to blue (renamed from dark)
        self.current_theme = "dark"  # This is the blue theme
        self.app_settings["theme"] = "dark"
        self.apply_stylesheet()
        
        # Apply initial zoom
        self._apply_zoom(self.zoom_manager.get_zoom_factor())
        
        # Set initial view
        self._show_dashboard()
        
        # Status message
        self.statusBar().showMessage("Application initialized")
        
    def _init_ui(self):
        # Central widget with stacked layout for different views
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for different views
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Create different views
        self._create_dashboard_view()
        self._create_vpn_management_view()
        self._create_rdp_management_view()
        self._create_settings_view()
        self._create_help_view()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
    def _create_dashboard_view(self):
        """Create the main dashboard view with connection tree."""
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        
        # Header
        header_label = QLabel("VPN Automation Dashboard")
        header_label.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dashboard_layout.addWidget(header_label)
        
        # Initialize RDP profile manager if needed
        rdp_profiles_dir = os.path.join(os.path.dirname(self.app_settings.get("profile_dir", DEFAULT_PROFILE_DIR)), "rdp_profiles")
        os.makedirs(rdp_profiles_dir, exist_ok=True)
        
        try:
            from ..core.rdp_profile_manager import RDPProfileManager
            rdp_profile_manager = RDPProfileManager(profiles_dir=rdp_profiles_dir)
        except ImportError:
            rdp_profile_manager = None
        
        # Connection tree widget
        self.connection_tree = ConnectionTreeWidget(
            vpn_manager=self.vpn_manager,
            model_manager=self.model_manager,
            rdp_profile_manager=rdp_profile_manager,
            icon_storage_dir=self.app_settings.get("icon_dir", DEFAULT_ICON_DIR)
        )
        self.connection_tree.connection_selected.connect(self._on_connection_selected)
        dashboard_layout.addWidget(self.connection_tree)
        
        # Connection status
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Not connected")
        status_layout.addWidget(self.status_label)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("background-color: #0078d7; color: white;")
        self.connect_button.clicked.connect(self._connect_selected)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setStyleSheet("background-color: #0078d7; color: white;")
        self.disconnect_button.clicked.connect(self._disconnect)
        self.disconnect_button.setEnabled(False)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.connect_button)
        buttons_layout.addWidget(self.disconnect_button)
        status_layout.addLayout(buttons_layout)
        
        dashboard_layout.addWidget(status_group)
        
        # Add to stacked widget
        self.stacked_widget.addWidget(dashboard_widget)
        
    def _create_vpn_management_view(self):
        """Create the VPN management view."""
        vpn_widget = QWidget()
        vpn_layout = QVBoxLayout(vpn_widget)
        
        # Import VPN management widget
        try:
            from .vpn_management_widget import VPNManagementWidget
            
            # Create and add the VPN management widget
            self.vpn_management_widget = VPNManagementWidget(
                vpn_manager=self.vpn_manager,
                model_manager=self.model_manager,
                icon_storage_dir=os.path.join(self.app_settings.get("icon_dir", DEFAULT_ICON_DIR), "vpn_icons")
            )
            vpn_layout.addWidget(self.vpn_management_widget)
            
        except ImportError as e:
            # Fallback if import fails
            print(f"Error importing VPN management widget: {e}")
            header_label = QLabel("VPN Connection Management")
            header_label.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vpn_layout.addWidget(header_label)
            
            error_label = QLabel(f"Could not load VPN management interface: {e}")
            error_label.setStyleSheet("color: red;")
            vpn_layout.addWidget(error_label)
        
        # Add to stacked widget
        self.stacked_widget.addWidget(vpn_widget)
        
    def _create_rdp_management_view(self):
        """Create the RDP management view."""
        rdp_widget = QWidget()
        rdp_layout = QVBoxLayout(rdp_widget)
        
        # Import RDP management widget
        try:
            from .rdp_management_widget import RDPManagementWidget
            from ..core.rdp_profile_manager import RDPProfileManager
            
            # Initialize RDP profile manager if not already done
            rdp_profiles_dir = os.path.join(os.path.dirname(self.app_settings.get("profile_dir", DEFAULT_PROFILE_DIR)), "rdp_profiles")
            os.makedirs(rdp_profiles_dir, exist_ok=True)
            rdp_profile_manager = RDPProfileManager(profiles_dir=rdp_profiles_dir)
            
            # Create and add the RDP management widget
            self.rdp_management_widget = RDPManagementWidget(
                rdp_profile_manager=rdp_profile_manager,
                remote_access_manager=self.remote_access_manager,
                icon_storage_dir=os.path.join(self.app_settings.get("icon_dir", DEFAULT_ICON_DIR), "rdp_icons")
            )
            rdp_layout.addWidget(self.rdp_management_widget)
            
        except ImportError as e:
            # Fallback if import fails
            print(f"Error importing RDP management widget: {e}")
            header_label = QLabel("RDP Connection Management")
            header_label.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rdp_layout.addWidget(header_label)
            
            error_label = QLabel(f"Could not load RDP management interface: {e}")
            error_label.setStyleSheet("color: red;")
            rdp_layout.addWidget(error_label)
        
        # Add to stacked widget
        self.stacked_widget.addWidget(rdp_widget)
        
    def _create_settings_view(self):
        """Create the settings view."""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        header_label = QLabel("Application Settings")
        header_label.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(header_label)
        
        # Settings tabs
        settings_tabs = QTabWidget()
        
        # Appearance tab
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        self.light_theme_radio = QRadioButton("Light")
        self.dark_theme_radio = QRadioButton("Dark")
        
        if self.current_theme == "light":
            self.light_theme_radio.setChecked(True)
        else:
            self.dark_theme_radio.setChecked(True)
            
        self.light_theme_radio.toggled.connect(lambda: self._change_theme("light"))
        self.dark_theme_radio.toggled.connect(lambda: self._change_theme("dark"))
        
        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        
        appearance_layout.addWidget(theme_group)
        appearance_layout.addStretch()
        
        # Paths tab
        paths_tab = QWidget()
        paths_layout = QVBoxLayout(paths_tab)
        
        profile_dir_group = QGroupBox("Profile Directory")
        profile_dir_layout = QHBoxLayout(profile_dir_group)
        
        self.profile_dir_edit = QLineEdit(self.app_settings.get("profile_dir", DEFAULT_PROFILE_DIR))
        self.profile_dir_edit.setReadOnly(True)
        
        profile_dir_browse = QPushButton("Browse...")
        profile_dir_browse.clicked.connect(self._browse_profile_dir)
        
        profile_dir_layout.addWidget(self.profile_dir_edit)
        profile_dir_layout.addWidget(profile_dir_browse)
        
        icon_dir_group = QGroupBox("Icon Directory")
        icon_dir_layout = QHBoxLayout(icon_dir_group)
        
        self.icon_dir_edit = QLineEdit(self.app_settings.get("icon_dir", DEFAULT_ICON_DIR))
        self.icon_dir_edit.setReadOnly(True)
        
        icon_dir_browse = QPushButton("Browse...")
        icon_dir_browse.clicked.connect(self._browse_icon_dir)
        
        icon_dir_layout.addWidget(self.icon_dir_edit)
        icon_dir_layout.addWidget(icon_dir_browse)
        
        paths_layout.addWidget(profile_dir_group)
        paths_layout.addWidget(icon_dir_group)
        paths_layout.addStretch()
        
        # About tab (moved from Help menu)
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml(f"""
        <h1>{APP_NAME}</h1>
        <p><b>Version:</b> {APP_VERSION}</p>
        <p><b>Author:</b> {APP_AUTHOR}</p>
        <p><b>Website:</b> <a href="{APP_WEBSITE}">{APP_WEBSITE}</a></p>
        <p>{APP_DESCRIPTION}</p>
        <h2>Help</h2>
        <p>This application helps you automate VPN connections and remote access.</p>
        <p>Use the connection tree to organize and manage your VPN and RDP connections.</p>
        <p>Double-click a connection to connect to it, or use the context menu for more options.</p>
        <p>Use the quick connect bar to quickly connect to recent or favorite connections.</p>
        """)
        
        about_layout.addWidget(about_text)
        
        # Add tabs
        settings_tabs.addTab(appearance_tab, "Appearance")
        settings_tabs.addTab(paths_tab, "Paths")
        settings_tabs.addTab(about_tab, "About & Help")
        
        settings_layout.addWidget(settings_tabs)
        
        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self._save_settings)
        settings_layout.addWidget(save_button)
        
        # Add to stacked widget
        self.stacked_widget.addWidget(settings_widget)
        
    def _create_help_view(self):
        """Create the help view - now integrated into Settings."""
        # This view is no longer needed as help is integrated into Settings
        # We'll keep a minimal implementation for backward compatibility
        help_widget = QWidget()
        help_layout = QVBoxLayout(help_widget)
        
        redirect_label = QLabel("Help information is now available in the Settings → About & Help tab.")
        redirect_label.setStyleSheet("font-size: 14pt; margin: 20px;")
        redirect_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_layout.addWidget(redirect_label)
        
        go_to_settings = QPushButton("Go to Settings")
        go_to_settings.clicked.connect(self._show_settings)
        help_layout.addWidget(go_to_settings, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add to stacked widget
        self.stacked_widget.addWidget(help_widget)
        
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("View")
        
        dashboard_action = QAction("Dashboard", self)
        dashboard_action.triggered.connect(self._show_dashboard)
        view_menu.addAction(dashboard_action)
        
        view_menu.addSeparator()
        
        vpn_management_action = QAction("VPN Connections", self)
        vpn_management_action.triggered.connect(self._show_vpn_management)
        view_menu.addAction(vpn_management_action)
        
        rdp_management_action = QAction("RDP Connections", self)
        rdp_management_action.triggered.connect(self._show_rdp_management)
        view_menu.addAction(rdp_management_action)
        
        view_menu.addSeparator()
        
        # Zoom submenu
        zoom_menu = view_menu.addMenu("Zoom")
        
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self._zoom_in)
        zoom_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self._zoom_out)
        zoom_menu.addAction(zoom_out_action)
        
        zoom_reset_action = QAction("Reset Zoom", self)
        zoom_reset_action.setShortcut("Ctrl+0")
        zoom_reset_action.triggered.connect(self._zoom_reset)
        zoom_menu.addAction(zoom_reset_action)
        
        zoom_menu.addSeparator()
        
        zoom_settings_action = QAction("Zoom Settings...", self)
        zoom_settings_action.triggered.connect(self._show_zoom_settings)
        zoom_menu.addAction(zoom_settings_action)
        
        # Settings menu (moved from View menu)
        settings_menu = menu_bar.addMenu("Settings")
        
        app_settings_action = QAction("Application Settings", self)
        app_settings_action.triggered.connect(self._show_settings)
        settings_menu.addAction(app_settings_action)
        
    def _show_dashboard(self):
        """Switch to the dashboard view."""
        self.stacked_widget.setCurrentIndex(0)
        self.statusBar().showMessage("Dashboard view")
        
    def _show_vpn_management(self):
        """Switch to the VPN management view."""
        self.stacked_widget.setCurrentIndex(1)
        self.statusBar().showMessage("VPN Management view")
        
    def _show_rdp_management(self):
        """Switch to the RDP management view."""
        self.stacked_widget.setCurrentIndex(2)
        self.statusBar().showMessage("RDP Management view")
        
    def _show_settings(self):
        """Switch to the settings view."""
        self.stacked_widget.setCurrentIndex(3)
        self.statusBar().showMessage("Settings view")
        
    def _show_help(self):
        """Switch to the help view."""
        self.stacked_widget.setCurrentIndex(4)
        self.statusBar().showMessage("Help view")
        
    def _on_connection_selected(self, name, conn_type):
        """Handle connection selection from the tree."""
        self.statusBar().showMessage(f"Selected {conn_type.upper()} connection: {name}")
        self.connect_button.setEnabled(True)
        
        # Store the selected connection info
        self.selected_connection = {
            "name": name,
            "type": conn_type
        }
        
    def _connect_selected(self):
        """Connect to the selected connection."""
        if not hasattr(self, 'selected_connection'):
            QMessageBox.warning(self, "No Selection", "Please select a connection first.")
            return
            
        name = self.selected_connection.get("name")
        conn_type = self.selected_connection.get("type")
        
        if not name or not conn_type:
            return
            
        try:
            self.status_label.setText(f"Connecting to {conn_type.upper()} {name}...")
            
            if conn_type == "vpn":
                # Connect to VPN
                if self.connection_manager.connect_vpn(name):
                    self._update_connection_status(f"Connected to VPN: {name}")
                    self.disconnect_button.setEnabled(True)
                    self.connect_button.setEnabled(False)
                else:
                    QMessageBox.critical(self, "Connection Error", f"Failed to connect to VPN '{name}'.")
                    self._update_connection_status("Connection failed")
            
            elif conn_type == "rdp":
                # Connect to RDP
                # Get RDP profile data
                rdp_profiles_dir = os.path.join(os.path.dirname(self.app_settings.get("profile_dir", DEFAULT_PROFILE_DIR)), "rdp_profiles")
                try:
                    from ..core.rdp_profile_manager import RDPProfileManager
                    rdp_profile_manager = RDPProfileManager(profiles_dir=rdp_profiles_dir)
                    profile = rdp_profile_manager.get_profile(name)
                    
                    if profile:
                        hostname = profile.get("hostname", "")
                        port = profile.get("port", 3389)
                        username = profile.get("username", "")
                        password = profile.get("password", "")
                        domain = profile.get("domain", "")
                        
                        # Ensure all parameters are passed to connect_rdp
                        if self.remote_access_manager.connect_rdp(
                            hostname=hostname,
                            port=port,
                            username=username,
                            password=password,
                            domain=domain
                        ):
                            self._update_connection_status(f"Connected to RDP: {name}")
                            self.disconnect_button.setEnabled(True)
                            self.connect_button.setEnabled(False)
                        else:
                            QMessageBox.critical(self, "Connection Error", f"Failed to connect to RDP '{name}'.")
                            self._update_connection_status("Connection failed")
                    else:
                        QMessageBox.critical(self, "Profile Error", f"Could not find RDP profile '{name}'.")
                        self._update_connection_status("Connection failed")
                        
                except ImportError as e:
                    QMessageBox.critical(self, "RDP Not Available", f"RDP connection management is not available: {e}")
                    self._update_connection_status("Connection failed")
            
            else:
                QMessageBox.warning(self, "Unknown Connection Type", f"Unknown connection type: {conn_type}")
                self._update_connection_status("Connection failed")
                
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {e}")
            self._update_connection_status("Connection failed")
            
    def _disconnect(self):
        """Disconnect the current connection."""
        try:
            if not hasattr(self, 'selected_connection'):
                QMessageBox.warning(self, "No Connection", "No active connection to disconnect.")
                return
                
            name = self.selected_connection.get("name")
            conn_type = self.selected_connection.get("type")
            
            if not name or not conn_type:
                return
                
            self.status_label.setText(f"Disconnecting from {conn_type.upper()} {name}...")
            
            if conn_type == "vpn":
                # Disconnect from VPN
                if self.connection_manager.disconnect_vpn():
                    self._update_connection_status("Not connected")
                    self.disconnect_button.setEnabled(False)
                    self.connect_button.setEnabled(True)
                else:
                    QMessageBox.critical(self, "Disconnection Error", f"Failed to disconnect from VPN '{name}'.")
            
            elif conn_type == "rdp":
                # For RDP, just update the UI as the RDP client window is separate
                self._update_connection_status("Not connected")
                self.disconnect_button.setEnabled(False)
                self.connect_button.setEnabled(True)
                
            else:
                QMessageBox.warning(self, "Unknown Connection Type", f"Unknown connection type: {conn_type}")
                
        except Exception as e:
            QMessageBox.critical(self, "Disconnection Error", f"Failed to disconnect: {e}")
            
    def _update_connection_status(self, status):
        """Update the connection status label."""
        self.status_label.setText(status)
        self.statusBar().showMessage(f"Connection status: {status}")
        
    def _load_app_settings(self):
        """Load application settings from config file."""
        config_path = os.path.join(os.path.expanduser("~"), ".vpn_auto_app", APP_CONFIG_FILE)
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading app settings: {e}")
                
        # Default settings
        return {
            "theme": "dark",
            "profile_dir": DEFAULT_PROFILE_DIR,
            "icon_dir": DEFAULT_ICON_DIR
        }
        
    def _save_settings(self):
        """Save application settings."""
        # Update settings from UI
        self.app_settings["profile_dir"] = self.profile_dir_edit.text()
        self.app_settings["icon_dir"] = self.icon_dir_edit.text()
        
        # Save to file
        config_dir = os.path.join(os.path.expanduser("~"), ".vpn_auto_app")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, APP_CONFIG_FILE)
        
        try:
            with open(config_path, "w") as f:
                json.dump(self.app_settings, f, indent=4)
            QMessageBox.information(self, "Settings Saved", "Application settings have been saved.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save settings: {e}")
            
    def _browse_profile_dir(self):
        """Browse for profile directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Profile Directory", self.profile_dir_edit.text())
        if dir_path:
            self.profile_dir_edit.setText(dir_path)
            
    def _browse_icon_dir(self):
        """Browse for icon directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Icon Directory", self.icon_dir_edit.text())
        if dir_path:
            self.icon_dir_edit.setText(dir_path)
            
    def _change_theme(self, theme):
        """Change application theme."""
        if theme == self.current_theme:
            return
            
        self.current_theme = theme
        self.app_settings["theme"] = theme
        self.apply_stylesheet()
        
        # Force update of all widgets to ensure theme is fully applied
        self.repaint()
        for widget in self.findChildren(QWidget):
            widget.repaint()
        
    def apply_stylesheet(self):
        """Apply stylesheet based on current theme."""
        if self.current_theme == "light":
            self.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #f0f0f0;
                color: #333333;
            }
            QLabel {
                color: #333333;
            }
            QPushButton {
                background-color: #0078d7;
                border: 1px solid #0067b8;
                border-radius: 4px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1a88e0;
            }
            QPushButton:pressed {
                background-color: #006cc1;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #ffffff;
                border: 1px solid #b0b0b0;
                border-radius: 4px;
                padding: 3px;
                color: #333333;
            }
            QGroupBox {
                border: 1px solid #b0b0b0;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                color: #333333;
            }
            """)
        else:  # blue theme (renamed from dark theme)
            self.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #2d2d2d;
                color: #f0f0f0;
            }
            QLabel {
                color: #f0f0f0;
            }
            QPushButton {
                background-color: #0078d7;
                border: 1px solid #0067b8;
                border-radius: 4px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #1a88e0;
            }
            QPushButton:pressed {
                background-color: #006cc1;
            }
            QTabWidget::pane {
                border: 1px solid #5d5d5d;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #3d3d3d;
                color: #f0f0f0;
                border: 1px solid #5d5d5d;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 5px 10px;
            }
            QTabBar::tab:selected {
                background-color: #0078d7;
            }
            QTabBar::tab:hover:!selected {
                background-color: #4d4d4d;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #5d5d5d;
                border-radius: 4px;
                padding: 3px;
                color: #f0f0f0;
            }
            QGroupBox {
                border: 1px solid #5d5d5d;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                color: #f0f0f0;
            }
            """)
            
    # Zoom functionality
    def _apply_zoom(self, factor):
        """Apply zoom factor to all widgets in the application."""
        # Store the zoom factor
        current_factor = self.zoom_manager.get_zoom_factor()
        new_factor = self.zoom_manager.set_zoom_factor(factor)
        
        # Calculate the relative change for font adjustment
        relative_change = new_factor / current_factor if current_factor > 0 else 1.0
        
        # Apply to application font
        app_font = self.font()
        app_font.setPointSizeF(app_font.pointSizeF() * relative_change)
        self.setFont(app_font)
        
        # Apply to all child widgets recursively
        self._apply_zoom_to_widget(self, relative_change)
        
        # Update status bar
        self.statusBar().showMessage(f"Zoom level: {int(new_factor * 100)}%", 3000)
        
        # Force update of all widgets
        self.central_widget.update()
        
    def _apply_zoom_to_widget(self, widget, factor):
        """Recursively apply zoom to a widget and all its children."""
        # Apply to this widget's font
        font = widget.font()
        font.setPointSizeF(font.pointSizeF() * factor)
        widget.setFont(font)
        
        # Apply to all children
        for child in widget.findChildren(QWidget):
            if child.parent() == widget:  # Only direct children
                self._apply_zoom_to_widget(child, factor)
        
    def _zoom_in(self):
        """Increase zoom level."""
        current_zoom = self.zoom_manager.get_zoom_factor()
        new_zoom = min(current_zoom + 0.1, 2.0)  # Max 200%
        self._apply_zoom(new_zoom)
        
    def _zoom_out(self):
        """Decrease zoom level."""
        current_zoom = self.zoom_manager.get_zoom_factor()
        new_zoom = max(current_zoom - 0.1, 0.5)  # Min 50%
        self._apply_zoom(new_zoom)
        
    def _zoom_reset(self):
        """Reset zoom to 100%."""
        self._apply_zoom(1.0)
        
    def _show_zoom_settings(self):
        """Show zoom settings dialog."""
        from .components.zoom_control import ZoomSettingsDialog
        dialog = ZoomSettingsDialog(self.zoom_manager, self)
        dialog.zoom_changed.connect(self._apply_zoom)
        dialog.exec()
        
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming with Ctrl+scroll."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_in()
            elif delta < 0:
                self._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
