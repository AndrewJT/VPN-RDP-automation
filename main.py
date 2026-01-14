import webview
import json
import os
import subprocess
import sys
import mimetypes
from pathlib import Path

# Fix MIME types for ES6 modules
mimetypes.add_type('application/javascript', '.ts')
mimetypes.add_type('application/javascript', '.tsx')

CONFIG_FILE = Path.home() / ".netconnect_pro.json"

class NetConnectAPI:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def load_config(self):
        """Loads the configuration file from the user's home directory."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"[Engine] Config loaded from {CONFIG_FILE}")
                    return content
            except Exception as e:
                print(f"[Engine] Error loading config: {e}")
                return None
        print(f"[Engine] No config file found at {CONFIG_FILE}")
        return None

    def save_config(self, config_json):
        """Saves the current configuration to the user's home directory."""
        if not config_json or len(config_json) < 10:
            return False
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(config_json)
            return True
        except Exception as e:
            print(f"[Engine] Error saving config: {e}")
            return False

    def export_config_dialog(self, config_json):
        """Native save file dialog for export using non-deprecated API."""
        if not self._window: return False
        try:
            # result can be a string or a list/tuple depending on version/OS
            result = self._window.create_file_dialog(webview.FileDialog.SAVE, file_types=('JSON Files (*.json)',), save_filename='netconnect_backup.json')
            if result:
                # result is expected to be a string or a sequence containing a string
                save_path = result[0] if isinstance(result, (list, tuple)) else result
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(config_json)
                print(f"[Engine] Exported successfully to {save_path}")
                return True
        except Exception as e:
            print(f"[Engine] Export failed: {e}")
            return False
        return False

    def import_config_dialog(self):
        """Native open file dialog for import using non-deprecated API."""
        if not self._window: return None
        try:
            result = self._window.create_file_dialog(webview.FileDialog.OPEN, file_types=('JSON Files (*.json)',))
            if result and len(result) > 0:
                with open(result[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"[Engine] Imported successfully from {result[0]}")
                    return content
        except Exception as e:
            print(f"[Engine] Import failed: {e}")
            return None
        return None

    def wipe_config(self):
        """Native factory reset - deletes the config file."""
        if os.path.exists(CONFIG_FILE):
            try:
                os.remove(CONFIG_FILE)
                print("[Engine] Config file deleted (Factory Reset)")
                return True
            except Exception as e:
                print(f"[Engine] Wipe failed: {e}")
                return False
        return True

    def launch_rdp(self, host, username, password):
        """Launches Windows MSTSC and injects credentials into the store temporarily."""
        try:
            if password:
                targets = [host, f"TERMSRV/{host}"]
                for target in targets:
                    cmd = f'cmdkey /add:"{target}" /user:"{username}" /pass:"{password}"'
                    subprocess.run(cmd, shell=True, capture_output=True, check=False)
            subprocess.Popen(['mstsc', f'/v:{host}'])
            return True
        except Exception as e:
            print(f"[Engine] Native RDP Error: {e}")
            try:
                subprocess.Popen(['mstsc', f'/v:{host}'])
            except:
                pass
            return False

    def toggle_vpn(self, protocol, host, disconnect=False, sso=False):
        """Orchestrates different VPN client binaries based on protocol."""
        try:
            action = "disconnect" if disconnect else "connect"
            print(f"[Engine] Toggling {protocol} for {host} (Action: {action}, SSO: {sso})")
            
            if protocol == "FortiClient":
                cli_paths = [
                    r"C:\Program Files\Fortinet\FortiClient\FortiSSLVPNcli.exe",
                    r"C:\Program Files (x86)\Fortinet\FortiClient\FortiSSLVPNcli.exe"
                ]
                exe = next((p for p in cli_paths if os.path.exists(p)), None)
                if exe and not sso:
                    subprocess.Popen([exe, action, "-h", host])
                    return True
                gui = r"C:\Program Files\Fortinet\FortiClient\FortiClient.exe"
                if os.path.exists(gui):
                    subprocess.Popen([gui])
                    return True

            elif protocol == "OpenVPN":
                exe = r"C:\Program Files\OpenVPN\bin\openvpn-gui.exe"
                if os.path.exists(exe):
                    cmd_action = "disconnect_all" if disconnect else "connect"
                    subprocess.Popen([exe, "--command", cmd_action, host])
                    return True

            elif protocol == "Palo Alto GlobalProtect":
                exe = r"C:\Program Files\Palo Alto Networks\GlobalProtect\PanGPA.exe"
                if os.path.exists(exe):
                    subprocess.Popen([exe])
                    return True

            elif protocol == "Cisco AnyConnect":
                exe_paths = [
                    r"C:\Program Files (x86)\Cisco\Cisco AnyConnect Secure Mobility Client\vpnui.exe",
                    r"C:\Program Files (x86)\Cisco\Cisco Secure Client\vpnui.exe"
                ]
                exe = next((p for p in exe_paths if os.path.exists(p)), None)
                if exe:
                    subprocess.Popen([exe])
                    return True

            elif protocol == "Citrix":
                exe = r"C:\Program Files (x86)\Citrix\ICA Client\SelfServicePlugin\SelfService.exe"
                if os.path.exists(exe):
                    subprocess.Popen([exe])
                    return True

            return True
        except Exception as e:
            print(f"[Engine] VPN Native Error: {e}")
            return False

def start_app():
    api = NetConnectAPI()
    template_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    index_path = os.path.join(template_dir, 'index.html')

    # Load initial config to check for devtools flag
    show_debug = False
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.loads(f.read())
                show_debug = cfg.get('showDevTools', False)
        except:
            pass

    window = webview.create_window(
        'NetConnect Pro Console',
        url=index_path,
        js_api=api,
        width=1280,
        height=900,
        background_color='#020617',
        resizable=True
    )
    
    api.set_window(window)
    # devconsole can only be enabled at start time via debug=True
    webview.start(debug=show_debug, gui='edgechromium')

if __name__ == '__main__':
    start_app()
