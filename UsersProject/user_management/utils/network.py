import os
import shutil
from pathlib import Path
from django.conf import settings
from .logging import log_scan_operation

def scan_network_directory(computer_ip, share_path):
    """Scan network directory for PDF files"""
    try:
        # Convert IP to UNC path
        network_path = f'//{computer_ip}/{share_path.strip("/")}'
        pdf_files = []
        
        # Walk through the network directory
        for root, _, files in os.walk(network_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
                    
        return pdf_files
    except Exception as e:
        log_scan_operation(f"Failed to scan network directory {network_path}: {str(e)}", "error")
        return []

def copy_network_file(src_path, dest_path):
    """Copy a file from network share"""
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        return True
    except Exception as e:
        log_scan_operation(f"Failed to copy {src_path}: {str(e)}", "error")
        return False
