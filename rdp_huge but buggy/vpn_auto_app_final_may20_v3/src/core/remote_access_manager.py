import os
import tempfile
import subprocess
import webbrowser
import platform
import json
import base64
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

class CredentialManager:
    """
    Manages secure storage and retrieval of credentials for remote connections.
    Supports both internal encrypted storage and Windows Credential Manager integration.
    """
    
    def __init__(self):
        """
        Initialize the credential manager.
        """
        self.current_os = platform.system().lower()
        self.credential_store_path = os.path.join(os.path.expanduser("~"), ".vpn_auto_app", "credentials")
        
        # Ensure credential store directory exists
        os.makedirs(self.credential_store_path, exist_ok=True)
    
    def store_credentials(self, connection_id: str, credentials: Dict[str, str], use_windows_cred_manager: bool = True) -> bool:
        """
        Store credentials for a connection.
        
        Args:
            connection_id (str): Unique identifier for the connection
            credentials (Dict[str, str]): Dictionary containing credentials (username, password, domain)
            use_windows_cred_manager (bool): Whether to use Windows Credential Manager (if available)
            
        Returns:
            bool: Success status
        """
        if self.current_os == "windows" and use_windows_cred_manager:
            return self._store_in_windows_credential_manager(connection_id, credentials)
        else:
            return self._store_in_internal_vault(connection_id, credentials)
    
    def retrieve_credentials(self, connection_id: str, use_windows_cred_manager: bool = True) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials for a connection.
        
        Args:
            connection_id (str): Unique identifier for the connection
            use_windows_cred_manager (bool): Whether to use Windows Credential Manager (if available)
            
        Returns:
            Optional[Dict[str, str]]: Dictionary containing credentials or None if not found
        """
        if self.current_os == "windows" and use_windows_cred_manager:
            return self._retrieve_from_windows_credential_manager(connection_id)
        else:
            return self._retrieve_from_internal_vault(connection_id)
    
    def delete_credentials(self, connection_id: str, use_windows_cred_manager: bool = True) -> bool:
        """
        Delete credentials for a connection.
        
        Args:
            connection_id (str): Unique identifier for the connection
            use_windows_cred_manager (bool): Whether to use Windows Credential Manager (if available)
            
        Returns:
            bool: Success status
        """
        if self.current_os == "windows" and use_windows_cred_manager:
            return self._delete_from_windows_credential_manager(connection_id)
        else:
            return self._delete_from_internal_vault(connection_id)
    
    def _store_in_windows_credential_manager(self, connection_id: str, credentials: Dict[str, str]) -> bool:
        """
        Store credentials in Windows Credential Manager.
        
        Args:
            connection_id (str): Unique identifier for the connection
            credentials (Dict[str, str]): Dictionary containing credentials
            
        Returns:
            bool: Success status
        """
        try:
            # Import Windows-specific modules only when needed
            import win32cred
            import win32credui
            import pywintypes
            
            # Create a target name that's unique to our application
            target_name = f"VPNAutoApp:RDP:{connection_id}"
            
            # Serialize credentials to JSON
            cred_blob = json.dumps(credentials).encode('utf-16-le')
            
            # Create credential structure
            cred = {
                'Type': win32cred.CRED_TYPE_GENERIC,
                'TargetName': target_name,
                'UserName': credentials.get('username', ''),
                'CredentialBlob': cred_blob,
                'Comment': 'VPN Automation Application RDP Credentials',
                'Persist': win32cred.CRED_PERSIST_LOCAL_MACHINE
            }
            
            # Store the credential
            win32cred.CredWrite(cred, 0)
            return True
        except ImportError:
            print("Windows credential modules not available. Using internal storage instead.")
            return self._store_in_internal_vault(connection_id, credentials)
        except Exception as e:
            print(f"Error storing credentials in Windows Credential Manager: {e}")
            return False
    
    def _retrieve_from_windows_credential_manager(self, connection_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials from Windows Credential Manager.
        
        Args:
            connection_id (str): Unique identifier for the connection
            
        Returns:
            Optional[Dict[str, str]]: Dictionary containing credentials or None if not found
        """
        try:
            # Import Windows-specific modules only when needed
            import win32cred
            import pywintypes
            
            # Create a target name that's unique to our application
            target_name = f"VPNAutoApp:RDP:{connection_id}"
            
            try:
                # Retrieve the credential
                cred = win32cred.CredRead(target_name, win32cred.CRED_TYPE_GENERIC, 0)
                
                # Deserialize credentials from JSON
                cred_blob = cred['CredentialBlob'].decode('utf-16-le')
                return json.loads(cred_blob)
            except pywintypes.error:
                # Credential not found
                return None
        except ImportError:
            print("Windows credential modules not available. Using internal storage instead.")
            return self._retrieve_from_internal_vault(connection_id)
        except Exception as e:
            print(f"Error retrieving credentials from Windows Credential Manager: {e}")
            return None
    
    def _delete_from_windows_credential_manager(self, connection_id: str) -> bool:
        """
        Delete credentials from Windows Credential Manager.
        
        Args:
            connection_id (str): Unique identifier for the connection
            
        Returns:
            bool: Success status
        """
        try:
            # Import Windows-specific modules only when needed
            import win32cred
            import pywintypes
            
            # Create a target name that's unique to our application
            target_name = f"VPNAutoApp:RDP:{connection_id}"
            
            try:
                # Delete the credential
                win32cred.CredDelete(target_name, win32cred.CRED_TYPE_GENERIC, 0)
                return True
            except pywintypes.error:
                # Credential not found
                return False
        except ImportError:
            print("Windows credential modules not available. Using internal storage instead.")
            return self._delete_from_internal_vault(connection_id)
        except Exception as e:
            print(f"Error deleting credentials from Windows Credential Manager: {e}")
            return False
    
    def _store_in_internal_vault(self, connection_id: str, credentials: Dict[str, str]) -> bool:
        """
        Store credentials in internal encrypted vault.
        
        Args:
            connection_id (str): Unique identifier for the connection
            credentials (Dict[str, str]): Dictionary containing credentials
            
        Returns:
            bool: Success status
        """
        try:
            # Simple encryption for demonstration (in production, use stronger encryption)
            # In a real implementation, use a proper encryption library like cryptography
            cred_json = json.dumps(credentials)
            encoded_creds = base64.b64encode(cred_json.encode()).decode()
            
            # Create a file for this connection
            cred_file = os.path.join(self.credential_store_path, f"{connection_id}.cred")
            with open(cred_file, 'w') as f:
                f.write(encoded_creds)
            
            # Set restrictive permissions on the file
            if os.name != 'nt':  # Not Windows
                os.chmod(cred_file, 0o600)  # Owner read/write only
                
            return True
        except Exception as e:
            print(f"Error storing credentials in internal vault: {e}")
            return False
    
    def _retrieve_from_internal_vault(self, connection_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials from internal encrypted vault.
        
        Args:
            connection_id (str): Unique identifier for the connection
            
        Returns:
            Optional[Dict[str, str]]: Dictionary containing credentials or None if not found
        """
        try:
            # Check if credential file exists
            cred_file = os.path.join(self.credential_store_path, f"{connection_id}.cred")
            if not os.path.exists(cred_file):
                return None
            
            # Read and decrypt credentials
            with open(cred_file, 'r') as f:
                encoded_creds = f.read().strip()
            
            # Simple decryption (in production, use stronger encryption)
            cred_json = base64.b64decode(encoded_creds.encode()).decode()
            return json.loads(cred_json)
        except Exception as e:
            print(f"Error retrieving credentials from internal vault: {e}")
            return None
    
    def _delete_from_internal_vault(self, connection_id: str) -> bool:
        """
        Delete credentials from internal encrypted vault.
        
        Args:
            connection_id (str): Unique identifier for the connection
            
        Returns:
            bool: Success status
        """
        try:
            # Check if credential file exists
            cred_file = os.path.join(self.credential_store_path, f"{connection_id}.cred")
            if not os.path.exists(cred_file):
                return False
            
            # Delete the file
            os.remove(cred_file)
            return True
        except Exception as e:
            print(f"Error deleting credentials from internal vault: {e}")
            return False


class RemoteAccessManager:
    """
    Manages the initiation of remote access methods like RDP and browser launching
    after a successful VPN connection.
    """

    def __init__(self):
        """
        Initializes the RemoteAccessManager.
        """
        self.current_os = platform.system().lower()
        self.credential_manager = CredentialManager()
        self.temp_dir = None
        
    def connect_rdp(self, hostname, port=3389, username=None, password=None, domain=None, 
                   connection_id=None, use_saved_credentials=True, save_credentials=False,
                   fullscreen=True, admin_console=False, width=1024, height=768):
        """
        Connects to an RDP server with the given parameters.
        
        Args:
            hostname (str): The hostname or IP address of the RDP server
            port (int, optional): The port to connect to. Defaults to 3389.
            username (str, optional): The username for authentication. Defaults to None.
            password (str, optional): The password for authentication. Defaults to None.
            domain (str, optional): The domain for authentication. Defaults to None.
            connection_id (str, optional): Unique identifier for saved credentials. Defaults to None.
            use_saved_credentials (bool, optional): Whether to use saved credentials. Defaults to True.
            save_credentials (bool, optional): Whether to save provided credentials. Defaults to False.
            fullscreen (bool, optional): Whether to launch in fullscreen mode. Defaults to True.
            admin_console (bool, optional): Whether to connect to admin console. Defaults to False.
            width (int, optional): Screen width when not in fullscreen. Defaults to 1024.
            height (int, optional): Screen height when not in fullscreen. Defaults to 768.
            
        Returns:
            bool: Success status
        """
        # Generate a connection ID if not provided
        if connection_id is None and hostname:
            connection_id = f"rdp_{hostname.replace('.', '_')}_{port}"
        
        # Save credentials if requested
        if save_credentials and username and connection_id:
            credentials = {
                "username": username,
                "password": password or "",
                "domain": domain or ""
            }
            self.credential_manager.store_credentials(connection_id, credentials)
        
        # Try to retrieve saved credentials if requested and not provided
        if use_saved_credentials and connection_id and (not username or not password):
            saved_creds = self.credential_manager.retrieve_credentials(connection_id)
            if saved_creds:
                username = username or saved_creds.get("username")
                password = password or saved_creds.get("password")
                domain = domain or saved_creds.get("domain")
        
        details = {
            "hostname": hostname,
            "port": port,
            "username": username,
            "password": password,
            "domain": domain,
            "fullscreen": fullscreen,
            "admin_console": admin_console,
            "width": width,
            "height": height
        }
            
        success, _ = self.initiate_access("rdp", details)
        return success

    def initiate_access(self, access_type: str, details: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Initiates a remote access session based on the type and details provided.

        Args:
            access_type (str): The type of remote access (e.g., "rdp", "browser").
            details (Dict[str, Any]): Configuration details for the access method.
                                      For "rdp": {"hostname": "...", "username": "..." (optional)}
                                      For "browser": {"url": "..."}

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success (True) or failure (False),
                              and a message describing the outcome.
        """
        access_type = access_type.lower()
        if access_type == "rdp":
            return self._launch_rdp(details)
        elif access_type == "browser":
            return self._launch_browser(details)
        else:
            return False, f"Unsupported remote access type: {access_type}"

    def _launch_rdp(self, details: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Launches a Remote Desktop Protocol (RDP) session using a temporary .rdp file.
        Currently supports Windows only.
        
        This method follows mRemoteNG's approach of generating a temporary .rdp file
        with connection settings and launching mstsc.exe with that file.
        """
        if self.current_os != "windows":
            # For non-Windows systems, provide a simulation for testing
            print(f"RDP simulation (non-Windows OS): Would connect to {details.get('hostname', 'unknown')}")
            return True, f"RDP simulation initiated (non-Windows OS). In production, this would connect to {details.get('hostname', 'unknown')}"

        hostname = details.get("hostname")
        if not hostname:
            return False, "RDP hostname not provided in details."
        
        # Create a temporary directory if not already created
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp(prefix="vpn_auto_app_")
        
        # Generate a unique name for the RDP file
        rdp_file_path = os.path.join(self.temp_dir, f"{hostname.replace('.', '_')}_{details.get('port', 3389)}.rdp")
        
        # Create RDP file content
        rdp_content = self._generate_rdp_file_content(details)
        
        try:
            # Write RDP file
            with open(rdp_file_path, 'w') as f:
                f.write(rdp_content)
            
            # Launch RDP client with the file
            print(f"Launching RDP to: {hostname} using RDP file: {rdp_file_path}")
            subprocess.Popen(["mstsc.exe", rdp_file_path], shell=True)
            
            return True, f"RDP session to '{hostname}' initiated. Please check your Remote Desktop Client."
        except FileNotFoundError:
            return False, "mstsc.exe (Remote Desktop Client) not found. Ensure it is installed and in your system PATH."
        except Exception as e:
            error_msg = str(e)
            print(f"RDP connection error: {error_msg}")
            return False, f"Failed to launch RDP session: {error_msg}"
    
    def _generate_rdp_file_content(self, details: Dict[str, Any]) -> str:
        """
        Generate RDP file content based on connection details.
        
        Args:
            details (Dict[str, Any]): Connection details
            
        Returns:
            str: RDP file content
        """
        # Basic connection settings
        rdp_settings = [
            f"full address:s:{details.get('hostname')}:{details.get('port', 3389)}",
            "prompt for credentials:i:1",  # Always prompt for credentials for security
            "connection type:i:7"  # RDP connection
        ]
        
        # Screen settings
        if details.get("fullscreen", True):
            rdp_settings.append("screen mode id:i:2")  # Fullscreen
        else:
            rdp_settings.extend([
                "screen mode id:i:1",  # Windowed
                f"desktopwidth:i:{details.get('width', 1024)}",
                f"desktopheight:i:{details.get('height', 768)}"
            ])
        
        # Admin console
        if details.get("admin_console", False):
            rdp_settings.append("admin console:i:1")
        else:
            rdp_settings.append("admin console:i:0")
        
        # Add other common RDP settings
        rdp_settings.extend([
            "session bpp:i:32",  # 32-bit color depth
            "compression:i:1",  # Enable compression
            "keyboardhook:i:2",  # Apply key combinations on remote server
            "audiocapturemode:i:0",  # Do not capture audio
            "videoplaybackmode:i:1",  # Enable video playback
            "connection type:i:7",  # RDP connection
            "networkautodetect:i:1",  # Auto-detect network
            "bandwidthautodetect:i:1",  # Auto-detect bandwidth
            "displayconnectionbar:i:1",  # Show connection bar
            "enableworkspacereconnect:i:0",  # Disable workspace reconnect
            "disable wallpaper:i:0",  # Keep wallpaper
            "allow font smoothing:i:1",  # Enable font smoothing
            "allow desktop composition:i:1",  # Enable desktop composition
            "disable full window drag:i:0",  # Enable full window drag
            "disable menu anims:i:0",  # Enable menu animations
            "disable themes:i:0",  # Enable themes
            "disable cursor setting:i:0",  # Enable cursor settings
            "bitmapcachepersistenable:i:1",  # Enable bitmap cache
            "audiomode:i:0",  # Play sounds on remote computer
            "redirectprinters:i:1",  # Redirect printers
            "redirectcomports:i:0",  # Don't redirect COM ports
            "redirectsmartcards:i:1",  # Redirect smart cards
            "redirectclipboard:i:1",  # Redirect clipboard
            "redirectposdevices:i:0",  # Don't redirect POS devices
            "autoreconnection enabled:i:1",  # Enable auto-reconnect
            "authentication level:i:2",  # Warn if authentication fails
            "prompt for credentials:i:1",  # Always prompt for credentials
            "negotiate security layer:i:1",  # Negotiate security layer
            "remoteapplicationmode:i:0",  # Not a RemoteApp
            "alternate shell:s:",  # No alternate shell
            "shell working directory:s:",  # No specific working directory
            "gatewayhostname:s:",  # No gateway
            "gatewayusagemethod:i:4",  # Don't use gateway
            "gatewaycredentialssource:i:4",  # Don't use gateway credentials
            "gatewayprofileusagemethod:i:0",  # Don't use gateway profile
            "promptcredentialonce:i:1",  # Prompt for credentials once
            "use redirection server name:i:0"  # Don't use redirection server name
        ])
        
        # Join all settings with newlines
        return "\n".join(rdp_settings)

    def _launch_browser(self, details: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Launches the default web browser to a specified URL.
        """
        url = details.get("url")
        if not url:
            return False, "URL not provided for browser access."

        try:
            print(f"Opening URL in browser: {url}")
            webbrowser.open_new_tab(url)
            return True, f"Browser opened to URL: {url}"
        except Exception as e:
            return False, f"Failed to open URL in browser: {e}"
    
    def cleanup(self):
        """
        Clean up temporary files.
        """
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                # Remove all files in the temporary directory
                for file_name in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, file_name)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                
                # Remove the directory
                os.rmdir(self.temp_dir)
                self.temp_dir = None
            except Exception as e:
                print(f"Error cleaning up temporary files: {e}")

# Example Usage (Conceptual)
if __name__ == "__main__":
    ram = RemoteAccessManager()
    print(f"Running on OS: {ram.current_os}")

    # Test RDP (will only work on Windows and if mstsc.exe is available)
    if ram.current_os == "windows":
        print("\nTesting RDP Launch (replace with a valid hostname if you want to test for real):")
        
        # Test with RDP file generation
        rdp_details = {
            "hostname": "your-test-rdp-server.com",
            "port": 3389,
            "fullscreen": False,
            "width": 1280,
            "height": 720
        }
        success, message = ram.initiate_access("rdp", rdp_details)
        print(f"RDP Launch (with RDP file): Success={success}, Message='{message}'")
        
        # Test credential storage
        print("\nTesting Credential Storage:")
        connection_id = "test_connection"
        test_creds = {"username": "testuser", "password": "testpass", "domain": "testdomain"}
        
        # Store credentials
        success = ram.credential_manager.store_credentials(connection_id, test_creds)
        print(f"Store Credentials: Success={success}")
        
        # Retrieve credentials
        retrieved_creds = ram.credential_manager.retrieve_credentials(connection_id)
        print(f"Retrieved Credentials: {retrieved_creds}")
        
        # Delete credentials
        success = ram.credential_manager.delete_credentials(connection_id)
        print(f"Delete Credentials: Success={success}")
        
        # Clean up
        ram.cleanup()
    else:
        print("\nSkipping RDP test as not on Windows.")

    print("\nRemoteAccessManager test complete.")
