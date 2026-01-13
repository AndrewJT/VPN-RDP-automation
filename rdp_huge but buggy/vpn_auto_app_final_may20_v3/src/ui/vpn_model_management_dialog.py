from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QMessageBox, 
    QListWidgetItem, QDialogButtonBox, QLabel, QLineEdit, QInputDialog
)
from PyQt6.QtCore import Qt
from typing import Optional, List

from ..models.vpn_model import VPNModel
from ..models.vpn_model_manager import VPNModelManager
from .vpn_model_editor_dialog import VPNModelEditorDialog
from PyQt6.QtWidgets import QWidget

class VPNModelManagementDialog(QDialog):
    def __init__(self, model_manager: VPNModelManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.setWindowTitle("VPN Model Management")
        self.setMinimumSize(500, 400)

        self.layout = QVBoxLayout(self)

        self.model_list_widget = QListWidget()
        self.model_list_widget.itemDoubleClicked.connect(self.edit_model)
        self.layout.addWidget(self.model_list_widget)

        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add New Model")
        self.add_button.clicked.connect(self.add_model)
        self.edit_button = QPushButton("Edit Selected")
        self.edit_button.clicked.connect(self.edit_model)
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_model)
        
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.edit_button)
        self.button_layout.addWidget(self.delete_button)
        self.layout.addLayout(self.button_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.load_models()

    def load_models(self):
        self.model_list_widget.clear()
        models = self.model_manager.list_models()
        for model in models:
            item = QListWidgetItem(f"{model.model_name} ({model.model_id})")
            item.setData(Qt.ItemDataRole.UserRole, model) # Store the whole model object
            self.model_list_widget.addItem(item)

    def get_selected_model(self) -> Optional[VPNModel]:
        selected_items = self.model_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a model first.")
            return None
        return selected_items[0].data(Qt.ItemDataRole.UserRole)

    def add_model(self):
        # Placeholder for VPNModelEditorDialog
        # For now, let's use a simple input dialog for model_id and model_name            # model_name, ok_name = QInputDialog.getText(self, "New Model Name", "Enter a Model Name (e.g., FortiClient v7 SSL-VPN):")
            # if ok_name and model_name:
            # Create a basic model for now. The editor dialog will handle full creation.
            # new_model = VPNModel(model_id=model_id, model_name=model_name, vpn_client_type="generic")
            editor_dialog = VPNModelEditorDialog(self.model_manager, model=None, parent=self) # Pass None for new model
            if editor_dialog.exec():
                self.load_models()
            # else:
            #     QMessageBox.information(self, "Cancelled", "Model creation cancelled.")
        # else:
        #     QMessageBox.information(self, "Cancelled", "Model creation cancelled.")

    def edit_model(self):
        model = self.get_selected_model()
        if model:
            editor_dialog = VPNModelEditorDialog(self.model_manager, model=model, parent=self)
            if editor_dialog.exec():
                self.load_models()

    def delete_model(self):
        model = self.get_selected_model()
        if model:
            reply = QMessageBox.question(self, "Confirm Delete", 
                                         f"Are you sure you want to delete model 	'{model.model_name}	'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self.model_manager.delete_model(model.model_id):
                    QMessageBox.information(self, "Success", f"Model 	'{model.model_name}	' deleted.")
                    self.load_models()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to delete model 	'{model.model_name}	'.")

# To make this runnable for quick testing (requires a models directory)
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    # Create a dummy model manager and models dir for testing
    if not os.path.exists("../../config/vpn_models"):
        os.makedirs("../../config/vpn_models")
    
    manager = VPNModelManager(models_dir="../../config/vpn_models")
    # Create some dummy models for testing
    model1 = VPNModel("test_model_1", "Test Model One", "test_client")
    model2 = VPNModel("test_model_2", "Test Model Two", "test_client_alt")
    manager.save_model(model1)
    manager.save_model(model2)

    app = QApplication(sys.argv)
    dialog = VPNModelManagementDialog(manager)
    dialog.show()
    sys.exit(app.exec())

