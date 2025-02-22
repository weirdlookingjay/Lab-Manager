import os
import shutil
import re
import pandas as pd
from datetime import datetime

# Configurations
CSV_FILE = "Lab-Computers.csv"  # CSV file containing "IP Address,ComputerLabel"
DESTINATION_ROOT = r"D:\Code\aw\labv2\UsersProject\media\pdfs"
LOG_FILE = "copy_log.txt"
USER_PROFILES = ["Client"]  # Adjust based on actual usernames on the target PCs

# Authentication Credentials
ADMIN_USERNAME = "infotech"
ADMIN_PASSWORD = "gidget003"  # Replace with actual password

# Get current date for folder naming
current_date = datetime.now().strftime("%m-%d-%Y")
destination_path = os.path.join(DESTINATION_ROOT, current_date)

# Ensure log file is cleared
with open(LOG_FILE, "w") as log:
    log.write(f"Copy operation started on {current_date}\n\n")

def sanitize_filename(filename):
    """Remove only square brackets [ ] from filenames while keeping the extension."""
    name, ext = os.path.splitext(filename)
    clean_name = re.sub(r'[\[\]]', '', name)  # Remove only square brackets
    return clean_name + ext

def authenticate_remote(computer_ip):
    """Authenticate to the remote computer using net use."""
    command = f'net use \\\\{computer_ip}\\C$ /user:{ADMIN_USERNAME} {ADMIN_PASSWORD}'
    result = os.system(command)
    if result == 0:
        log_message(f"[{computer_ip}] Authentication successful")
    else:
        log_message(f"[{computer_ip}] Authentication failed")

def copy_files(computer_ip, computer_label):
    """Copy PDF files from remote computer's Desktop, Documents, and Downloads folders."""
    global destination_path
    computer_dest = os.path.join(destination_path, computer_label)  # Use label (PC1, PC2, etc.)
    os.makedirs(computer_dest, exist_ok=True)

    folders_to_copy = ["Desktop", "Documents", "Downloads"]
    base_path = f"\\\\{computer_ip}\\C$\\Users"

    for user in USER_PROFILES:
        for folder in folders_to_copy:
            source_folder = os.path.join(base_path, user, folder)
            if not os.path.exists(source_folder):
                log_message(f"[{computer_ip}] Skipping {source_folder} (not found)")
                continue

            try:
                for file in os.listdir(source_folder):
                    if file.lower().endswith(".pdf"):
                        source_file = os.path.join(source_folder, file)
                        sanitized_name = sanitize_filename(file)
                        dest_file = os.path.join(computer_dest, sanitized_name)

                        shutil.copy2(source_file, dest_file)
                        log_message(f"[{computer_ip}] Copied {file} -> {sanitized_name}")
            except Exception as e:
                log_message(f"[{computer_ip}] Error copying from {source_folder}: {e}")

def log_message(message):
    """Write log message to file and print it."""
    print(message)
    with open(LOG_FILE, "a") as log:
        log.write(message + "\n")

def main():
    """Main execution function."""
    try:
        computers = pd.read_csv(CSV_FILE)
        for _, row in computers.iterrows():
            computer_ip = row["IPAddress"]
            computer_label = row["ComputerLabel"]

            log_message(f"Processing {computer_ip} ({computer_label})...")
            authenticate_remote(computer_ip)  # Authenticate first
            copy_files(computer_ip, computer_label)
    except Exception as e:
        log_message(f"Critical error: {e}")

if __name__ == "__main__":
    main()
