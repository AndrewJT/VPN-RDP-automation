import os
import sys
import argparse
import logging
from typing import Optional

from logger import get_logger

logger = get_logger(__name__)

def ensure_headless_env(use_headless: bool):
    """
    Prepare environment variables and virtual display for headless runs.
    If running on Linux and pyvirtualdisplay is available, start an Xvfb display.
    """
    if not use_headless:
        return None

    # Ensure DISPLAY is set to something so pyautogui/Qt do not crash immediately.
    os.environ.setdefault("DISPLAY", ":0")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    logger.debug("Environment variables set for headless mode (DISPLAY and QT_QPA_PLATFORM).")

    # Try to start a pyvirtualdisplay (Xvfb) if available (on Linux)
    if sys.platform.startswith("linux"):
        try:
            from pyvirtualdisplay import Display
            display = Display(visible=0, size=(1280, 720))
            display.start()
            logger.info("Started virtual X display for headless mode using pyvirtualdisplay.")
            return display
        except Exception as e:
            logger.warning("pyvirtualdisplay is not available or failed to start. "
                           "If GUI automation needs a display, consider installing pyvirtualdisplay or using Xvfb. "
                           "Error: %s", e)
    return None

def import_app_components():
    try:
        from src.ui.main_window import MainWindow
        from src.core.connection_manager import ConnectionManager
        from src.vcal.vpn_manager import VPNManager
        from src.models.vpn_model_manager import VPNModelManager
        logger.debug("Imported application components successfully.")
        return MainWindow, ConnectionManager, VPNManager, VPNModelManager
    except Exception as e:
        logger.exception("Failed importing application components: %s", e)
        raise

def main(argv=None):
    parser = argparse.ArgumentParser(description="VPN Automation Application")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no GUI).")
    parser.add_argument("--config-dir", type=str, default=None, help="Directory for VPN profiles config.")
    args = parser.parse_args(argv)

    # Configure logging to console (can be extended to file/rotating logs)
    logging_level = logging.DEBUG if os.environ.get("VPN_APP_DEBUG") == "1" else logging.INFO
    logging.getLogger().setLevel(logging_level)

    display = ensure_headless_env(args.headless)

    # locate config dir
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_config_dir = os.path.join(base_dir, "vpn_profiles_config")
    config_dir = args.config_dir or default_config_dir
    os.makedirs(config_dir, exist_ok=True)
    logger.info("Using VPN profile configuration directory: %s", config_dir)

    # Import application modules (fail fast if missing)
    try:
        MainWindow, ConnectionManager, VPNManager, VPNModelManager = import_app_components()
    except Exception:
        logger.error("Cannot start application because required modules could not be imported.")
        if display:
            try:
                display.stop()
            except Exception:
                pass
        sys.exit(1)

    # Initialize core components
    vpn_manager = VPNManager(config_dir=config_dir)
    connection_manager = ConnectionManager(vpn_manager=vpn_manager)

    if args.headless:
        logger.info("Application initialized in headless mode. Exiting after initialization for tests.")
        # If you want to run headless sequences automatically, add CLI commands here.
    else:
        # Start Qt application
        try:
            from PyQt6.QtWidgets import QApplication
        except Exception as e:
            logger.exception("PyQt6 is required for GUI mode but could not be imported: %s", e)
            sys.exit(1)

        app = QApplication(sys.argv)
        main_window = MainWindow(connection_manager=connection_manager)
        main_window.show()
        exit_code = app.exec()
        logger.info("Application exited with code %s", exit_code)
        if display:
            try:
                display.stop()
            except Exception:
                pass
        sys.exit(exit_code)

if __name__ == "__main__":
    main()