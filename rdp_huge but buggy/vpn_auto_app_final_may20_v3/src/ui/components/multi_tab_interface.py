import os
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton,
    QSplitter, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QAction

# Import custom components
try:
    from .components.connection_properties_panel import ConnectionPropertiesPanel
except ImportError as e:
    print(f"Warning: Could not import ConnectionPropertiesPanel: {e}")
    # Placeholder class if import fails
    class ConnectionPropertiesPanel(QWidget):
        property_changed = pyqtSignal(str, str, object)
        def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Connection Properties Panel Placeholder"))
        def set_connection(self, connection_data): pass

class MultiTabConnectionInterface(QWidget):
    """Multi-tab interface for managing multiple open connections."""
    
    connection_opened = pyqtSignal(str, str)  # connection_id, connection_type
    connection_closed = pyqtSignal(str)  # connection_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.open_connections = {}  # Dictionary of open connection tabs
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter for tabs and properties panel
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Tab widget for connections
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Add "+" button for new tab
        self.tab_widget.setCornerWidget(self._create_corner_widget())
        
        # Properties panel
        self.properties_panel = ConnectionPropertiesPanel()
        self.properties_panel.property_changed.connect(self._on_property_changed)
        
        # Add widgets to splitter
        self.splitter.addWidget(self.tab_widget)
        self.splitter.addWidget(self.properties_panel)
        self.splitter.setSizes([700, 300])  # Initial sizes
        
        main_layout.addWidget(self.splitter)
        
    def _create_corner_widget(self):
        """Create widget for the corner of the tab bar."""
        corner_widget = QWidget()
        layout = QHBoxLayout(corner_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        new_tab_button = QPushButton("+")
        new_tab_button.setToolTip("New Connection Tab")
        new_tab_button.clicked.connect(self._show_new_tab_menu)
        
        layout.addWidget(new_tab_button)
        return corner_widget
        
    def _show_new_tab_menu(self):
        """Show menu for creating new connection tabs."""
        menu = QMenu(self)
        menu.addAction("New VPN Connection", lambda: self._create_new_connection("vpn"))
        menu.addAction("New RDP Connection", lambda: self._create_new_connection("rdp"))
        menu.addAction("New Browser Connection", lambda: self._create_new_connection("browser"))
        
        # Show menu at button position
        button = self.sender()
        if button:
            menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
        
    def _create_new_connection(self, connection_type):
        """Create a new connection of the specified type."""
        # In a real implementation, this would open a dialog to create a new connection
        # and then open a tab for it
        QMessageBox.information(self, "New Connection", f"Creating new {connection_type} connection...")
        
    def open_connection(self, connection_id, connection_type, connection_data):
        """Open a connection in a new tab."""
        if connection_id in self.open_connections:
            # Connection already open, switch to its tab
            self.tab_widget.setCurrentIndex(self.open_connections[connection_id]["tab_index"])
            return
            
        # Create tab content based on connection type
        if connection_type == "vpn":
            tab_content = self._create_vpn_tab(connection_data)
        elif connection_type == "rdp":
            tab_content = self._create_rdp_tab(connection_data)
        else:
            tab_content = QWidget()
            layout = QVBoxLayout(tab_content)
            layout.addWidget(QLabel(f"Unsupported connection type: {connection_type}"))
            
        # Add tab
        tab_index = self.tab_widget.addTab(tab_content, connection_data.get("name", "Unnamed"))
        
        # Set icon if available
        icon_path = connection_data.get("icon_path")
        if icon_path and os.path.exists(icon_path):
            self.tab_widget.setTabIcon(tab_index, QIcon(icon_path))
            
        # Store connection info
        self.open_connections[connection_id] = {
            "tab_index": tab_index,
            "type": connection_type,
            "data": connection_data
        }
        
        # Switch to new tab
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Emit signal
        self.connection_opened.emit(connection_id, connection_type)
        
    def _create_vpn_tab(self, connection_data):
        """Create tab content for VPN connection."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Connection info
        info_label = QLabel(f"VPN Connection: {connection_data.get('name', 'Unnamed')}")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(info_label)
        
        # Server info
        vpn_params = connection_data.get("config", {}).get("vpn_params", {})
        server_label = QLabel(f"Server: {vpn_params.get('server', 'Unknown')}")
        layout.addWidget(server_label)
        
        # Status
        status_label = QLabel("Status: Disconnected")
        layout.addWidget(status_label)
        
        # Connect button
        connect_button = QPushButton("Connect")
        layout.addWidget(connect_button)
        
        layout.addStretch()
        return widget
        
    def _create_rdp_tab(self, connection_data):
        """Create tab content for RDP connection."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Connection info
        info_label = QLabel(f"RDP Connection: {connection_data.get('name', 'Unnamed')}")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(info_label)
        
        # Host info
        rdp_details = connection_data.get("config", {}).get("remote_access", {}).get("rdp_details", {})
        host_label = QLabel(f"Host: {rdp_details.get('hostname', 'Unknown')}")
        layout.addWidget(host_label)
        
        # Status
        status_label = QLabel("Status: Disconnected")
        layout.addWidget(status_label)
        
        # Connect button
        connect_button = QPushButton("Connect")
        layout.addWidget(connect_button)
        
        layout.addStretch()
        return widget
        
    def _close_tab(self, index):
        """Close the tab at the specified index."""
        # Find connection ID for this tab
        connection_id = None
        for cid, info in self.open_connections.items():
            if info["tab_index"] == index:
                connection_id = cid
                break
                
        if connection_id:
            # Remove tab
            self.tab_widget.removeTab(index)
            
            # Update tab indices for connections after this one
            for cid, info in self.open_connections.items():
                if info["tab_index"] > index:
                    info["tab_index"] -= 1
                    
            # Remove from open connections
            del self.open_connections[connection_id]
            
            # Emit signal
            self.connection_closed.emit(connection_id)
            
    def _on_tab_changed(self, index):
        """Handle tab change event."""
        if index < 0:
            # No tabs open
            self.properties_panel.set_connection(None)
            return
            
        # Find connection for this tab
        connection_data = None
        for info in self.open_connections.values():
            if info["tab_index"] == index:
                connection_data = info["data"]
                break
                
        # Update properties panel
        self.properties_panel.set_connection(connection_data)
        
    def _on_property_changed(self, property_name, connection_id, value):
        """Handle property change event."""
        if connection_id in self.open_connections:
            # Update connection data
            if property_name == "name":
                # Update tab text
                tab_index = self.open_connections[connection_id]["tab_index"]
                self.tab_widget.setTabText(tab_index, value)
                
            # In a real implementation, this would update the connection data
            # and possibly save it to persistent storage
            
    def get_open_connections(self) -> List[str]:
        """Get list of open connection IDs."""
        return list(self.open_connections.keys())
        
    def close_all_tabs(self):
        """Close all open tabs."""
        while self.tab_widget.count() > 0:
            self._close_tab(0)
