import os
import msvcrt
import shutil
from datetime import datetime
from django.conf import settings
from .logs import log_scan_operation
import re

def find_case_insensitive_path(base_path, folder_name):
    """Find a folder name case-insensitively within base_path."""
    try:
        log_scan_operation(f"Looking for '{folder_name}' in '{base_path}'", event="FILE_FOUND")
        
        if not os.path.exists(base_path):
            log_scan_operation(f"Base path '{base_path}' does not exist", level="error", event="FILE_ACCESS")
            return None
            
        # Try direct match first
        direct_path = os.path.join(base_path, folder_name)
        if os.path.exists(direct_path):
            log_scan_operation(f"Found direct match: {direct_path}", event="FILE_FOUND")
            return direct_path
            
        # If no direct match, try case-insensitive search
        try:
            items = os.listdir(base_path)
            log_scan_operation(f"Found {len(items)} items in {base_path}", event="FILE_INDEXED")
            for item in items:
                log_scan_operation(f"Checking item: {item}", event="FILE_INDEXED")
                if item.lower() == folder_name.lower():
                    found_path = os.path.join(base_path, item)
                    log_scan_operation(f"Found case-insensitive match: {found_path}", event="FILE_FOUND")
                    return found_path
        except Exception as e:
            log_scan_operation(f"Error accessing {base_path}: {str(e)}", "error", event="FILE_ACCESS")
            
        log_scan_operation(f"No match found for '{folder_name}' in '{base_path}'", event="FILE_ACCESS")
        return None
        
    except Exception as e:
        log_scan_operation(f"Error in find_case_insensitive_path: {str(e)}", "error", event="FILE_ACCESS")
        return None

def sanitize_filename(filename):
    """Remove only square brackets [ ] from filenames while keeping the extension."""
    # Split filename into name and extension
    name, ext = os.path.splitext(filename)
    # Remove square brackets from name part only
    clean_name = name.replace('[', '').replace(']', '')
    return clean_name + ext

def check_file_access(file_path):
    """Check if a file can be accessed and modified."""
    try:
        # Try to open the file for both reading and writing
        with open(file_path, 'r+b') as f:
            # Try to get an exclusive lock
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            # Release the lock
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        return True, None
    except IOError as e:
        return False, f"IO Error: {str(e)}"
    except PermissionError as e:
        return False, f"Permission Error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_base_filename(filename):
    """Get the base filename without numbers or date."""
    # For StrengthsProfile files
    if filename.startswith('StrengthsProfile-'):
        # Remove the .pdf extension
        name = filename.replace('.pdf', '')
        # Remove any (N) suffix
        name = re.sub(r'\s*\(\d+\)$', '', name)
        # Remove any date suffix
        name = re.sub(r'-\d{2}-\d{2}-\d{4}$', '', name)
        # Log the transformation
        log_scan_operation(f"Normalized filename '{filename}' to base name '{name}.pdf'")
        return name + '.pdf'
    # For O*NET files
    elif 'O_NET' in filename.upper():
        # Remove the .pdf extension and any spaces
        name = filename.replace('.pdf', '').replace(' ', '_')
        # Remove any (N) suffix
        name = re.sub(r'\s*\(\d+\)$', '', name)
        # Remove any date patterns
        name = re.sub(r'[_-]\d{2}[_-]\d{2}[_-]\d{4}$', '', name)  # MM-DD-YYYY or MM_DD_YYYY
        name = re.sub(r'_\d{8}$', '', name)  # _MMDDYYYY
        # Remove Perfil_ prefix (Spanish)
        name = name.replace('Perfil_', '')
        # Normalize O_NET prefix
        name = re.sub(r'^O[_-]?NET[_-]?(?:Profile)?[_-]?', 'O_NET_', name, flags=re.IGNORECASE)
        # Log the transformation
        log_scan_operation(f"Normalized O*NET filename '{filename}' to base name '{name}.pdf'")
        return name + '.pdf'
    return filename

def is_duplicate_file(filename, dir_path):
    """Check if a file is a duplicate."""
    log_scan_operation(f"Checking for duplicates of: {filename}", event="FILE_DUPLICATE_CHECK")
    
    try:
        # Get base filename without numbers or date
        base_filename = get_base_filename(filename)
        log_scan_operation(f"Base filename to check: {base_filename}", event="FILE_DUPLICATE_CHECK")
        
        # List all files in directory
        existing_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.pdf')]
        log_scan_operation(f"Found {len(existing_files)} PDF files in destination", event="FILE_DUPLICATE_CHECK")
        
        # For each existing file, compare their base names
        for existing_file in existing_files:
            existing_base = get_base_filename(existing_file)
            log_scan_operation(f"Comparing with existing file: {existing_file} (base: {existing_base})", event="FILE_DUPLICATE_CHECK")
            
            if base_filename.lower() == existing_base.lower():
                log_scan_operation(f"MATCH FOUND! {filename} matches existing file {existing_file}", event="FILE_DUPLICATE_FOUND")
                return True
                
        log_scan_operation(f"No duplicates found for {filename}", event="FILE_DUPLICATE_CHECK")
        return False
        
    except Exception as e:
        log_scan_operation(f"Error checking for duplicates: {str(e)}", "error", event="FILE_DUPLICATE_CHECK")
        return False

def is_duplicate_strengthsprofile(directory, name):
    """Check if a StrengthsProfile file already exists for this person today."""
    try:
        # Remove any (1), (2) etc from the base name
        base_name = re.sub(r' \(\d+\)', '', name)
        
        # Get today's date
        today = datetime.now().strftime('%m-%d-%Y')
        
        # Look for any file that matches the pattern: StrengthsProfile_Name-Date.pdf
        pattern = f"StrengthsProfile_{base_name}-{today}.pdf"
        
        # List all files in directory
        for file in os.listdir(directory):
            # Remove any (1), (2) etc from existing files
            clean_file = re.sub(r' \(\d+\)\.pdf$', '.pdf', file)
            if clean_file == pattern:
                return True
        return False
        
    except Exception as e:
        logger.error(f"Error checking for duplicates: {str(e)}")
        return False

def is_duplicate_onet(directory, name):
    """Check if an O*NET file already exists for this person."""
    try:
        if not name:
            return False
            
        # First normalize the name to handle special characters
        normalized_name = normalize_name(name)
        if not normalized_name or normalized_name == "Unknown_Name":
            return False
            
        # Get current date
        current_date = datetime.now().strftime("%m%d%Y")
        
        # Generate the pattern to match
        pattern = f"O_NET_Interest_Profiler_{normalized_name}_{current_date}.pdf"
        log_scan_operation(f"Checking for O*NET duplicates with pattern: {pattern}")
        
        # List all files in directory using os.scandir() instead of os.listdir()
        try:
            for entry in os.scandir(directory):
                if not entry.is_file():
                    continue
                    
                file = entry.name
                if 'O_NET' in file.upper():
                    # Normalize the existing filename for comparison
                    existing_name = normalize_name(file)
                    if not existing_name:
                        continue
                        
                    if pattern.lower() == file.lower():
                        log_scan_operation(f"Found duplicate O*NET file: {file}")
                        return True
                        
                    # If names don't match exactly, try content comparison
                    try:
                        file_path = os.path.join(directory, file)
                        reader = PdfReader(file_path)
                        content = reader.pages[0].extract_text()
                        pdf_name = extract_name_from_onet(content)
                        if pdf_name:
                            pdf_name = normalize_name(pdf_name)
                            if pdf_name == normalized_name:
                                log_scan_operation(f"Found duplicate O*NET by content: {file}")
                                return True
                    except Exception as e:
                        logger.error(f"Error checking PDF content in {file}: {str(e)}")
                        continue
        except Exception as e:
            logger.error(f"Error listing directory {directory}: {str(e)}")
            return False
                
        log_scan_operation(f"No duplicate O*NET found for {normalized_name}")
        return False

    except Exception as e:
        logger.error(f"Error in is_duplicate_onet: {str(e)}")
        return False


def extract_name_from_pdf(self, pdf_file):
    """Extract name from PDF content using specific markers"""
    try:
        self.logger.info(f"Extracting name from PDF: {pdf_file}", extra={'event': 'EXTRACT_NAME_FROM_PDF'})
        # Open and read PDF content
        reader = PdfReader(pdf_file)
        page = reader.pages[0]
        content = page.extract_text()
        self.logger.debug(f"Extracted PDF content (first 500 chars): {repr(content[:500])}", extra={'event': 'EXTRACT_NAME_FROM_PDF'})
        
        # Determine file type from filename
        filename = os.path.basename(pdf_file).lower()
        
        # For Perfil files, first try to extract from filename if it follows the expected pattern
        if 'perfil' in filename:
            # Try to extract name from filename first (Perfil_O_NET_Profile_Name_Date.pdf)
            if '_Profile_' in filename:
                name_part = filename.split('_Profile_')[1].rsplit('_', 1)[0]
                raw_name = name_part.replace('_', ' ').strip()
                
                # Capitalize first letter of each word
                raw_name = ' '.join(word.capitalize() for word in raw_name.split())
                
                self.logger.info(f"Extracted name from Perfil filename: {raw_name}", extra={'event': 'EXTRACT_NAME_FROM_PDF'})
                return raw_name
                
            # If filename parsing fails, try content
            name = self.parse_perfil_pdf(content)
            if name:
                return name
            else:
                self.logger.error("Failed to extract name from Perfil PDF content", extra={'event': 'EXTRACT_NAME_FROM_PDF'})
                return None
            
        # For O*NET files
        elif 'o_net' in filename:
            name = self.parse_onet_pdf(content)
            if name:
                self.logger.info(f"Found name in O_NET: {name}", extra={'event': 'EXTRACT_NAME_FROM_PDF'})
                return name
            else:
                self.logger.warning(f"No name found in O_NET file: {pdf_file}", extra={'event': 'EXTRACT_NAME_FROM_PDF'})
                return None
            
        # For StrengthsProfile files
        elif filename.startswith('strengths'):
            name = self.parse_strengthsprofile_pdf(content)
            if name:
                self.logger.info(f"Found name in StrengthsProfile: {name}", extra={'event': 'EXTRACT_NAME_FROM_PDF'})
                return name
            else:
                self.logger.warning(f"No name found in StrengthsProfile file: {pdf_file}", extra={'event': 'EXTRACT_NAME_FROM_PDF'})
                return None
        else:
            self.logger.warning(f"Unknown file type: {pdf_file}", extra={'event': 'EXTRACT_NAME_FROM_PDF'})
            return None
                    
    except Exception as e:
        self.logger.error(f"Error extracting name from PDF {pdf_file}: {str(e)}", extra={'event': 'EXTRACT_NAME_FROM_PDF'})
        return None


def clean_up_duplicates(computer_name):
    """Clean up duplicate PDF files for a given computer."""
    pdf_dir = os.path.join(settings.DESTINATION_ROOT, computer_name)
    if not os.path.exists(pdf_dir):
        return
            
    # Group files by name (excluding date)
    files_by_name = {}
    for filename in os.listdir(pdf_dir):
        if not filename.endswith('.pdf'):
            continue
                
        # Extract name and date from filename (format: name_YYYY-MM-DD.pdf)
        parts = filename.rsplit('_', 1)
        if len(parts) != 2:
            continue
                
        name = parts[0]
        if name not in files_by_name:
            files_by_name[name] = []
        files_by_name[name].append(filename)
            
    # Keep only the latest file for each name
    for name, files in files_by_name.items():
        if len(files) <= 1:
            continue
                
        # Sort files by date (newest first)
        sorted_files = sorted(files, key=lambda x: x.split('_')[1], reverse=True)
            
        # Keep the newest file, delete the rest
        for old_file in sorted_files[1:]:
            try:
                os.remove(os.path.join(pdf_dir, old_file))
            except Exception as e:
                log_scan_operation(f"Error deleting duplicate file {old_file}: {str(e)}", "error", event="FILE_DELETE_ERROR")

def copy_file(source, destination):
    """Copy a file from source to destination."""
    try:
        shutil.copy(source, destination)
        log_scan_operation(f"File copied successfully: {source} -> {destination}", event="FILE_COPY_SUCCESS")
        return True
    except Exception as e:
        log_scan_operation(f"Error copying file: {str(e)}", "error", event="FILE_COPY_ERROR")
        return False

def move_file(source, destination):
    """Move a file from source to destination."""
    try:
        shutil.move(source, destination)
        log_scan_operation(f"File moved successfully: {source} -> {destination}", event="FILE_MOVE_SUCCESS")
        return True
    except Exception as e:
        log_scan_operation(f"Error moving file: {str(e)}", "error", event="FILE_MOVE_ERROR")
        return False

def delete_file(file_path):
    """Delete a file."""
    try:
        os.remove(file_path)
        log_scan_operation(f"File deleted successfully: {file_path}", event="FILE_DELETE_SUCCESS")
        return True
    except Exception as e:
        log_scan_operation(f"Error deleting file: {str(e)}", "error", event="FILE_DELETE_ERROR")
        return False