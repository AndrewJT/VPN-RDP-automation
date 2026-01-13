import os
import shutil
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QFormLayout, QMessageBox, QFileDialog, 
    QTabWidget, QWidget, QComboBox, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap

# Attempt to import backend modules and other UI dialogs
try:
    from ..vcal.vpn_manager import VPNManager
    from ..models.vpn_model_manager import VPNModelManager
    from ..models.vpn_model import VPNModel # Assuming VPNModel is needed for type hinting or direct use
    from .visual_config_dialog import VisualConfigDialog
except ImportError as e:
    print(f"Warning (vpn_profile_edit_dialog): Could not import backend/UI modules: {e}. Using placeholders.")
    # Dummy classes for standalone UI testing or when imports fail
    class VPNManager:
        def get_available_driver_types(self) -> List[str]: return ["dummy_type"]
    class VPNModelManager:
        def list_models(self) -> List[Any]: return []
        def load_model(self, model_id: str) -> Optional[Any]: return None
    class VPNModel: pass
    class VisualConfigDialog(QDialog):
        def __init__(self, parent=None, existing_sequence=None):
            super().__init__(parent)
            self.setWindowTitle("Visual Config (Placeholder)")
        def get_sequence(self) -> list: return []
        def get_mapped_sequence(self) -> list: return []

ICON_SIZE = QSize(24, 24)
PROFILE_ICON_DIR_FALLBACK = os.path.join(os.path.expanduser("~"), ".vpn_auto_app_icons")
if not os.path.exists(PROFILE_ICON_DIR_FALLBACK):
    os.makedirs(PROFILE_ICON_DIR_FALLBACK, exist_ok=True)

class VPNProfileEditDialog(QDialog):
    """Dialog for adding or editing VPN profiles, now with tabs as per redesign."""
    def __init__(self, parent=None, profile_data: Optional[Dict[str, Any]]=None, 
                 vpn_manager_instance: Optional[VPNManager]=None, 
                 model_manager_instance: Optional[VPNModelManager]=None,
                 icon_storage_dir: str = PROFILE_ICON_DIR_FALLBACK):
        super().__init__(parent)
        self.setWindowTitle("Edit VPN Profile" if profile_data else "Add VPN Profile")
        self.setMinimumWidth(600) 
        self.icon_storage_dir = icon_storage_dir
        
        self.profile_data = profile_data.copy() if profile_data else {}
        self.vpn_specific_config = self.profile_data.get("config", {}).get("vpn_params", {})
        self.automation_sequence = self.profile_data.get("config", {}).get("automation_sequence", [])
        self.mapped_automation_sequence = self.profile_data.get("config", {}).get("mapped_automation_sequence", [])
        self.icon_path = self.profile_data.get("config", {}).get("icon_path")
        
        self.vpn_manager = vpn_manager_instance
        self.model_manager = model_manager_instance 
        self.selected_model_id = self.profile_data.get("config", {}).get("selected_vpn_model_id")
        self.selected_model = None
        
        if self.selected_model_id and self.model_manager:
            try:
                self.selected_model = self.model_manager.load_model(self.selected_model_id)
            except Exception as e:
                print(f"Error loading selected model: {e}")

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self._create_general_tab()
        self._create_vpn_connection_tab()
        self._create_automation_tab()
        
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Profile")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.save_button.clicked.connect(self.validate_and_accept)
        self.cancel_button.clicked.connect(self.reject)
        
        self._populate_vpn_models()

    def _create_general_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)
        self.profile_name_edit = QLineEdit(self.profile_data.get("name", ""))
        layout.addRow("Profile Name:", self.profile_name_edit)

        icon_layout = QHBoxLayout()
        self.icon_preview_label = QLabel()
        self.icon_preview_label.setFixedSize(ICON_SIZE)
        self.icon_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_preview_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.select_icon_button = QPushButton("Select Icon")
        self.select_icon_button.clicked.connect(self._select_icon)
        self.clear_icon_button = QPushButton("Clear Icon")
        self.clear_icon_button.clicked.connect(self._clear_icon)
        icon_layout.addWidget(self.icon_preview_label)
        icon_layout.addWidget(self.select_icon_button)
        icon_layout.addWidget(self.clear_icon_button)
        layout.addRow("Profile Icon:", icon_layout)
        self._update_icon_preview()
        self.tabs.addTab(tab, "General")

    def _create_vpn_connection_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)
        self.vpn_type_combo = QComboBox()
        if self.vpn_manager:
            try:
                available_types = self.vpn_manager.get_available_driver_types()
                if not available_types: available_types = ["forticlient_dummy", "globalprotect_dummy", "custom"]
                self.vpn_type_combo.addItems(available_types)
            except Exception as e:
                print(f"Could not get VPN types from manager: {e}, using defaults.")
                self.vpn_type_combo.addItems(["forticlient_dummy", "globalprotect_dummy", "custom"])
        else:
            self.vpn_type_combo.addItems(["forticlient_dummy", "globalprotect_dummy", "custom"])
        self.vpn_type_combo.setCurrentText(self.profile_data.get("type", "custom"))
        layout.addRow("VPN Type:", self.vpn_type_combo)

        self.vpn_model_combo = QComboBox()
        self.vpn_model_combo.addItem("None", None)  
        self.vpn_model_combo.currentIndexChanged.connect(self._on_model_selected)
        layout.addRow("VPN Model (Optional):", self.vpn_model_combo)

        self.vpn_server_edit = QLineEdit(self.vpn_specific_config.get("server", ""))
        layout.addRow("Server Address:", self.vpn_server_edit)
        self.vpn_username_edit = QLineEdit(self.vpn_specific_config.get("username", ""))
        layout.addRow("Username:", self.vpn_username_edit)
        self.vpn_group_edit = QLineEdit(self.vpn_specific_config.get("group", ""))
        layout.addRow("Group (Optional):", self.vpn_group_edit)
        
        self.model_fields_group = QGroupBox("Model-Specific Parameters")
        self.model_fields_group.setVisible(False)
        self.model_fields_layout = QFormLayout()
        self.model_fields_group.setLayout(self.model_fields_layout)
        self.model_field_widgets = {}  
        layout.addRow(self.model_fields_group)
        self.tabs.addTab(tab, "VPN Connection")

    def _create_automation_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.configure_automation_button = QPushButton("Configure/Edit Automation Sequence")
        if VisualConfigDialog and VisualConfigDialog.__module__ != __name__ and hasattr(VisualConfigDialog, "exec"):
            self.configure_automation_button.clicked.connect(self.open_visual_config_dialog)
        else:
            self.configure_automation_button.setEnabled(False)
            self.configure_automation_button.setToolTip("VisualConfigDialog module not loaded or placeholder active.")
        layout.addWidget(self.configure_automation_button)
        
        if self.selected_model:
            mapped_steps = len(self.mapped_automation_sequence)
            total_steps = len(self.selected_model.automation_steps) if self.selected_model else 0
            self.automation_summary_label = QLabel(f"{mapped_steps}/{total_steps} model steps mapped")
        else:
            self.automation_summary_label = QLabel(f"{len(self.automation_sequence)} automation steps configured")
        layout.addWidget(self.automation_summary_label)
        self.tabs.addTab(tab, "Automation")

    def _select_icon(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.ico)")
        if file_name:
            base_name = os.path.basename(file_name)
            target_path = os.path.join(self.icon_storage_dir, base_name)
            try:
                shutil.copy(file_name, target_path)
                self.icon_path = target_path 
                self._update_icon_preview()
            except Exception as e:
                QMessageBox.warning(self, "Icon Error", f"Could not copy icon: {e}")
                self.icon_path = None

    def _clear_icon(self):
        self.icon_path = None
        self._update_icon_preview()

    def _update_icon_preview(self):
        if self.icon_path and os.path.exists(self.icon_path):
            pixmap = QPixmap(self.icon_path)
            self.icon_preview_label.setPixmap(pixmap.scaled(ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.icon_preview_label.setText("No Icon")
            self.icon_preview_label.setPixmap(QPixmap()) 
        
    def _populate_vpn_models(self):
        self.vpn_model_combo.clear()
        self.vpn_model_combo.addItem("None", None)  
        if self.model_manager:
            try:
                models = self.model_manager.list_models()
                for model in models:
                    self.vpn_model_combo.addItem(f"{model.model_name} ({model.model_id})", model.model_id)
                if self.selected_model_id:
                    for i in range(self.vpn_model_combo.count()):
                        if self.vpn_model_combo.itemData(i) == self.selected_model_id:
                            self.vpn_model_combo.setCurrentIndex(i)
                            break
            except Exception as e:
                print(f"Error populating VPN models: {e}")
    
    def _on_model_selected(self, index):
        model_id = self.vpn_model_combo.itemData(index)
        self.selected_model_id = model_id
        self.selected_model = None
        self._clear_model_fields()
        if not model_id:  
            self.model_fields_group.setVisible(False)
            self.automation_summary_label.setText(f"{len(self.automation_sequence)} automation steps configured")
            return
        if self.model_manager:
            try:
                self.selected_model = self.model_manager.load_model(model_id)
                if self.selected_model:
                    mapped_steps = len(self.mapped_automation_sequence)
                    total_steps = len(self.selected_model.automation_steps)
                    self.automation_summary_label.setText(f"{mapped_steps}/{total_steps} model steps mapped")
                    self._create_model_fields()
            except Exception as e:
                print(f"Error loading selected model: {e}")
    
    def _clear_model_fields(self):
        while self.model_fields_layout.count():
            item = self.model_fields_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.model_field_widgets = {}
        self.model_fields_group.setVisible(False)
    
    def _create_model_fields(self):
        if not self.selected_model or not hasattr(self.selected_model, "logical_fields") or not self.selected_model.logical_fields:
            self.model_fields_group.setVisible(False)
            return
        for field in self.selected_model.logical_fields:
            field_id = field.get("field_id", "")
            field_name = field.get("field_name", field_id)
            field_type = field.get("field_type", "text_input")
            field_desc = field.get("description", "")
            current_value = self.vpn_specific_config.get(field_id, "")
            widget = None
            if field_type == "text_input": widget = QLineEdit(str(current_value))
            elif field_type == "checkbox": 
                widget = QCheckBox()
                widget.setChecked(bool(current_value))
            elif field_type == "dropdown":
                widget = QComboBox()
                # Placeholder for actual dropdown options if defined in model
                if current_value: widget.addItem(str(current_value))
            if widget:
                if field_desc: widget.setToolTip(field_desc)
                self.model_fields_layout.addRow(f"{field_name}:", widget)
                self.model_field_widgets[field_id] = widget
        self.model_fields_group.setVisible(True)

    def open_visual_config_dialog(self):
        if not VisualConfigDialog or VisualConfigDialog.__module__ == __name__:
            QMessageBox.warning(self, "Feature Unavailable", "Visual configuration dialog is not available.")
            return
        try:
            # Only pass the parameters that VisualConfigDialog accepts
            dialog = VisualConfigDialog(parent=self, 
                                        existing_sequence=self.automation_sequence)
            if dialog.exec():
                self.automation_sequence = dialog.get_sequence()
                # Check if get_mapped_sequence exists before calling it
                if hasattr(dialog, 'get_mapped_sequence'):
                    self.mapped_automation_sequence = dialog.get_mapped_sequence()
                else:
                    # If get_mapped_sequence doesn't exist, use an empty list
                    self.mapped_automation_sequence = []
                
                if self.selected_model:
                    mapped_steps = len(self.mapped_automation_sequence)
                    total_steps = len(self.selected_model.automation_steps)
                    self.automation_summary_label.setText(f"{mapped_steps}/{total_steps} model steps mapped")
                else:
                    self.automation_summary_label.setText(f"{len(self.automation_sequence)} automation steps configured")
        except Exception as e:
            QMessageBox.warning(self, "Configuration Error", f"Error opening visual configuration dialog: {e}")
            print(f"Error in open_visual_config_dialog: {e}")

    def validate_and_accept(self):
        """Validate profile data before accepting the dialog."""
        try:
            # Validate profile name
            profile_name = self.profile_name_edit.text().strip()
            if not profile_name:
                QMessageBox.warning(self, "Validation Error", "Profile name is required.")
                self.tabs.setCurrentIndex(0)  # Switch to General tab
                self.profile_name_edit.setFocus()
                return
            
            # Validate VPN type
            vpn_type = self.vpn_type_combo.currentText()
            if not vpn_type:
                QMessageBox.warning(self, "Validation Error", "VPN type is required.")
                self.tabs.setCurrentIndex(1)  # Switch to VPN Connection tab
                self.vpn_type_combo.setFocus()
                return
            
            # Validate server address (required for most VPN connections)
            server = self.vpn_server_edit.text().strip()
            if not server:
                reply = QMessageBox.question(
                    self, 
                    "Missing Server Address", 
                    "Server address is empty. This may cause connection issues. Continue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    self.tabs.setCurrentIndex(1)  # Switch to VPN Connection tab
                    self.vpn_server_edit.setFocus()
                    return
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during validation: {e}")
            print(f"Error in validate_and_accept: {e}")
    
    def get_profile_data(self):
        """Get the profile data from the dialog."""
        profile_name = self.profile_name_edit.text().strip()
        vpn_type = self.vpn_type_combo.currentText()
        
        # Collect VPN-specific configuration
        vpn_params = {
            "server": self.vpn_server_edit.text().strip(),
            "username": self.vpn_username_edit.text().strip(),
            "group": self.vpn_group_edit.text().strip()
        }
        
        # Add model-specific fields if a model is selected
        if self.selected_model_id and self.model_field_widgets:
            for field_id, widget in self.model_field_widgets.items():
                if isinstance(widget, QLineEdit):
                    vpn_params[field_id] = widget.text().strip()
                elif isinstance(widget, QCheckBox):
                    vpn_params[field_id] = widget.isChecked()
                elif isinstance(widget, QComboBox):
                    vpn_params[field_id] = widget.currentText()
        
        # Build the complete profile data structure
        profile_data = {
            "name": profile_name,
            "type": vpn_type,
            "config": {
                "vpn_params": vpn_params,
                "automation_sequence": self.automation_sequence,
                "mapped_automation_sequence": self.mapped_automation_sequence,
                "selected_vpn_model_id": self.selected_model_id
            }
        }
        
        # Only include icon_path if it exists and is valid
        if self.icon_path and os.path.exists(self.icon_path):
            profile_data["config"]["icon_path"] = self.icon_path
        
        return profile_data
