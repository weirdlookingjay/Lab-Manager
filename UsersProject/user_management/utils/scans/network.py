import os
import subprocess
from .logs import log_scan_operation

def cleanup_network_connections():
    """Clean up network connections."""
    try:
        # List current connections
        log_scan_operation("Listing current network connections", event="NETWORK_CHECK")
        result = subprocess.run('net use', shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Parse output to find and disconnect existing connections
            connections = result.stdout.split('\n')
            for line in connections:
                if '\\\\' in line:  # Line contains a network path
                    # Extract the network path
                    path = line.split()[1]
                    log_scan_operation(f"Disconnecting from {path}", event="NETWORK_CLEANUP")
                    # Disconnect the connection
                    subprocess.run(f'net use {path} /delete /y', shell=True, check=False)
    except Exception as e:
        log_scan_operation(f"Error cleaning up network connections: {str(e)}", "error", event="NETWORK_ERROR")

def establish_network_connection(computer_ip, username='Client', password=None):
    """Authenticate to the remote computer using net use."""
    try:
        # Clean up any existing connections first
        cleanup_network_connections()
        
        # First try with computer's credentials if provided
        if username and password:
            connect_cmd = f'net use \\\\{computer_ip}\\C$ /user:"{username}" "{password}" /persistent:no /y'
            result = subprocess.run(connect_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                log_scan_operation(f"Successfully connected to \\\\{computer_ip}\\C$ with computer credentials", event="NETWORK_CONNECTED")
                return True
                
        # If computer credentials failed or weren't provided, try admin credentials
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_password = os.getenv('ADMIN_PASSWORD')
        
        if not admin_username or not admin_password:
            log_scan_operation("Admin credentials not found in environment variables", "error", event="NETWORK_ERROR")
            return False
            
        connect_cmd = f'net use \\\\{computer_ip}\\C$ /user:"{admin_username}" "{admin_password}" /persistent:no /y'
        result = subprocess.run(connect_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            log_scan_operation(f"Successfully connected to \\\\{computer_ip}\\C$ with admin credentials", event="NETWORK_CONNECTED")
            return True
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            log_scan_operation(f"Failed to connect to {computer_ip} with both sets of credentials: {error_msg}", "error", event="NETWORK_ERROR")
            return False
            
    except Exception as e:
        log_scan_operation(f"Error connecting to {computer_ip}: {str(e)}", "error", event="NETWORK_ERROR")
        return False

def scan_network_directory(ip_address, share_path, computer_label=None):
    """
    Scan specific user folders (Desktop, Documents, Downloads) for PDF files.
    
    Args:
        ip_address (str): IP address of the computer to scan
        share_path (str): Base path to scan (e.g. 'C$\\Users')
        computer_label (str): Label of the computer being scanned (for logging)
        
    Returns:
        list: List of PDF file paths found
    """
    try:
        # Build the full network path
        network_path = f"\\\\{ip_address}\\{share_path}"
        label_info = f" ({computer_label})" if computer_label else ""
        log_scan_operation(f"Scanning network path: {network_path}{label_info}", event="SCAN_START")
        
        all_files = []
        # Only scan specific user folders
        target_folders = ["Desktop", "Documents", "Downloads"]
        
        # First, list all user profiles
        cmd = f'dir /B /AD "{network_path}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            user_profiles = [p.strip() for p in result.stdout.split('\n') if p.strip() 
                           and not p.strip().lower() in ['public', 'default', 'default user', 'all users']]
            
            # For each user profile, scan the specific folders
            for profile in user_profiles:
                for folder in target_folders:
                    folder_path = os.path.join(network_path, profile, folder)
                    temp_file = os.path.join(os.environ.get('TEMP', ''), f'pdf_files_{profile}_{folder}.txt')
                    
                    # Use robocopy to list all PDF files in the specific folder
                    cmd = f'robocopy "{folder_path}" NULL *.pdf /L /S /FP /NS /NC /NDL /NJH /NJS /LOG:"{temp_file}"'
                    subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    
                    if os.path.exists(temp_file):
                        # Read the file list
                        with open(temp_file, 'r', encoding='utf-8') as f:
                            files = [line.strip() for line in f if line.strip().lower().endswith('.pdf')]
                            all_files.extend(files)
                        
                        # Clean up temp file
                        try:
                            os.remove(temp_file)
                        except:
                            pass
        
        log_scan_operation(f"Found {len(all_files)} PDF files in user folders", event="SCAN_COMPLETE")
        return all_files
        
    except Exception as e:
        log_scan_operation(f"Error scanning network directory: {str(e)}", "error", event="SCAN_ERROR")
        return []
    finally:
        # Clean up any remaining temp files
        try:
            temp_dir = os.environ.get('TEMP', '')
            for file in os.listdir(temp_dir):
                if file.startswith('pdf_files_') and file.endswith('.txt'):
                    os.remove(os.path.join(temp_dir, file))
        except:
            pass