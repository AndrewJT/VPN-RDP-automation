import os
from typing import Optional, Dict, Any, List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel,
    QToolBar, QLineEdit, QCompleter, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QAction

class QuickConnectBar(QWidget):
    """Enhanced quick connect bar for rapidly accessing frequently used connections."""
    
    connection_requested = pyqtSignal(str, str, dict)  # connection_id, connection_type, connection_details
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recent_connections = []  # List of (id, name, type) tuples
        self.favorite_connections = []  # List of (id, name, type) tuples
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        label = QLabel("Quick Connect:")
        main_layout.addWidget(label)
        
        # Connection combo with autocomplete
        self.connection_combo = QComboBox()
        self.connection_combo.setEditable(True)
        self.connection_combo.setMinimumWidth(250)
        self.connection_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.connection_combo.lineEdit().returnPressed.connect(self._connect_current)
        self.connection_combo.currentIndexChanged.connect(self._update_favorite_button_state)
        main_layout.addWidget(self.connection_combo)
        
        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._connect_current)
        main_layout.addWidget(self.connect_button)
        
        # Favorite button
        self.favorite_button = QPushButton("☆")  # Start with unfilled star
        self.favorite_button.setToolTip("Add to Favorites")
        self.favorite_button.clicked.connect(self._toggle_favorite)
        main_layout.addWidget(self.favorite_button)
        
        # Recent connections button
        self.recent_button = QPushButton("History")
        self.recent_button.setToolTip("Recent Connections")
        self.recent_button.clicked.connect(self._show_recent_menu)
        main_layout.addWidget(self.recent_button)
        
        # Update the combo box
        self._update_combo_box()
        
    def _update_combo_box(self):
        """Update the combo box with favorites and recent connections."""
        current_text = self.connection_combo.currentText()
        self.connection_combo.clear()
        
        # Add favorites first
        for conn_id, name, conn_type in self.favorite_connections:
            self.connection_combo.addItem(f"★ {name} ({conn_type})", (conn_id, conn_type))
            
        # Then add recent connections that aren't favorites
        for conn_id, name, conn_type in self.recent_connections:
            if not any(fav_id == conn_id for fav_id, _, _ in self.favorite_connections):
                self.connection_combo.addItem(f"{name} ({conn_type})", (conn_id, conn_type))
        
        # Restore the text if it was being edited
        if current_text:
            self.connection_combo.setCurrentText(current_text)
            
        # Update favorite button state
        self._update_favorite_button_state()
                
    def _update_favorite_button_state(self):
        """Update the favorite button icon based on current selection."""
        index = self.connection_combo.currentIndex()
        is_favorite = False
        
        if index >= 0:
            conn_data = self.connection_combo.itemData(index)
            if conn_data:
                conn_id, _ = conn_data
                # Check if it's in favorites
                is_favorite = any(fav_id == conn_id for fav_id, _, _ in self.favorite_connections)
        
        # Update button text/icon
        if is_favorite:
            self.favorite_button.setText("★")  # Filled star
            self.favorite_button.setToolTip("Remove from Favorites")
        else:
            self.favorite_button.setText("☆")  # Unfilled star
            self.favorite_button.setToolTip("Add to Favorites")
                
    def _connect_current(self):
        """Connect to the currently selected connection."""
        index = self.connection_combo.currentIndex()
        if index >= 0:
            # Get connection from combo box item data
            conn_data = self.connection_combo.itemData(index)
            if conn_data:
                conn_id, conn_type = conn_data
                # Find connection details if available
                details = self._get_connection_details(conn_id, conn_type)
                self.connection_requested.emit(conn_id, conn_type, details)
                return
        
        # Try to find a connection by name or use as direct connection
        text = self.connection_combo.currentText().strip()
        if text:
            # Check if it's an IP address or hostname (direct RDP connection)
            if self._looks_like_hostname_or_ip(text):
                # Create basic details for direct RDP connection
                details = {"hostname": text, "port": 3389}
                # Add to recent connections
                self.add_recent_connection(text, text, "rdp")
                # Emit signal for direct RDP connection
                self.connection_requested.emit(text, "rdp", details)
                return
                
            # Search in favorites and recent connections
            for conn_id, name, conn_type in self.favorite_connections + self.recent_connections:
                if name.lower() == text.lower():
                    details = self._get_connection_details(conn_id, conn_type)
                    self.connection_requested.emit(conn_id, conn_type, details)
                    return
                    
            # Not found, ask user if they want to create a new RDP connection
            if QMessageBox.question(
                self, 
                "New Connection", 
                f"'{text}' is not a recognized connection. Do you want to create a new RDP connection to this host?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                # Create basic details for new RDP connection
                details = {"hostname": text, "port": 3389}
                # Add to recent connections
                self.add_recent_connection(text, text, "rdp")
                # Emit signal for new RDP connection
                self.connection_requested.emit(text, "rdp", details)
                
    def _looks_like_hostname_or_ip(self, text):
        """Check if text looks like a hostname or IP address."""
        # Simple check for IP or hostname patterns
        return (
            "." in text or  # Has dots like domain or IP
            text.lower() == "localhost" or  # Localhost
            text.isdigit() or  # Numeric only could be an IP without dots
            (text.replace(".", "").isdigit() and text.count(".") <= 3)  # IP-like with dots
        )
                
    def _get_connection_details(self, conn_id, conn_type):
        """Get connection details for a given connection ID and type."""
        # This would typically fetch from a connection manager or profile store
        # For now, return a basic dictionary with the ID as hostname for RDP
        if conn_type == "rdp":
            return {"hostname": conn_id, "port": 3389, "save_credentials": True, "use_saved_credentials": True}
        return {}
                
    def _toggle_favorite(self):
        """Toggle favorite status of the current connection."""
        index = self.connection_combo.currentIndex()
        if index >= 0:
            conn_data = self.connection_combo.itemData(index)
            if conn_data:
                conn_id, conn_type = conn_data
                
                # Find the connection name
                conn_name = ""
                for c_id, name, c_type in self.recent_connections:
                    if c_id == conn_id:
                        conn_name = name
                        break
                        
                if not conn_name:
                    # Try to get the name from the combo box text
                    text = self.connection_combo.currentText().strip()
                    if text:
                        # Remove the type suffix if present
                        if f" ({conn_type})" in text:
                            conn_name = text.replace(f" ({conn_type})", "")
                        # Remove star prefix if present
                        if conn_name.startswith("★ "):
                            conn_name = conn_name[2:]
                        else:
                            conn_name = text
                
                if not conn_name:
                    return
                    
                # Check if it's already a favorite
                is_favorite = False
                for i, (fav_id, fav_name, fav_type) in enumerate(self.favorite_connections):
                    if fav_id == conn_id:
                        is_favorite = True
                        # Remove from favorites
                        self.favorite_connections.pop(i)
                        break
                        
                if not is_favorite:
                    # Add to favorites
                    self.favorite_connections.append((conn_id, conn_name, conn_type))
                    
                # Update the combo box
                self._update_combo_box()
        else:
            # Try to favorite the current text
            text = self.connection_combo.currentText().strip()
            if text and self._looks_like_hostname_or_ip(text):
                # Add as a favorite RDP connection
                self.favorite_connections.append((text, text, "rdp"))
                # Also add to recent connections
                self.add_recent_connection(text, text, "rdp")
                # Update the combo box
                self._update_combo_box()
                return
                
    def _show_recent_menu(self):
        """Show menu with recent connections."""
        menu = QMenu(self)
        
        # Add favorites section
        if self.favorite_connections:
            menu.addSection("Favorites")
            for conn_id, name, conn_type in self.favorite_connections:
                action = menu.addAction(f"★ {name} ({conn_type})")
                action.triggered.connect(lambda checked=False, cid=conn_id, ctype=conn_type: 
                                        self._connect_from_menu(cid, ctype))
                                        
        # Add recent connections section
        if self.recent_connections:
            menu.addSection("Recent")
            for conn_id, name, conn_type in self.recent_connections:
                if not any(fav_id == conn_id for fav_id, _, _ in self.favorite_connections):
                    action = menu.addAction(f"{name} ({conn_type})")
                    action.triggered.connect(lambda checked=False, cid=conn_id, ctype=conn_type: 
                                            self._connect_from_menu(cid, ctype))
                                            
        # Show menu
        if menu.isEmpty():
            menu.addAction("No recent connections").setEnabled(False)
            
        button = self.sender()
        if button:
            menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
            
    def _connect_from_menu(self, conn_id, conn_type):
        """Connect to a connection selected from the menu."""
        details = self._get_connection_details(conn_id, conn_type)
        self.connection_requested.emit(conn_id, conn_type, details)
            
    def add_recent_connection(self, conn_id: str, name: str, conn_type: str):
        """Add a connection to the recent list."""
        # Remove if already in list
        self.recent_connections = [(cid, cname, ctype) for cid, cname, ctype in self.recent_connections 
                                  if cid != conn_id]
                                  
        # Add to beginning of list
        self.recent_connections.insert(0, (conn_id, name, conn_type))
        
        # Limit to 10 recent connections
        if len(self.recent_connections) > 10:
            self.recent_connections = self.recent_connections[:10]
            
        # Update the combo box
        self._update_combo_box()
        
    def set_connections(self, favorites: List[Tuple[str, str, str]], recents: List[Tuple[str, str, str]]):
        """Set the favorite and recent connections."""
        self.favorite_connections = favorites
        self.recent_connections = recents
        self._update_combo_box()
