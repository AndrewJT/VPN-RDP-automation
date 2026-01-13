# /home/ubuntu/vpn_auto_app/src/vcal/vpn_manager.py

from typing import Dict, List, Optional, Type
import importlib
import os
import json
import traceback # For detailed error logging

from .base_vpn_driver import BaseVPNDriver

class VPNManager:
    """
    Manages the available VPN drivers and provides an interface for the core application
    to interact with them without knowing the specific implementation details.
    """

    def __init__(self, config_dir: str = None):
        """
        Initializes the VPN Manager.

        Args:
            config_dir (str, optional): Directory where VPN profiles and automation sequences are stored.
                                       Defaults to None, in which case a default location will be used.
        """
        self.config_dir = config_dir or os.path.expanduser("~/vpn_auto_app_config")
        self.drivers_dir = os.path.dirname(os.path.abspath(__file__))
        self.registered_drivers: Dict[str, Type[BaseVPNDriver]] = {}
        self.active_connections: Dict[str, BaseVPNDriver] = {}
        
        os.makedirs(self.config_dir, exist_ok=True)
        self._discover_drivers()

    def _discover_drivers(self):
        """
        Scans the drivers directory for available VPN client drivers and registers them.
        This method should be expanded to dynamically load drivers.
        """
        drivers_path = os.path.join(self.drivers_dir, "drivers")
        if not os.path.exists(drivers_path):
            print(f"Drivers directory not found: {drivers_path}. Cannot discover drivers.")
            return

        for filename in os.listdir(drivers_path):
            if filename.endswith("_driver.py") and not filename.startswith("__"):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f".drivers.{module_name}", package=__package__)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, BaseVPNDriver) and attr != BaseVPNDriver:
                            # Use a consistent naming convention for driver_type, e.g., module_name without "_driver"
                            driver_type_key = module_name.replace("_driver", "").lower()
                            self.register_driver(driver_type_key, attr)
                except ImportError as e:
                    print(f"Error importing driver module {module_name}: {e}\n{traceback.format_exc()}")
                except Exception as e_gen:
                    print(f"General error processing driver {module_name}: {e_gen}\n{traceback.format_exc()}")
        
        if not self.registered_drivers:
            print("VPN Manager: No drivers were dynamically discovered or registered. Check drivers directory and implementations.")
        else:
            print(f"VPN Manager: Successfully discovered and registered drivers: {list(self.registered_drivers.keys())}")

    def register_driver(self, driver_type: str, driver_class: Type[BaseVPNDriver]):
        """
        Registers a VPN driver class for a specific VPN client type.
        """
        self.registered_drivers[driver_type.lower()] = driver_class
        print(f"Registered driver for VPN type: {driver_type}")

    def get_available_driver_types(self) -> List[str]:
        """
        Returns a list of available VPN client types that have registered drivers.
        """
        return list(self.registered_drivers.keys())

    def create_connection(self, profile_name: str, vpn_type: str, vpn_config: dict) -> Optional[BaseVPNDriver]:
        """
        Creates a VPN connection instance for the specified profile and VPN type.
        """
        try:
            vpn_type_lower = vpn_type.lower()
            if vpn_type_lower not in self.registered_drivers:
                print(f"Error: No driver registered for VPN type 	'{vpn_type_lower}	'")
                return None
            
            driver_class = self.registered_drivers[vpn_type_lower]
            # Pass the full vpn_config to the driver, it can extract what it needs
            driver = driver_class(profile_name, vpn_config) 
            return driver
        except Exception as e:
            print(f"Error creating connection for 	'{profile_name}	' (type 	'{vpn_type}	'): {e}\n{traceback.format_exc()}")
            return None

    def connect(self, profile_name: str, vpn_type: str, vpn_config: dict) -> tuple[bool, str]:
        """
        Creates a VPN connection instance and attempts to establish the connection.
        Returns a tuple (success_boolean, message_string).
        """
        try:
            driver = self.create_connection(profile_name, vpn_type, vpn_config)
            if not driver:
                return False, f"Failed to create driver for VPN type 	'{vpn_type}	'."
            
            success, message = driver.connect() # Driver.connect() should return (bool, str)
            if success:
                self.active_connections[profile_name] = driver
            return success, message
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"CRITICAL ERROR in VPNManager.connect for 	'{profile_name}	': {e}\n{error_details}")
            return False, f"Unexpected error in VPNManager during connect: {e}"

    def disconnect(self, profile_name: str) -> tuple[bool, str]:
        """
        Disconnects an active VPN connection.
        Returns a tuple (success_boolean, message_string).
        """
        try:
            if profile_name not in self.active_connections:
                return True, "Profile was not actively connected."
            
            driver = self.active_connections[profile_name]
            success, message = driver.disconnect() # Driver.disconnect() should return (bool, str)
            
            if success:
                del self.active_connections[profile_name]
            return success, message
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"CRITICAL ERROR in VPNManager.disconnect for 	'{profile_name}	': {e}\n{error_details}")
            return False, f"Unexpected error in VPNManager during disconnect: {e}"

    def get_connection_status(self, profile_name: str) -> str:
        """
        Gets the status of a VPN connection.
        """
        try:
            if profile_name not in self.active_connections:
                return "Not Connected"
            return self.active_connections[profile_name].get_status()
        except Exception as e:
            print(f"Error getting connection status for 	'{profile_name}	': {e}\n{traceback.format_exc()}")
            return "Error retrieving status"

    def save_profile(self, profile_name: str, vpn_type: str, vpn_config: dict) -> bool:
        """
        Saves a VPN profile configuration to disk.
        """
        profiles_dir = os.path.join(self.config_dir, "profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        
        profile_path = os.path.join(profiles_dir, f"{profile_name}.json")
        profile_data = {
            "name": profile_name,
            "type": vpn_type.lower(),
            "config": vpn_config
        }
        
        try:
            with open(profile_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving profile {profile_name}: {e}\n{traceback.format_exc()}")
            return False

    def load_profile(self, profile_name: str) -> Optional[dict]:
        """
        Loads a VPN profile configuration from disk.
        """
        profile_path = os.path.join(self.config_dir, "profiles", f"{profile_name}.json")
        if not os.path.exists(profile_path):
            # print(f"Profile {profile_name} not found at {profile_path}") # Can be noisy
            return None
        try:
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
            return profile_data
        except Exception as e:
            print(f"Error loading profile {profile_name}: {e}\n{traceback.format_exc()}")
            return None

    def get_all_profiles(self) -> List[dict]:
        """
        Gets a list of all saved VPN profiles.
        """
        profiles_dir = os.path.join(self.config_dir, "profiles")
        if not os.path.exists(profiles_dir):
            return [] # No profiles directory means no profiles
            
        profiles = []
        for filename in os.listdir(profiles_dir):
            if filename.endswith('.json'):
                profile_name = filename[:-5]
                profile_data = self.load_profile(profile_name)
                if profile_data:
                    profiles.append(profile_data)
        return profiles

    def delete_profile(self, profile_name: str) -> bool:
        """
        Deletes a VPN profile.
        """
        profile_path = os.path.join(self.config_dir, "profiles", f"{profile_name}.json")
        if not os.path.exists(profile_path):
            print(f"Profile {profile_name} not found for deletion.")
            return False
        try:
            os.remove(profile_path)
            return True
        except Exception as e:
            print(f"Error deleting profile {profile_name}: {e}\n{traceback.format_exc()}")
            return False

