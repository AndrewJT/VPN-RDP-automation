# /home/ubuntu/vpn_auto_app/src/ui/visual_config_dialog.py

import sys
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout, QComboBox, 
    QLineEdit, QLabel, QMessageBox, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal

# Attempt to import AutomationEngine, handling potential import errors
try:
    from ..automation_engine.engine import AutomationEngine
except ImportError:
    print("Warning: Could not import AutomationEngine. VisualConfigDialog will have limited functionality.")
    AutomationEngine = None

class VisualConfigDialog(QDialog):
    """Dialog for visually configuring automation sequences for VPN clients."""
    sequence_saved = pyqtSignal(list) # Signal to emit the saved sequence

    def __init__(self, parent=None, existing_sequence=None):
        super().__init__(parent)
        self.setWindowTitle("Visual VPN Automation Configurator")
        self.setMinimumSize(600, 500)

        self.automation_engine = AutomationEngine() if AutomationEngine else None
        self.current_sequence = existing_sequence if existing_sequence else []
        self.is_recording = False # Placeholder for actual recording state

        main_layout = QVBoxLayout(self)

        # --- Top: Controls for adding steps ---
        step_config_group = QGroupBox("Configure Automation Step")
        step_config_layout = QFormLayout()

        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems([
            "Click on Image", 
            "Type Text at Image", 
            "Type Text (Current Focus)", 
            "Press Key", 
            "Wait for Image to Appear", 
            "Wait for Image to Disappear",
            "Move Mouse to Image",
            "Comment"
        ])
        self.action_type_combo.currentTextChanged.connect(self._update_step_fields)

        self.target_image_path_edit = QLineEdit()
        self.browse_image_button = QPushButton("Browse...")
        self.browse_image_button.clicked.connect(self._browse_for_image)
        image_layout = QHBoxLayout()
        image_layout.addWidget(self.target_image_path_edit)
        image_layout.addWidget(self.browse_image_button)

        self.text_to_type_edit = QLineEdit()
        self.key_to_press_edit = QLineEdit()
        self.comment_edit = QLineEdit()
        self.timeout_edit = QLineEdit("10") # Default timeout for wait operations

        step_config_layout.addRow("Action Type:", self.action_type_combo)
        self.row_target_image = step_config_layout.addRow("Target Image Path:", image_layout)
        self.row_text_to_type = step_config_layout.addRow("Text to Type:", self.text_to_type_edit)
        self.row_key_to_press = step_config_layout.addRow("Key to Press:", self.key_to_press_edit)
        self.row_comment = step_config_layout.addRow("Comment:", self.comment_edit)
        self.row_timeout = step_config_layout.addRow("Timeout (sec):", self.timeout_edit)
        
        step_config_group.setLayout(step_config_layout)
        main_layout.addWidget(step_config_group)
        self._update_step_fields() # Initial field visibility

        self.add_step_button = QPushButton("Add Step to Sequence")
        self.add_step_button.clicked.connect(self._add_step)
        main_layout.addWidget(self.add_step_button)

        # --- Middle: List of current steps in sequence ---
        sequence_group = QGroupBox("Current Automation Sequence")
        sequence_layout = QVBoxLayout()
        self.sequence_list_widget = QListWidget()
        sequence_layout.addWidget(self.sequence_list_widget)

        sequence_controls_layout = QHBoxLayout()
        self.remove_step_button = QPushButton("Remove Selected Step")
        self.move_step_up_button = QPushButton("Move Up")
        self.move_step_down_button = QPushButton("Move Down")
        self.remove_step_button.clicked.connect(self._remove_step)
        self.move_step_up_button.clicked.connect(self._move_step_up)
        self.move_step_down_button.clicked.connect(self._move_step_down)
        sequence_controls_layout.addWidget(self.remove_step_button)
        sequence_controls_layout.addWidget(self.move_step_up_button)
        sequence_controls_layout.addWidget(self.move_step_down_button)
        sequence_layout.addLayout(sequence_controls_layout)
        sequence_group.setLayout(sequence_layout)
        main_layout.addWidget(sequence_group)

        # --- Bottom: Save/Cancel Buttons ---
        dialog_buttons_layout = QHBoxLayout()
        self.save_sequence_button = QPushButton("Save Sequence")
        self.cancel_button = QPushButton("Cancel")
        dialog_buttons_layout.addStretch()
        dialog_buttons_layout.addWidget(self.save_sequence_button)
        dialog_buttons_layout.addWidget(self.cancel_button)
        main_layout.addLayout(dialog_buttons_layout)

        self.save_sequence_button.clicked.connect(self._save_sequence)
        self.cancel_button.clicked.connect(self.reject)

        self._populate_sequence_list()

    def _update_step_fields(self):
        action = self.action_type_combo.currentText()
        self.target_image_path_edit.setVisible("Image" in action)
        self.browse_image_button.setVisible("Image" in action)
        self.text_to_type_edit.setVisible("Type Text" in action)
        self.key_to_press_edit.setVisible("Press Key" in action)
        self.comment_edit.setVisible("Comment" in action)
        self.timeout_edit.setVisible("Wait for" in action)
        
        # Adjust visibility of QFormLayout rows
        for i in range(self.row_target_image.formRow): # Assuming formRow is an accessible attribute or find another way
            if self.row_target_image.labelItem and self.row_target_image.fieldItem:
                 self.row_target_image.labelItem.widget().setVisible("Image" in action)
                 self.row_target_image.fieldItem.widget().setVisible("Image" in action)
            if self.row_text_to_type.labelItem and self.row_text_to_type.fieldItem:
                 self.row_text_to_type.labelItem.widget().setVisible("Type Text" in action)
                 self.row_text_to_type.fieldItem.widget().setVisible("Type Text" in action)
            if self.row_key_to_press.labelItem and self.row_key_to_press.fieldItem:
                 self.row_key_to_press.labelItem.widget().setVisible("Press Key" in action)
                 self.row_key_to_press.fieldItem.widget().setVisible("Press Key" in action)
            if self.row_comment.labelItem and self.row_comment.fieldItem:
                 self.row_comment.labelItem.widget().setVisible("Comment" in action)
                 self.row_comment.fieldItem.widget().setVisible("Comment" in action)
            if self.row_timeout.labelItem and self.row_timeout.fieldItem:
                 self.row_timeout.labelItem.widget().setVisible("Wait for" in action)
                 self.row_timeout.fieldItem.widget().setVisible("Wait for" in action)

    def _browse_for_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Target Image", "", "Image Files (*.png *.jpg *.bmp)")
        if file_name:
            self.target_image_path_edit.setText(file_name)

    def _add_step(self):
        action = self.action_type_combo.currentText()
        step_details = {"action": action}
        valid_step = True

        if "Image" in action:
            if not self.target_image_path_edit.text():
                QMessageBox.warning(self, "Input Error", "Target Image Path is required for this action.")
                valid_step = False
            step_details["target_image"] = self.target_image_path_edit.text()
        if "Type Text" in action:
            step_details["text"] = self.text_to_type_edit.text()
        if "Press Key" in action:
            if not self.key_to_press_edit.text():
                QMessageBox.warning(self, "Input Error", "Key to Press is required for this action.")
                valid_step = False
            step_details["key"] = self.key_to_press_edit.text()
        if "Comment" in action:
            step_details["comment"] = self.comment_edit.text()
        if "Wait for" in action:
            try:
                step_details["timeout"] = int(self.timeout_edit.text())
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Timeout must be a valid integer.")
                valid_step = False
        
        if valid_step:
            self.current_sequence.append(step_details)
            self._populate_sequence_list()
            # Clear fields for next step (optional)
            # self.target_image_path_edit.clear()
            # self.text_to_type_edit.clear()
            # self.key_to_press_edit.clear()
            # self.comment_edit.clear()

    def _populate_sequence_list(self):
        self.sequence_list_widget.clear()
        for i, step in enumerate(self.current_sequence):
            action = step.get("action", "Unknown Action")
            details_str = ", ".join(f"{k}: {v}" for k, v in step.items() if k != "action")
            self.sequence_list_widget.addItem(f"{i+1}. {action} - {details_str}")

    def _remove_step(self):
        current_row = self.sequence_list_widget.currentRow()
        if current_row >= 0 and current_row < len(self.current_sequence):
            del self.current_sequence[current_row]
            self._populate_sequence_list()

    def _move_step_up(self):
        current_row = self.sequence_list_widget.currentRow()
        if current_row > 0 and current_row < len(self.current_sequence):
            self.current_sequence.insert(current_row - 1, self.current_sequence.pop(current_row))
            self._populate_sequence_list()
            self.sequence_list_widget.setCurrentRow(current_row - 1)

    def _move_step_down(self):
        current_row = self.sequence_list_widget.currentRow()
        if current_row >= 0 and current_row < len(self.current_sequence) - 1:
            self.current_sequence.insert(current_row + 1, self.current_sequence.pop(current_row))
            self._populate_sequence_list()
            self.sequence_list_widget.setCurrentRow(current_row + 1)

    def _save_sequence(self):
        if not self.current_sequence:
            QMessageBox.information(self, "Empty Sequence", "No steps in the sequence to save.")
            # self.accept() # Or reject if empty sequence is not allowed
            return
        self.sequence_saved.emit(self.current_sequence)
        self.accept()

    def get_sequence(self):
        return self.current_sequence

# Example usage:
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Example existing sequence
    # test_sequence = [
    #     {"action": "Click on Image", "target_image": "login_button.png"},
    #     {"action": "Type Text at Image", "target_image": "username_field.png", "text": "myuser"},
    #     {"action": "Comment", "comment": "Entered username"}
    # ]
    # dialog = VisualConfigDialog(existing_sequence=test_sequence)
    dialog = VisualConfigDialog()
    
    def on_save(seq):
        print("Sequence Saved by Dialog:")
        for s in seq:
            print(s)

    dialog.sequence_saved.connect(on_save)

    if dialog.exec():
        print("Dialog accepted. Sequence emitted via signal or can be retrieved with get_sequence().")
        # final_sequence = dialog.get_sequence()
        # print("Final sequence:", final_sequence)
    else:
        print("Dialog cancelled.")
    sys.exit(app.exec())

