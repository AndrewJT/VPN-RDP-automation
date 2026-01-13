from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QTextEdit, 
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QDialogButtonBox,
    QLabel, QComboBox, QCheckBox, QGroupBox, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional, List, Dict, Any

from ..models.vpn_model import VPNModel
from ..models.vpn_model_manager import VPNModelManager

class ListEditorWidget(QWidget):
    """A generic widget to edit a list of dictionary items."""
    items_changed = pyqtSignal()

    def __init__(self, item_schema: Dict[str, str], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.item_schema = item_schema # e.g., {"field_id": "text", "field_name": "text", "field_type": "combo:text_input,button"}
        self.items_data: List[Dict[str, Any]] = []

        self.main_layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.edit_item)
        self.main_layout.addWidget(self.list_widget)

        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_item)
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_item)
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_item)
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.edit_button)
        self.button_layout.addWidget(self.remove_button)
        self.main_layout.addLayout(self.button_layout)

    def _display_items(self):
        self.list_widget.clear()
        for item_data in self.items_data:
            # Display the first value or a combination
            display_text = " | ".join(str(item_data.get(key, "")) for key in self.item_schema.keys())
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.ItemDataRole.UserRole, item_data) # Store full dict
            self.list_widget.addItem(list_item)

    def set_items(self, items: List[Dict[str, Any]]):
        self.items_data = list(items) # Make a copy
        self._display_items()

    def get_items(self) -> List[Dict[str, Any]]:
        return self.items_data

    def add_item(self):
        dialog = ItemEditDialog(self.item_schema, parent=self)
        if dialog.exec():
            new_item_data = dialog.get_data()
            self.items_data.append(new_item_data)
            self._display_items()
            self.items_changed.emit()

    def edit_item(self):
        selected_list_items = self.list_widget.selectedItems()
        if not selected_list_items:
            QMessageBox.warning(self, "Selection Error", "Please select an item to edit.")
            return
        
        current_item_widget = selected_list_items[0]
        current_item_data = current_item_widget.data(Qt.ItemDataRole.UserRole)
        original_index = self.items_data.index(current_item_data)

        dialog = ItemEditDialog(self.item_schema, item_data=current_item_data, parent=self)
        if dialog.exec():
            updated_item_data = dialog.get_data()
            self.items_data[original_index] = updated_item_data
            self._display_items()
            self.items_changed.emit()

    def remove_item(self):
        selected_list_items = self.list_widget.selectedItems()
        if not selected_list_items:
            QMessageBox.warning(self, "Selection Error", "Please select an item to remove.")
            return

        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to remove this item?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            current_item_widget = selected_list_items[0]
            current_item_data = current_item_widget.data(Qt.ItemDataRole.UserRole)
            self.items_data.remove(current_item_data)
            self._display_items()
            self.items_changed.emit()

class ItemEditDialog(QDialog):
    """A generic dialog to edit a dictionary based on a schema."""
    def __init__(self, schema: Dict[str, str], item_data: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.schema = schema
        self.data = dict(item_data) if item_data else {}
        self.setWindowTitle("Edit Item")

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.editors: Dict[str, QWidget] = {}

        for key, field_type_info in schema.items():
            label = QLabel(key.replace("_", " ").title() + ":")
            editor: QWidget
            field_type_parts = field_type_info.split(":", 1)
            field_type = field_type_parts[0]
            options = field_type_parts[1].split(",") if len(field_type_parts) > 1 else []

            if field_type == "text":
                editor = QLineEdit(str(self.data.get(key, "")))
            elif field_type == "textarea":
                editor = QTextEdit(str(self.data.get(key, "")))
                editor.setAcceptRichText(False)
            elif field_type == "combo":
                editor = QComboBox()
                editor.addItems(options)
                if key in self.data:
                    editor.setCurrentText(str(self.data[key]))
            elif field_type == "checkbox":
                editor = QCheckBox()
                if key in self.data:
                    editor.setChecked(bool(self.data[key]))
            else:
                editor = QLineEdit(str(self.data.get(key, ""))) # Default to text
            
            self.editors[key] = editor
            self.form_layout.addRow(label, editor)
        
        self.layout.addLayout(self.form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept_data)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def accept_data(self):
        for key, editor in self.editors.items():
            if isinstance(editor, QLineEdit):
                self.data[key] = editor.text()
            elif isinstance(editor, QTextEdit):
                self.data[key] = editor.toPlainText()
            elif isinstance(editor, QComboBox):
                self.data[key] = editor.currentText()
            elif isinstance(editor, QCheckBox):
                self.data[key] = editor.isChecked()
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return self.data

class VPNModelEditorDialog(QDialog):
    def __init__(self, model_manager: VPNModelManager, model: Optional[VPNModel] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.model = model
        self.is_editing = model is not None

        self.setWindowTitle("Edit VPN Model" if self.is_editing else "Create New VPN Model")
        self.setMinimumSize(600, 700)

        self.main_layout = QVBoxLayout(self)
        
        # Scroll Area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(scroll_area)
        
        scroll_content_widget = QWidget()
        scroll_area.setWidget(scroll_content_widget)
        self.content_layout = QVBoxLayout(scroll_content_widget)

        # --- Model Metadata --- 
        metadata_group = QGroupBox("Model Metadata")
        metadata_form_layout = QFormLayout()
        self.model_id_edit = QLineEdit()
        self.model_id_edit.setPlaceholderText("e.g., forticlient_ssl_v7")
        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText("e.g., FortiClient SSL VPN v7.x")
        self.vpn_client_type_edit = QLineEdit()
        self.vpn_client_type_edit.setPlaceholderText("e.g., forticlient, globalprotect")
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Brief description of the model and its use case.")
        self.description_edit.setAcceptRichText(False)

        metadata_form_layout.addRow("Model ID:", self.model_id_edit)
        metadata_form_layout.addRow("Model Name:", self.model_name_edit)
        metadata_form_layout.addRow("VPN Client Type:", self.vpn_client_type_edit)
        metadata_form_layout.addRow("Description:", self.description_edit)
        metadata_group.setLayout(metadata_form_layout)
        self.content_layout.addWidget(metadata_group)

        if self.is_editing and self.model:
            self.model_id_edit.setText(self.model.model_id)
            self.model_id_edit.setReadOnly(True) # Cannot change ID of existing model
            self.model_name_edit.setText(self.model.model_name)
            self.vpn_client_type_edit.setText(self.model.vpn_client_type)
            self.description_edit.setText(self.model.description)

        # --- Logical Fields --- 
        logical_fields_group = QGroupBox("Logical Fields")
        logical_fields_layout = QVBoxLayout()
        logical_field_schema = {
            "field_id": "text", 
            "field_name": "text", 
            "field_type": "combo:text_input,button,checkbox,dropdown,label",
            "description": "textarea"
        }
        self.logical_fields_editor = ListEditorWidget(logical_field_schema)
        if self.is_editing and self.model:
            self.logical_fields_editor.set_items(self.model.logical_fields)
        logical_fields_layout.addWidget(self.logical_fields_editor)
        logical_fields_group.setLayout(logical_fields_layout)
        self.content_layout.addWidget(logical_fields_group)

        # --- Automation Steps --- 
        automation_steps_group = QGroupBox("Automation Steps")
        automation_steps_layout = QVBoxLayout()
        automation_step_schema = {
            "step_id": "text",
            "step_name": "text",
            "action_type": "combo:LOCATE_AND_INPUT_TEXT,LOCATE_AND_CLICK,WAIT_FOR_ELEMENT,CREATE_NEW_CONNECTION_ENTRY,SEND_KEYS,EXECUTE_SCRIPT",
            "target_logical_field_id": "text", # Ideally, this would be a combo box populated from logical_fields_editor
            "default_value_source": "text",
            "required": "checkbox"
        }
        self.automation_steps_editor = ListEditorWidget(automation_step_schema)
        if self.is_editing and self.model:
            self.automation_steps_editor.set_items(self.model.automation_steps)
        automation_steps_layout.addWidget(self.automation_steps_editor)
        automation_steps_group.setLayout(automation_steps_layout)
        self.content_layout.addWidget(automation_steps_group)

        # --- Dialog Buttons --- 
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.save_model_data)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)

    def save_model_data(self):
        model_id = self.model_id_edit.text().strip()
        model_name = self.model_name_edit.text().strip()
        vpn_client_type = self.vpn_client_type_edit.text().strip()

        if not model_id or not model_name:
            QMessageBox.warning(self, "Validation Error", "Model ID and Model Name cannot be empty.")
            return

        if not self.is_editing and self.model_manager.load_model(model_id):
            QMessageBox.warning(self, "Validation Error", f"Model ID 	'{model_id}	' already exists. Please choose a unique ID.")
            return

        logical_fields = self.logical_fields_editor.get_items()
        automation_steps = self.automation_steps_editor.get_items()

        if self.model and self.is_editing: # Editing existing model
            self.model.model_name = model_name
            self.model.vpn_client_type = vpn_client_type
            self.model.description = self.description_edit.toPlainText()
            self.model.logical_fields = logical_fields
            self.model.automation_steps = automation_steps
            save_success = self.model_manager.save_model(self.model)
        else: # Creating new model
            new_model = VPNModel(
                model_id=model_id,
                model_name=model_name,
                vpn_client_type=vpn_client_type,
                description=self.description_edit.toPlainText(),
                logical_fields=logical_fields,
                automation_steps=automation_steps
            )
            save_success = self.model_manager.save_model(new_model)
            self.model = new_model # So it can be accessed if needed after save

        if save_success:
            QMessageBox.information(self, "Success", f"VPN Model 	'{model_name}	' saved successfully.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save VPN Model 	'{model_name}	'. Check console for details.")

# Example usage (for testing this dialog directly)
if __name__ == '__main__':
    import sys
    import os
    from PyQt6.QtWidgets import QApplication

    # Create a dummy model manager and models dir for testing
    test_models_dir = "../../config/vpn_models_editor_test"
    if not os.path.exists(test_models_dir):
        os.makedirs(test_models_dir)
    
    manager = VPNModelManager(models_dir=test_models_dir)
    
    # Test creating a new model
    # app = QApplication(sys.argv)
    # editor_dialog = VPNModelEditorDialog(manager)
    # if editor_dialog.exec():
    #     print("Dialog accepted, model should be saved.")
    # else:
    #     print("Dialog cancelled.")

    # Test editing an existing model (create one first)
    sample_model_data = {
        "model_id": "sample_edit_model",
        "model_name": "Sample Model for Editing",
        "vpn_client_type": "sample_client",
        "description": "This is a test model to demonstrate editing.",
        "logical_fields": [
            {"field_id": "server", "field_name": "Server Address", "field_type": "text_input", "description": "VPN Server"},
            {"field_id": "user", "field_name": "Username", "field_type": "text_input", "description": "Login username"}
        ],
        "automation_steps": [
            {"step_id": "s1", "step_name": "Enter Server", "action_type": "LOCATE_AND_INPUT_TEXT", "target_logical_field_id": "server", "required": True},
            {"step_id": "s2", "step_name": "Click Connect", "action_type": "LOCATE_AND_CLICK", "target_logical_field_id": "connect_button", "required": True}
        ]
    }
    existing_model = VPNModel.from_dict(sample_model_data)
    manager.save_model(existing_model)

    app = QApplication(sys.argv)
    editor_dialog_edit = VPNModelEditorDialog(manager, model=existing_model)
    if editor_dialog_edit.exec():
        print("Edit Dialog accepted, model should be updated.")
    else:
        print("Edit Dialog cancelled.")

    sys.exit(app.exec())

