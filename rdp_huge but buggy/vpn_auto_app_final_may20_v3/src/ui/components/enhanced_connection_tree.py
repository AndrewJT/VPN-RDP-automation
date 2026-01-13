import os
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon

# Constants
FOLDER_TYPE = "folder"
VPN_CONNECTION_TYPE = "vpn"
RDP_CONNECTION_TYPE = "rdp"
ICON_SIZE = QSize(24, 24)

class ConnectionTreeItem(QTreeWidgetItem):
    """Enhanced tree item with inheritance support for the connection tree."""
    
    def __init__(self, parent=None, item_type=None, name=None, data=None):
        super().__init__(parent, [name] if name else [])
        self.item_type = item_type or FOLDER_TYPE
        self.connection_data = data or {}
        self.inherited_properties = set()
        
        # Set icon based on type
        if self.item_type == FOLDER_TYPE:
            self.setIcon(0, QIcon.fromTheme("folder", QIcon(":/qt-project.org/styles/commonstyle/images/diropen-32.png")))
        elif self.item_type == VPN_CONNECTION_TYPE:
            icon_path = self.connection_data.get("icon_path")
            if icon_path and os.path.exists(icon_path):
                self.setIcon(0, QIcon(icon_path))
            else:
                self.setIcon(0, QIcon.fromTheme("network-vpn", QIcon(":/qt-project.org/styles/commonstyle/images/network-32.png")))
        elif self.item_type == RDP_CONNECTION_TYPE:
            icon_path = self.connection_data.get("icon_path")
            if icon_path and os.path.exists(icon_path):
                self.setIcon(0, QIcon(icon_path))
            else:
                self.setIcon(0, QIcon.fromTheme("computer", QIcon(":/qt-project.org/styles/commonstyle/images/computer-32.png")))
                
        # Store data for easy access
        self.setData(0, Qt.ItemDataRole.UserRole, {
            "type": self.item_type,
            "name": name,
            "data": self.connection_data
        })
        
    def get_inherited_properties(self):
        """Get properties that should be inherited by children."""
        if self.item_type != FOLDER_TYPE:
            return {}
            
        # For folders, return properties that can be inherited
        return self.connection_data.get("inheritable_properties", {})
        
    def inherit_properties_from_parent(self):
        """Inherit properties from parent folder."""
        if self.item_type == FOLDER_TYPE:
            return  # Folders don't inherit
            
        parent = self.parent()
        if not parent:
            return
            
        # Get inheritable properties from parent
        inherited = parent.get_inherited_properties()
        if not inherited:
            return
            
        # Apply inherited properties to this connection
        for prop_name, prop_value in inherited.items():
            # Skip if property is explicitly set in this connection
            if prop_name in self.connection_data:
                continue
                
            # Apply inherited property
            self.connection_data[prop_name] = prop_value
            self.inherited_properties.add(prop_name)
            
    def update_inheritance(self):
        """Update inheritance for this item and all children."""
        if self.item_type == FOLDER_TYPE:
            # Update all children
            for i in range(self.childCount()):
                child = self.child(i)
                if isinstance(child, ConnectionTreeItem):
                    child.inherit_properties_from_parent()
                    child.update_inheritance()
        else:
            # Just inherit from parent
            self.inherit_properties_from_parent()

class EnhancedConnectionTree(QTreeWidget):
    """Enhanced tree widget with inheritance support for managing connections."""
    
    connection_selected = pyqtSignal(str, str, dict)  # connection_id, connection_type, connection_data
    connection_activated = pyqtSignal(str, str, dict)  # connection_id, connection_type, connection_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Connections"])
        self.setIconSize(ICON_SIZE)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemClicked.connect(self._on_item_clicked)
        
    def _show_context_menu(self, position):
        """Show context menu for tree items."""
        item = self.itemAt(position)
        if not item or not isinstance(item, ConnectionTreeItem):
            return
            
        menu = QMenu()
        
        if item.item_type == FOLDER_TYPE:
            # Folder context menu
            menu.addAction("New Connection", lambda: self._new_connection(item))
            menu.addAction("New Folder", lambda: self._new_folder(item))
            menu.addSeparator()
            menu.addAction("Set Inheritable Properties", lambda: self._set_inheritable_properties(item))
            menu.addSeparator()
            menu.addAction("Rename", lambda: self._rename_item(item))
            menu.addAction("Delete", lambda: self._delete_item(item))
        else:
            # Connection context menu
            menu.addAction("Connect", lambda: self._connect_item(item))
            menu.addAction("Edit", lambda: self._edit_item(item))
            menu.addAction("Duplicate", lambda: self._duplicate_item(item))
            menu.addSeparator()
            
            # Inheritance submenu
            inheritance_menu = menu.addMenu("Inheritance")
            
            # Toggle inheritance
            inherit_action = inheritance_menu.addAction("Inherit from Parent")
            inherit_action.setCheckable(True)
            inherit_action.setChecked(item.connection_data.get("inherit_from_parent", False))
            inherit_action.toggled.connect(lambda checked: self._toggle_inheritance(item, checked))
            
            # Override specific properties
            if item.connection_data.get("inherit_from_parent", False):
                inheritance_menu.addSeparator()
                inheritance_menu.addAction("Override Properties", lambda: self._override_properties(item))
            
            menu.addSeparator()
            menu.addAction("Delete", lambda: self._delete_item(item))
        
        menu.exec(self.mapToGlobal(position))
        
    def _on_item_double_clicked(self, item, column):
        """Handle double-click on tree items."""
        if not isinstance(item, ConnectionTreeItem):
            return
            
        if item.item_type != FOLDER_TYPE:
            # Connect to the selected connection
            self._connect_item(item)
            
    def _on_item_clicked(self, item, column):
        """Handle click on tree items."""
        if not isinstance(item, ConnectionTreeItem):
            return
            
        if item.item_type != FOLDER_TYPE:
            # Emit signal for connection selected
            conn_id = item.connection_data.get("id", item.text(0))
            self.connection_selected.emit(conn_id, item.item_type, item.connection_data)
            
    def _connect_item(self, item):
        """Connect to the selected connection."""
        if not isinstance(item, ConnectionTreeItem) or item.item_type == FOLDER_TYPE:
            return
            
        # Emit signal for connection activated
        conn_id = item.connection_data.get("id", item.text(0))
        self.connection_activated.emit(conn_id, item.item_type, item.connection_data)
        
    def _new_connection(self, parent_item=None):
        """Create a new connection."""
        # In a real implementation, this would open a dialog to create a new connection
        name, ok = QInputDialog.getText(self, "New Connection", "Connection name:")
        if ok and name:
            # Create a new connection item
            connection_data = {"name": name, "id": name}
            item = ConnectionTreeItem(parent_item, VPN_CONNECTION_TYPE, name, connection_data)
            
            # Apply inheritance if parent is a folder
            if parent_item and isinstance(parent_item, ConnectionTreeItem) and parent_item.item_type == FOLDER_TYPE:
                item.inherit_properties_from_parent()
                
            # If no parent specified, add to root
            if not parent_item:
                self.addTopLevelItem(item)
                
    def _new_folder(self, parent_item=None):
        """Create a new folder."""
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            # Create a new folder item
            folder_data = {"name": name}
            item = ConnectionTreeItem(parent_item, FOLDER_TYPE, name, folder_data)
            
            # If no parent specified, add to root
            if not parent_item:
                self.addTopLevelItem(item)
                
            # Expand parent
            if parent_item:
                parent_item.setExpanded(True)
                
    def _set_inheritable_properties(self, item):
        """Set properties that can be inherited by children."""
        if not isinstance(item, ConnectionTreeItem) or item.item_type != FOLDER_TYPE:
            return
            
        # In a real implementation, this would open a dialog to set inheritable properties
        QMessageBox.information(self, "Set Inheritable Properties", 
                               "This would open a dialog to set properties that can be inherited by child connections.")
                               
    def _rename_item(self, item):
        """Rename an item."""
        if not isinstance(item, ConnectionTreeItem):
            return
            
        old_name = item.text(0)
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_name)
        if ok and new_name and new_name != old_name:
            item.setText(0, new_name)
            item.connection_data["name"] = new_name
            if "id" in item.connection_data:
                item.connection_data["id"] = new_name
                
    def _delete_item(self, item):
        """Delete an item."""
        if not isinstance(item, ConnectionTreeItem):
            return
            
        # Confirm deletion
        msg = "Are you sure you want to delete this folder and all its contents?" if item.item_type == FOLDER_TYPE else \
              "Are you sure you want to delete this connection?"
        reply = QMessageBox.question(self, "Confirm Deletion", msg, 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                    QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # Remove from tree
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            index = self.indexOfTopLevelItem(item)
            if index >= 0:
                self.takeTopLevelItem(index)
                
    def _edit_item(self, item):
        """Edit a connection item."""
        if not isinstance(item, ConnectionTreeItem) or item.item_type == FOLDER_TYPE:
            return
            
        # In a real implementation, this would open a dialog to edit the connection
        QMessageBox.information(self, "Edit Connection", 
                               f"This would open a dialog to edit the {item.item_type} connection '{item.text(0)}'.")
                               
    def _duplicate_item(self, item):
        """Duplicate a connection item."""
        if not isinstance(item, ConnectionTreeItem) or item.item_type == FOLDER_TYPE:
            return
            
        # Create a copy of the connection data
        connection_data = item.connection_data.copy()
        connection_data["name"] = f"{connection_data.get('name', 'Unnamed')} (Copy)"
        if "id" in connection_data:
            connection_data["id"] = connection_data["name"]
            
        # Create a new item
        new_item = ConnectionTreeItem(item.parent(), item.item_type, connection_data["name"], connection_data)
        
        # If no parent, add to root
        if not item.parent():
            self.addTopLevelItem(new_item)
            
    def _toggle_inheritance(self, item, checked):
        """Toggle inheritance for a connection."""
        if not isinstance(item, ConnectionTreeItem) or item.item_type == FOLDER_TYPE:
            return
            
        item.connection_data["inherit_from_parent"] = checked
        
        if checked:
            # Apply inheritance
            item.inherit_properties_from_parent()
        else:
            # Clear inherited properties
            for prop in list(item.inherited_properties):
                if prop in item.connection_data:
                    del item.connection_data[prop]
            item.inherited_properties.clear()
            
    def _override_properties(self, item):
        """Override inherited properties."""
        if not isinstance(item, ConnectionTreeItem) or item.item_type == FOLDER_TYPE:
            return
            
        # In a real implementation, this would open a dialog to select properties to override
        QMessageBox.information(self, "Override Properties", 
                               "This would open a dialog to select which inherited properties to override.")
                               
    def update_all_inheritance(self):
        """Update inheritance for all items in the tree."""
        # Start with top-level items
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if isinstance(item, ConnectionTreeItem):
                item.update_inheritance()
