import sys
import os
import shutil
import tempfile
import traceback
from logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logger.level)  # inherit root level if set externally

logger.info("--- Starting Headless Test for VPN Automation App ---")

# Ensure src package import works when running from repo root
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = current_dir  # adjust if this file lives in repository root
sys.path.insert(0, repo_root)

try:
    from src.core.connection_manager import ConnectionManager
    from src.vcal.vpn_manager import VPNManager
    from src.vcal.base_vpn_driver import BaseVPNDriver
    logger.info("Core backend modules imported successfully.")
except Exception as e:
    logger.exception("FATAL: Could not import core backend modules: %s", e)
    raise SystemExit(1)

class HeadlessDummyFortiClientDriver(BaseVPNDriver):
    VPN_TYPE_ID = "forticlient_headless_dummy"

    def __init__(self, profile_name: str, config: dict, automation_engine_mock=None):
        super().__init__(profile_name, config, automation_engine_mock)
        self.log_prefix = f"[HL-Forti-{profile_name}]"
        logger.debug("%s Initialized.", self.log_prefix)

    def connect(self) -> tuple[bool, str]:
        logger.debug("%s Attempting connect...", self.log_prefix)
        # simulate automation steps if present
        for step in self.vpn_config.get("automation_sequence", []):
            logger.debug("%s Simulating step: %s", self.log_prefix, step)
        self.is_connected = True
        msg = f"{self.log_prefix} Connected."
        logger.info(msg)
        return True, msg

    def disconnect(self) -> tuple[bool, str]:
        logger.debug("%s Attempting disconnect...", self.log_prefix)
        self.is_connected = False
        msg = f"{self.log_prefix} Disconnected."
        logger.info(msg)
        return True, msg

    def get_status(self) -> str:
        status = "Connected" if self.is_connected else "Disconnected"
        logger.debug("%s Status: %s", self.log_prefix, status)
        return status

class HeadlessDummyGlobalProtectDriver(HeadlessDummyFortiClientDriver):
    VPN_TYPE_ID = "globalprotect_headless_dummy"
    # reuses the same logic; only VPN_TYPE_ID differs

def run_headless_test():
    temp_dir = tempfile.mkdtemp(prefix="headless_test_vpn_profiles_")
    logger.info("Using temporary VPN profile config directory: %s", temp_dir)

    try:
        vpn_manager = VPNManager(config_dir=temp_dir)
        vpn_manager.register_driver(HeadlessDummyFortiClientDriver.VPN_TYPE_ID, HeadlessDummyFortiClientDriver)
        vpn_manager.register_driver(HeadlessDummyGlobalProtectDriver.VPN_TYPE_ID, HeadlessDummyGlobalProtectDriver)
        logger.info("Registered headless drivers: %s", vpn_manager.get_available_driver_types())

        connection_manager = ConnectionManager(vpn_manager=vpn_manager)
        logger.info("ConnectionManager initialized.")

        # Test 1: Save, load
        profile_name = "WorkVPN_Forti"
        profile_type = HeadlessDummyFortiClientDriver.VPN_TYPE_ID
        profile_config = {
            "vpn_params": {"server": "forti.example.com", "username": "testuser"},
            "automation_sequence": [
                {"action": "type_text", "text": "forti.example.com"},
                {"action": "click_image", "image_path": "forti_connect_button.png"}
            ],
            "remote_access": {"type": "RDP", "details": {"hostname": "desktop-01"}}
        }
        saved = vpn_manager.save_profile(profile_name, profile_type, profile_config)
        assert saved, "Failed to save profile"

        loaded = vpn_manager.load_profile(profile_name)
        assert loaded and loaded.get("name") == profile_name, "Saved profile failed to load or mismatch"

        # Test 2: Connect/disconnect
        conn_success, conn_msg = connection_manager.connect_to_profile(profile_name)
        logger.info("Connect attempt: success=%s, msg=%s", conn_success, conn_msg)
        assert conn_success, "Connection failed in headless test"
        assert connection_manager.get_current_connection_status() in ("Connected", True, "True",), "Bad status after connect"

        disc_success, disc_msg = connection_manager.disconnect_current_profile()
        logger.info("Disconnect attempt: success=%s, msg=%s", disc_success, disc_msg)
        assert disc_success, "Disconnect failed in headless test"
        assert connection_manager.get_current_connection_status() in ("Disconnected", False, "False",), "Bad status after disconnect"

        # Test 3: Delete profile
        deleted = vpn_manager.delete_profile(profile_name)
        assert deleted, "Failed to delete profile"
        assert not vpn_manager.load_profile(profile_name), "Profile still present after delete"

        logger.info("Headless test completed successfully.")
        return 0
    except AssertionError:
        logger.exception("Assertion failed during headless test.")
        traceback.print_exc()
        return 2
    except Exception:
        logger.exception("Unexpected error during headless test.")
        traceback.print_exc()
        return 1
    finally:
        try:
            shutil.rmtree(temp_dir)
            logger.info("Removed temporary config directory.")
        except Exception:
            logger.warning("Could not remove temporary directory: %s", temp_dir)

if __name__ == "__main__":
    exit_code = run_headless_test()
    sys.exit(exit_code)