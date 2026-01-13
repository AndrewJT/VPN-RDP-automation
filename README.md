# VPN Automation Application

This application allows users to manage and automate connections to various VPN clients and subsequently launch RDP or browser sessions.

## Features

-   Manage VPN profiles (add, edit, delete).
-   Visually configure automation sequences for connecting to VPN clients (requires a graphical environment).
-   Connect to configured VPNs.
-   Launch RDP or browser sessions after a successful VPN connection.
-   Core logic tested via a headless script.

## Project Structure

-   `main.py`: Main entry point to launch the GUI application.
-   `headless_test.py`: Script to test core backend logic without GUI (useful in environments without a display server).
-   `src/`:
    -   `core/`: Contains `connection_manager.py` and `remote_access_manager.py` for orchestrating connections and remote access.
    -   `vcal/`: VPN Client Abstraction Layer, including `base_vpn_driver.py`, `vpn_manager.py`, and specific driver implementations in `drivers/`.
    -   `ui/`: Contains PyQt6 UI components like `main_window.py` and `visual_config_dialog.py`.
    -   `automation_engine/`: Contains `engine.py` which wraps PyAutoGUI for GUI automation.
    -   `__init__.py`: Makes `src` a Python package.
-   `vpn_automation_app_architecture.md`: The architecture design document.
-   `requirements.txt`: Python dependencies.

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.8+ installed.
    *   A graphical environment (e.g., Windows with a display server) is required for the full GUI application and GUI automation features to work. The sandbox environment where this was developed is headless, so full GUI testing was not possible.

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    Navigate to the project root directory (`vpn_auto_app`) and run:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `PyQt6` and `PyAutoGUI`.

## Running the Application

1.  **GUI Application (Requires a Display Server):**
    Navigate to the `vpn_auto_app` directory and run:
    ```bash
    python3 main.py
    ```
    **Note:** The GUI automation features (interacting with actual VPN client windows) will only work if the respective VPN client software is installed on your system and the visual automation sequences are correctly configured for them using the application's Visual Configuration Tool.

2.  **Headless Test (For Core Logic Validation):**
    This script tests the backend logic without launching the GUI or relying on PyAutoGUI for screen interactions. It can be run in any environment where Python is installed.
    Navigate to the `vpn_auto_app` directory and run:
    ```bash
    python3 headless_test.py
    ```

## Important Considerations for GUI Automation

-   **PyAutoGUI and Display Servers:** PyAutoGUI, used for visual automation, requires an active display server (e.g., X11 on Linux, or a standard Windows/macOS desktop environment). It will not work in a purely headless server environment without a virtual display like Xvfb.
-   **VPN Client GUIs:** The visual automation sequences you configure will be specific to the GUI layout and appearance of the VPN client versions you are using. If a VPN client updates its UI, you may need to re-configure the automation sequence for it.
-   **Image Recognition:** The Visual Configuration Tool relies on image recognition. Ensure the images captured for automation steps are clear, unique, and representative of what will be on the screen.

## Further Development

-   Implement concrete VPN drivers in `src/vcal/drivers/` for specific VPN clients (e.g., FortiClient, GlobalProtect, Citrix Gateway, Parallels) by inheriting from `BaseVPNDriver` and using the `AutomationEngine`.
-   Enhance error handling and logging throughout the application.
-   Securely manage sensitive information like VPN credentials (e.g., using a system keychain or encrypted storage).
-   Add more sophisticated automation actions to the `AutomationEngine` and Visual Configuration Tool.

