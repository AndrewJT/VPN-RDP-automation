import os
import json
from typing import List, Dict, Optional, Any

class RDPProfileManager:
    """Manages storage and retrieval of RDP connection profiles."""

    def __init__(self, profiles_dir: str):
        """
        Initializes the RDPProfileManager.

        Args:
            profiles_dir (str): The directory where RDP profiles will be stored.
        """
        self.profiles_dir = profiles_dir
        self.profiles_file = os.path.join(self.profiles_dir, "rdp_profiles.json")
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir, exist_ok=True)
        self.profiles: Dict[str, Dict[str, Any]] = self._load_profiles_from_file()

    def _load_profiles_from_file(self) -> Dict[str, Dict[str, Any]]:
        """Loads RDP profiles from the JSON file."""
        if not os.path.exists(self.profiles_file):
            return {}
        try:
            with open(self.profiles_file, "r") as f:
                data = json.load(f)
                # Ensure it's a dictionary (profile_name: profile_data)
                if isinstance(data, dict):
                    return data
                # Handle old list format if necessary, or just return empty for new structure
                print(f"Warning: rdp_profiles.json is not in the expected format. Starting fresh.")
                return {}
        except json.JSONDecodeError:
            print(f"Error decoding {self.profiles_file}. Starting with an empty profile list.")
            return {}
        except Exception as e:
            print(f"An unexpected error occurred while loading RDP profiles: {e}")
            return {}

    def _save_profiles_to_file(self) -> None:
        """Saves the current RDP profiles to the JSON file."""
        try:
            with open(self.profiles_file, "w") as f:
                json.dump(self.profiles, f, indent=4)
        except Exception as e:
            print(f"Error saving RDP profiles to {self.profiles_file}: {e}")

    def list_profiles(self) -> List[Dict[str, Any]]:
        """Returns a list of all RDP profiles."""
        # Convert the dictionary of profiles to a list of profile dicts, adding 'name' key
        return [dict(profile_data, name=name) for name, profile_data in self.profiles.items()]

    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific RDP profile by name."""
        profile_data = self.profiles.get(name)
        if profile_data:
            return dict(profile_data, name=name) # Add name to the returned dict
        return None

    def save_profile(self, profile_data: Dict[str, Any]) -> bool:
        """
        Saves an RDP profile. If a profile with the same name exists, it's updated.
        The profile_data dictionary should contain a 'name' key.
        """
        name = profile_data.get("name")
        if not name:
            print("Error: Profile name is required to save an RDP profile.")
            return False
        
        # Store the profile without the 'name' key in the internal dict, as name is the key
        data_to_store = {k: v for k, v in profile_data.items() if k != "name"}
        self.profiles[name] = data_to_store
        self._save_profiles_to_file()
        return True

    def delete_profile(self, name: str) -> bool:
        """Deletes an RDP profile by name."""
        if name in self.profiles:
            del self.profiles[name]
            self._save_profiles_to_file()
            return True
        return False

if __name__ == "__main__":
    # Example Usage:
    # Create a temporary directory for testing
    test_profiles_dir = "./temp_rdp_profiles"
    if not os.path.exists(test_profiles_dir):
        os.makedirs(test_profiles_dir)

    manager = RDPProfileManager(profiles_dir=test_profiles_dir)

    # Test saving profiles
    profile1 = {
        "name": "Work Server",
        "hostname": "work.example.com",
        "port": 3389,
        "username": "user1"
    }
    profile2 = {
        "name": "Home PC",
        "hostname": "192.168.1.100",
        "username": "user2",
        "icon_path": "/path/to/home_icon.png"
    }
    manager.save_profile(profile1)
    manager.save_profile(profile2)
    print("Saved profiles:", manager.list_profiles())

    # Test getting a profile
    retrieved_profile = manager.get_profile("Work Server")
    print("Retrieved 'Work Server':", retrieved_profile)

    # Test updating a profile
    if retrieved_profile:
        retrieved_profile["port"] = 3390
        retrieved_profile["domain"] = "WORKGROUP"
        manager.save_profile(retrieved_profile)
        print("Updated 'Work Server':", manager.get_profile("Work Server"))

    # Test deleting a profile
    manager.delete_profile("Home PC")
    print("Profiles after deleting 'Home PC':", manager.list_profiles())

    # Clean up the temporary directory and file
    if os.path.exists(manager.profiles_file):
        os.remove(manager.profiles_file)
    if os.path.exists(test_profiles_dir):
        os.rmdir(test_profiles_dir)
    print("Test complete and cleaned up.")
