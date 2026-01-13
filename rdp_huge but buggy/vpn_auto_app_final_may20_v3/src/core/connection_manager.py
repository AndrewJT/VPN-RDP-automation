# /home/ubuntu/vpn_auto_app/src/core/connection_manager.py

from ..vcal.vpn_manager import VPNManager
from ..vcal.base_vpn_driver import BaseVPNDriver
from .remote_access_manager import RemoteAccessManager
from typing import Optional, Dict, Any
import traceback # For detailed error logging

class ConnectionManager:
    """
    Orchestrates the process of selecting a VPN profile, establishing the VPN connection,
    and then initiating remote access (RDP or browser) if configured.
    This acts as a central part of the "Core Module" from the architecture design.
    """

    def __init__(self, vpn_manager: VPNManager):
        """
        Initializes the ConnectionManager.

        Args:
            vpn_manager (VPNManager): An instance of the VPNManager to interact with VPN profiles and drivers.
        """
        self.vpn_manager = vpn_manager
        self.remote_access_manager = RemoteAccessManager()
        self.current_active_profile: Optional[str] = None

    def list_vpn_profiles(self) -> list[Dict[str, Any]]:
        """
        Retrieves a list of all available VPN profiles.

        Returns:
            list[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a VPN profile.
        """
        try:
            return self.vpn_manager.get_all_profiles()
        except Exception as e:
            print(f"Error listing VPN profiles in ConnectionManager: {e}\n{traceback.format_exc()}")
            return []

    def connect_to_profile(self, profile_name: str) -> tuple[bool, str]:
        """
        Attempts to connect to a VPN using the specified profile name.
        If successful and remote access is configured, it will also attempt to initiate that.

        Args:
            profile_name (str): The name of the VPN profile to connect to.

        Returns:
            tuple[bool, str]: A tuple containing a boolean indicating success (True) or failure (False),
                              and a message describing the outcome.
        """
        try:
            if self.current_active_profile:
                if self.current_active_profile == profile_name:
                    return True, f"Profile 	'{profile_name}'	 is already connected."
                else:
                    return False, f"Another profile (	'{self.current_active_profile}'	) is currently active. Please disconnect it first."

            profile_data = self.vpn_manager.load_profile(profile_name)
            if not profile_data:
                return False, f"Profile 	'{profile_name}'	 not found."

            vpn_type = profile_data.get("type")
            vpn_config = profile_data.get("config", {})

            if not vpn_type:
                return False, f"VPN type not specified in profile 	'{profile_name}'	."

            print(f"Attempting to connect profile: {profile_name} (Type: {vpn_type})")
            # Ensure vpn_manager.connect is also robust
            connection_success, conn_msg = self.vpn_manager.connect(profile_name, vpn_type, vpn_config)

            if connection_success:
                self.current_active_profile = profile_name
                message = f"Successfully connected to VPN profile: {profile_name}. {conn_msg}"
                print(message)
                
                remote_access_config = vpn_config.get("remote_access")
                if remote_access_config:
                    ra_type = remote_access_config.get("type")
                    ra_details = remote_access_config.get("details")
                    if ra_type and ra_details and ra_type != "None":
                        print(f"Initiating remote access ({ra_type}) for profile {profile_name}...")
                        ra_success, ra_message = self.remote_access_manager.initiate_access(ra_type, ra_details)
                        message += f" {ra_message}"
                    elif ra_type == "None":
                        message += " Remote access type is 'None'."
                    else:
                        message += " Remote access configured but type or details missing."
                else:
                    message += " No remote access configured for this profile."
                return True, message
            else:
                return False, f"Failed to connect to VPN profile: {profile_name}. Reason: {conn_msg}"
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"CRITICAL ERROR in ConnectionManager.connect_to_profile for '{profile_name}': {e}\n{error_details}")
            # Ensure state is reset if a critical error occurs mid-process
            self.current_active_profile = None 
            return False, f"An unexpected critical error occurred while connecting to '{profile_name}': {e}. Check logs."

    def disconnect_current_profile(self) -> tuple[bool, str]:
        """
        Disconnects the currently active VPN profile.

        Returns:
            tuple[bool, str]: A tuple containing a boolean indicating success (True) or failure (False),
                              and a message describing the outcome.
        """
        try:
            if not self.current_active_profile:
                return True, "No VPN profile is currently active."

            profile_name_to_disconnect = self.current_active_profile
            print(f"Attempting to disconnect profile: {profile_name_to_disconnect}")
            # Ensure vpn_manager.disconnect is also robust
            disconnection_success, disconn_msg = self.vpn_manager.disconnect(profile_name_to_disconnect)

            if disconnection_success:
                self.current_active_profile = None
                return True, f"Successfully disconnected from VPN profile: {profile_name_to_disconnect}. {disconn_msg}"
            else:
                return False, f"Failed to disconnect VPN profile: {profile_name_to_disconnect}. Reason: {disconn_msg}"
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"CRITICAL ERROR in ConnectionManager.disconnect_current_profile for '{self.current_active_profile}': {e}\n{error_details}")
            return False, f"An unexpected critical error occurred while disconnecting: {e}. Check logs."


    def get_current_connection_status(self) -> str:
        """
        Gets the status of the currently active VPN connection.

        Returns:
            str: The connection status, or "No active connection" if no profile is active.
        """
        try:
            if not self.current_active_profile:
                return "No active connection"
            return self.vpn_manager.get_connection_status(self.current_active_profile)
        except Exception as e:
            print(f"Error getting connection status: {e}\n{traceback.format_exc()}")
            return "Error retrieving status"

# Example Usage (Conceptual - would be driven by UI or main app logic)
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    from vcal.vpn_manager import VPNManager 
    from vcal.base_vpn_driver import BaseVPNDriver
    
    class DummyVPNManager(VPNManager):
        def __init__(self):
            super().__init__(config_dir="./temp_vpn_config_cm_test")
            class DummyDriver(BaseVPNDriver):
                def connect(self) -> tuple[bool, str]: 
                    self.is_connected = True; 
                    msg = f"{self.profile_name} connected by dummy driver."
                    print(msg)
                    return True, msg
                def disconnect(self) -> tuple[bool, str]: 
                    self.is_connected = False; 
                    msg = f"{self.profile_name} disconnected by dummy driver."
                    print(msg)
                    return True, msg
                def get_status(self) -> str: return "Connected" if self.is_connected else "Disconnected"
            self.register_driver("dummyvpn", DummyDriver)
        
        # Override connect and disconnect to return tuple as expected by updated ConnectionManager
        def connect(self, profile_name: str, vpn_type: str, vpn_config: dict) -> tuple[bool, str]:
            driver = self.create_connection(profile_name, vpn_type, vpn_config)
            if not driver:
                return False, "Failed to create dummy driver instance."
            success, msg = driver.connect()
            if success:
                self.active_connections[profile_name] = driver
            return success, msg

        def disconnect(self, profile_name: str) -> tuple[bool, str]:
            if profile_name not in self.active_connections:
                return True, "Dummy profile not active."
            driver = self.active_connections[profile_name]
            success, msg = driver.disconnect()
            if success:
                del self.active_connections[profile_name]
            return success, msg

    print("Initializing ConnectionManager for testing...")
    test_vpn_manager = DummyVPNManager()
    conn_manager = ConnectionManager(test_vpn_manager)

    profile1_name = "TestDummyVPN_with_RDP"
    profile1_type = "dummyvpn"
    profile1_config = {
        "vpn_params": {"server": "dummy.server.com"}, 
        "automation_sequence": [],
        "remote_access": {
            "type": "RDP",
            "details": {"hostname": "your-test-rdp-server.com"}
        }
    }
    test_vpn_manager.save_profile(profile1_name, profile1_type, profile1_config)
    print(f"Saved profile: {profile1_name}")

    profile2_name = "TestDummyVPN_with_Browser"
    profile2_config = {
        "vpn_params": {"server": "dummy.server.com"}, 
        "automation_sequence": [],
        "remote_access": {
            "type": "Browser",
            "details": {"url": "https://www.google.com"}
        }
    }
    test_vpn_manager.save_profile(profile2_name, profile1_type, profile2_config)
    print(f"Saved profile: {profile2_name}")

    profiles = conn_manager.list_vpn_profiles()
    print("Available profiles:", [p.get("name") for p in profiles])

    print("\n--- Testing RDP Profile ---")
    success, message = conn_manager.connect_to_profile(profile1_name)
    print(f"Connection attempt (RDP): Success={success}, Message='{message}'")
    print(f"Current status: {conn_manager.get_current_connection_status()}")
    success, message = conn_manager.disconnect_current_profile()
    print(f"Disconnection attempt (RDP): Success={success}, Message='{message}'")

    print("\n--- Testing Browser Profile ---")
    success, message = conn_manager.connect_to_profile(profile2_name)
    print(f"Connection attempt (Browser): Success={success}, Message='{message}'")
    print(f"Current status: {conn_manager.get_current_connection_status()}")
    success, message = conn_manager.disconnect_current_profile()
    print(f"Disconnection attempt (Browser): Success={success}, Message='{message}'")

    test_vpn_manager.delete_profile(profile1_name)
    test_vpn_manager.delete_profile(profile2_name)
    import shutil
    if os.path.exists("./temp_vpn_config_cm_test"):
        shutil.rmtree("./temp_vpn_config_cm_test")
    print("\nConnectionManager integration test complete.")

