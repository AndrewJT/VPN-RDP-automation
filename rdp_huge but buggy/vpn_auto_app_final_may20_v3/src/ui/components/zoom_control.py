import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QComboBox, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QWheelEvent

class ZoomManager:
    """Manages application-wide zoom settings."""
    
    def __init__(self):
        """Initialize the zoom manager with default settings."""
        self.settings = QSettings("VPNAutoApp", "ZoomSettings")
        self.zoom_factor = self.settings.value("zoom_factor", 1.0, type=float)
        
    def get_zoom_factor(self):
        """Get the current zoom factor."""
        return self.zoom_factor
        
    def set_zoom_factor(self, factor):
        """Set and save the zoom factor."""
        self.zoom_factor = max(0.5, min(2.0, factor))  # Limit between 50% and 200%
        self.settings.setValue("zoom_factor", self.zoom_factor)
        return self.zoom_factor
        
    def increase_zoom(self, step=0.1):
        """Increase zoom by step amount."""
        return self.set_zoom_factor(self.zoom_factor + step)
        
    def decrease_zoom(self, step=0.1):
        """Decrease zoom by step amount."""
        return self.set_zoom_factor(self.zoom_factor - step)
        
    def reset_zoom(self):
        """Reset zoom to default (100%)."""
        return self.set_zoom_factor(1.0)

class ZoomControlWidget(QWidget):
    """Widget for controlling zoom level."""
    
    zoom_changed = pyqtSignal(float)
    
    def __init__(self, zoom_manager=None, parent=None):
        """Initialize the zoom control widget."""
        super().__init__(parent)
        
        self.zoom_manager = zoom_manager or ZoomManager()
        self._init_ui()
        
        # Enable mouse tracking for wheel events
        self.setMouseTracking(True)
        
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Zoom slider
        slider_layout = QHBoxLayout()
        
        zoom_out_label = QLabel("50%")
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(50)
        self.zoom_slider.setMaximum(200)
        self.zoom_slider.setValue(int(self.zoom_manager.get_zoom_factor() * 100))
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setTickInterval(25)
        zoom_in_label = QLabel("200%")
        
        self.zoom_slider.valueChanged.connect(self._on_slider_changed)
        
        slider_layout.addWidget(zoom_out_label)
        slider_layout.addWidget(self.zoom_slider)
        slider_layout.addWidget(zoom_in_label)
        
        layout.addLayout(slider_layout)
        
        # Current zoom display
        self.zoom_label = QLabel(f"Current zoom: {int(self.zoom_manager.get_zoom_factor() * 100)}%")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.zoom_label)
        
        # Preset buttons
        presets_layout = QHBoxLayout()
        
        self.zoom_50_btn = QPushButton("50%")
        self.zoom_75_btn = QPushButton("75%")
        self.zoom_100_btn = QPushButton("100%")
        self.zoom_125_btn = QPushButton("125%")
        self.zoom_150_btn = QPushButton("150%")
        self.zoom_200_btn = QPushButton("200%")
        
        self.zoom_50_btn.clicked.connect(lambda: self._set_zoom(0.5))
        self.zoom_75_btn.clicked.connect(lambda: self._set_zoom(0.75))
        self.zoom_100_btn.clicked.connect(lambda: self._set_zoom(1.0))
        self.zoom_125_btn.clicked.connect(lambda: self._set_zoom(1.25))
        self.zoom_150_btn.clicked.connect(lambda: self._set_zoom(1.5))
        self.zoom_200_btn.clicked.connect(lambda: self._set_zoom(2.0))
        
        presets_layout.addWidget(self.zoom_50_btn)
        presets_layout.addWidget(self.zoom_75_btn)
        presets_layout.addWidget(self.zoom_100_btn)
        presets_layout.addWidget(self.zoom_125_btn)
        presets_layout.addWidget(self.zoom_150_btn)
        presets_layout.addWidget(self.zoom_200_btn)
        
        layout.addLayout(presets_layout)
        
    def _on_slider_changed(self, value):
        """Handle slider value changes."""
        zoom_factor = value / 100
        self.zoom_label.setText(f"Current zoom: {value}%")
        self.zoom_manager.set_zoom_factor(zoom_factor)
        self.zoom_changed.emit(zoom_factor)
        
    def _set_zoom(self, factor):
        """Set zoom to a specific factor."""
        self.zoom_slider.setValue(int(factor * 100))
        # The slider's valueChanged signal will trigger _on_slider_changed
        
    def increase_zoom(self):
        """Increase zoom by 10%."""
        current_value = self.zoom_slider.value()
        new_value = min(200, current_value + 10)
        self.zoom_slider.setValue(new_value)
        return new_value / 100
        
    def decrease_zoom(self):
        """Decrease zoom by 10%."""
        current_value = self.zoom_slider.value()
        new_value = max(50, current_value - 10)
        self.zoom_slider.setValue(new_value)
        return new_value / 100
        
    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.zoom_slider.setValue(100)
        return 1.0
        
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel events for zooming when Ctrl is pressed."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.increase_zoom()
            elif delta < 0:
                self.decrease_zoom()
            event.accept()
        else:
            super().wheelEvent(event)

class ZoomSettingsDialog(QDialog):
    """Dialog for adjusting zoom settings."""
    
    zoom_changed = pyqtSignal(float)
    
    def __init__(self, zoom_manager=None, parent=None):
        """Initialize the zoom settings dialog."""
        super().__init__(parent)
        
        self.zoom_manager = zoom_manager or ZoomManager()
        self.setWindowTitle("Zoom Settings")
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Zoom control widget
        self.zoom_control = ZoomControlWidget(self.zoom_manager)
        self.zoom_control.zoom_changed.connect(self._on_zoom_changed)
        layout.addWidget(self.zoom_control)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def _on_zoom_changed(self, factor):
        """Handle zoom changes from the control widget."""
        self.zoom_changed.emit(factor)
        
    def get_zoom_factor(self):
        """Get the current zoom factor."""
        return self.zoom_manager.get_zoom_factor()
        
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel events for zooming when Ctrl is pressed."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_control.increase_zoom()
            elif delta < 0:
                self.zoom_control.decrease_zoom()
            event.accept()
        else:
            super().wheelEvent(event)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = ZoomSettingsDialog()
    if dialog.exec():
        print(f"Zoom set to: {dialog.get_zoom_factor()}")
    else:
        print("Zoom settings canceled")
