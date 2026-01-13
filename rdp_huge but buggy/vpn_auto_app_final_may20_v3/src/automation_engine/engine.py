# /home/ubuntu/vpn_auto_app/src/automation_engine/engine.py
import os
import time
from typing import Optional, Tuple, Any

# Attempt to import pyautogui and handle failure for headless environments
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
    pyautogui.PAUSE = 0.2  # Small pause after each pyautogui call
except (ImportError, KeyError, Exception) as e: # Catch generic Exception for Xlib/Display issues
    print(f"Warning: PyAutoGUI could not be initialized: {e}. Automation engine will run in a mocked mode.")
    PYAUTOGUI_AVAILABLE = False
    # Mock PyAutoGUI for headless environments or if import fails
    class MockPyAutoGUI:
        FAILSAFE = False
        PAUSE = 0.0

        def __getattr__(self, name):
            """Return a dummy function for any attribute not found."""
            def dummy_method(*args, **kwargs):
                print(f"MockPyAutoGUI: {name}({args}, {kwargs}) called (PyAutoGUI not available)")
                if name == "locateOnScreen" or name == "locateCenterOnScreen":
                    return None # Simulate image not found
                if name == "size":
                    return (0,0) # Simulate no screen size
                return None # Default for other methods
            return dummy_method

    pyautogui = MockPyAutoGUI()

class AutomationEngine:
    """
    Wraps GUI automation functionalities (e.g., using pyautogui) to provide
    a simpler interface for VPN drivers to interact with the screen, mouse, and keyboard.
    """

    def __init__(self, confidence=0.8, default_timeout=10, default_interval=0.5):
        """
        Initializes the Automation Engine.

        Args:
            confidence (float): Default confidence level for image recognition.
            default_timeout (int): Default timeout in seconds for operations like finding an image.
            default_interval (float): Default interval in seconds between checks when waiting for an image.
        """
        self.confidence = confidence
        self.default_timeout = default_timeout
        self.default_interval = default_interval
        self.pyautogui_available = PYAUTOGUI_AVAILABLE
        if not self.pyautogui_available:
            print("AutomationEngine: Running with mocked PyAutoGUI. Actual screen interactions will not occur.")

    def find_image_on_screen(self, image_path: str, confidence: Optional[float] = None, timeout: Optional[int] = None, interval: Optional[float] = None) -> Optional[Tuple[int, int, int, int]]:
        """
        Finds an image on the screen and returns its coordinates (left, top, width, height).
        """
        if not self.pyautogui_available: return None
        conf = confidence if confidence is not None else self.confidence
        to = timeout if timeout is not None else self.default_timeout
        inv = interval if interval is not None else self.default_interval
        
        start_time = time.time()
        while time.time() - start_time < to:
            try:
                location = pyautogui.locateOnScreen(image_path, confidence=conf)
                if location:
                    return location
            except pyautogui.ImageNotFoundException:
                pass 
            except Exception as e:
                print(f"Error finding image {image_path}: {e}") 
                return None
            time.sleep(inv)
        # print(f"Timeout finding image: {image_path}") # Can be noisy
        return None

    def click_on_image(self, image_path: str, confidence: Optional[float] = None, timeout: Optional[int] = None, button="left", clicks=1, interval_clicks=0.1) -> bool:
        """
        Finds an image on the screen and clicks on its center.
        """
        if not self.pyautogui_available: return False
        location = self.find_image_on_screen(image_path, confidence, timeout)
        if location:
            try:
                center_x, center_y = pyautogui.center(location)
                pyautogui.click(center_x, center_y, button=button, clicks=clicks, interval=interval_clicks)
                return True
            except Exception as e:
                print(f"Error clicking on image {image_path} at {location}: {e}")
                return False
        return False

    def type_text(self, text: str, interval_chars: float = 0.05) -> None:
        """
        Types the given text using the keyboard.
        """
        if not self.pyautogui_available: return
        try:
            pyautogui.typewrite(text, interval=interval_chars)
        except Exception as e:
            print(f"Error typing text: {e}")

    def press_key(self, key: str, presses: int = 1) -> None:
        """
        Presses a specific keyboard key.
        """
        if not self.pyautogui_available: return
        try:
            for _ in range(presses):
                pyautogui.press(key)
        except Exception as e:
            print(f"Error pressing key {key}: {e}")

    def hotkey(self, *args: Any) -> None:
        """
        Presses a combination of keys simultaneously (e.g., "ctrl", "c").
        """
        if not self.pyautogui_available: return
        try:
            pyautogui.hotkey(*args)
        except Exception as e:
            print(f"Error pressing hotkey {args}: {e}")

    def wait_for_image_to_appear(self, image_path: str, timeout: int = 30, confidence: Optional[float] = None) -> bool:
        """
        Waits for a specific image to appear on the screen.
        """
        if not self.pyautogui_available: return False
        location = self.find_image_on_screen(image_path, confidence=confidence, timeout=timeout)
        return location is not None

    def wait_for_image_to_disappear(self, image_path: str, timeout: int = 30, confidence: Optional[float] = None, interval: Optional[float] = None) -> bool:
        """
        Waits for a specific image to disappear from the screen.
        """
        if not self.pyautogui_available: return True # If no pyautogui, assume it disappeared
        inv = interval if interval is not None else self.default_interval
        start_time = time.time()
        while time.time() - start_time < timeout:
            location = self.find_image_on_screen(image_path, confidence=confidence, timeout=1) 
            if not location:
                return True
            time.sleep(inv)
        # print(f"Timeout waiting for image {image_path} to disappear.") # Can be noisy
        return False

    def get_screen_resolution(self) -> Tuple[int, int]:
        """
        Returns the current screen resolution (width, height).
        """
        if not self.pyautogui_available: return (0, 0)
        return pyautogui.size()

    def move_mouse(self, x: int, y: int, duration: float = 0.25) -> None:
        """
        Moves the mouse cursor to the specified coordinates.
        """
        if not self.pyautogui_available: return
        try:
            pyautogui.moveTo(x, y, duration=duration)
        except Exception as e:
            print(f"Error moving mouse to ({x}, {y}): {e}")

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button="left", clicks=1, interval_clicks=0.1) -> None:
        """
        Performs a mouse click at the current mouse position or specified coordinates.
        """
        if not self.pyautogui_available: return
        try:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks, interval=interval_clicks)
        except Exception as e:
            print(f"Error clicking at ({x}, {y}): {e}")

# Example usage (for testing this module directly):
if __name__ == "__main__":
    engine = AutomationEngine()
    print(f"PyAutoGUI Available: {engine.pyautogui_available}")
    print(f"Screen Resolution: {engine.get_screen_resolution()}")
    
    # Test a mocked call if pyautogui is not available
    engine.type_text("Hello, Test!")
    engine.press_key("enter")
    found = engine.find_image_on_screen("non_existent_image.png", timeout=1)
    print(f"Found non_existent_image.png: {found}")

    print("Automation Engine module loaded.")

