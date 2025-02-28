import os
import logging
from datetime import datetime
import unicodedata
from PyPDF2 import PdfReader
import shutil
from .logs import log_scan_operation

logger = logging.getLogger(__name__)

def extract_name_from_onet(content):
    """Extract name from O*NET Interest Profiler PDF content."""
    try:
        logger.info("Starting O*NET name extraction", extra={'event': 'PARSE_ONET_PDF'})
        
        # Normalize line endings and clean content
        content = unicodedata.normalize('NFKC', content)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not lines:
            logger.warning("No content found in O*NET PDF", extra={'event': 'PARSE_ONET_PDF'})
            return None
            
        # Common patterns for name extraction
        english_patterns = ["printed for:", "printed for", "name:"]
        spanish_patterns = [
            "copia impresa para:", "impreso para:", "nombre:",
            "copia impr esa par a:"  # Common OCR variant
        ]
        
        # Skip patterns - these indicate lines we should not treat as names
        skip_patterns = [
            "perfil de intereses", "o*net", "onet", 
            "interest profiler", "character strengths"
        ]
        
        # First try exact patterns at start of lines
        for idx, line in enumerate(lines[:10]):  # Only check first 10 lines
            line = line.strip()
            if not line:
                continue
                
            lower_line = line.lower()
            
            # Skip if line contains any skip patterns
            if any(pattern in lower_line for pattern in skip_patterns):
                continue
                
            # Handle English versions
            for pattern in english_patterns:
                if pattern in lower_line:
                    name = line.split(":", 1)[1].strip() if ":" in line else line.replace(pattern, "", 1).strip()
                    if name and len(name.split()) >= 2:
                        # Skip if name contains any skip patterns
                        name_lower = name.lower()
                        if any(pattern in name_lower for pattern in skip_patterns):
                            continue
                        # Normalize name - capitalize each part and remove extra spaces
                        name_parts = [part.strip().capitalize() for part in name.split() if part.strip()]
                        normalized_name = " ".join(name_parts)
                        logger.info(f"Successfully extracted name from O*NET (English): {normalized_name}", extra={'event': 'PARSE_ONET_PDF'})
                        return normalized_name
            
            # Handle Spanish versions
            for pattern in spanish_patterns:
                if pattern in lower_line:
                    name = line.split(":", 1)[1].strip() if ":" in line else line.replace(pattern, "", 1).strip()
                    if name and len(name.split()) >= 2:
                        # Skip if name contains any skip patterns
                        name_lower = name.lower()
                        if any(pattern in name_lower for pattern in skip_patterns):
                            continue
                        # Normalize Spanish name
                        name_parts = [part.strip().capitalize() for part in name.split() if part.strip()]
                        normalized_name = " ".join(name_parts)
                        logger.info(f"Successfully extracted name from O*NET (Spanish): {normalized_name}", extra={'event': 'PARSE_ONET_PDF'})
                        return normalized_name
        
        # If no pattern match, check first non-empty line if it looks like a name
        first_line = lines[0].strip()
        if len(first_line.split()) >= 2:
            # Skip if line contains any skip patterns
            if not any(pattern in first_line.lower() for pattern in skip_patterns):
                name_parts = [part.strip().capitalize() for part in first_line.split() if part.strip()]
                normalized_name = " ".join(name_parts)
                logger.info(f"Extracted name from first line: {normalized_name}", extra={'event': 'PARSE_ONET_PDF'})
                return normalized_name
                        
        logger.warning("No valid name patterns found in O*NET PDF", extra={'event': 'PARSE_ONET_PDF'})
        return None
        
    except Exception as e:
        logger.error(f"Error parsing O*NET PDF: {str(e)}", extra={'event': 'PARSE_ONET_PDF'})
        return None

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

def process_onet_pdf(file_path, current_date=None):
    """Process O*NET Interest Profiler PDF and return tuple of (success, new_filename)."""
    try:
        # Skip non-O*NET files
        filename = os.path.basename(file_path).lower()
        if not any(x in filename for x in ['o_net', 'o*net', 'onet', 'perfil_o_net', 'perfil onet']):
            logger.info(f"Skipping non-O*NET file: {filename}", extra={'event': 'PROCESS_ONET_PDF'})
            return False, None
            
        # Skip VIA and other non-Interest Profiler PDFs
        if any(x in filename for x in ['via character', 'job zones', 'score report', 'clearinghouse']):
            logger.info(f"Skipping non-Interest Profiler file: {filename}", extra={'event': 'PROCESS_ONET_PDF'})
            return False, None

        # Read PDF content
        reader = PdfReader(file_path)
        content = ""
        for page in reader.pages:
            content += page.extract_text()

        # Extract name
        name = extract_name_from_onet(content)
        if not name:
            logger.warning(f"Could not extract name from O*NET PDF: {file_path}", extra={'event': 'PROCESS_ONET_PDF'})
            return False, None

        # Generate new filename
        if not current_date:
            current_date = datetime.now()
        date_str = current_date.strftime("%m%d%Y")
        
        # Normalize name for filename
        name_parts = name.split()
        normalized_parts = []
        for part in name_parts:
            # Remove special characters and normalize spaces
            clean_part = ''.join(c for c in part if c.isalnum() or c.isspace()).strip()
            if clean_part:
                normalized_parts.append(clean_part)
        
        filename_name = "_".join(normalized_parts)
        new_filename = f"O_NET_Interest_Profiler_{filename_name}_{date_str}.pdf"
        
        # Get Django media root for storing files
        from django.conf import settings
        media_root = settings.MEDIA_ROOT
        
        # Create computer-specific directory in media root
        computer_name = os.path.basename(os.path.dirname(os.path.dirname(file_path)))
        target_dir = os.path.join(media_root, computer_name)
        os.makedirs(target_dir, exist_ok=True)
        
        target_path = os.path.join(target_dir, new_filename)
        
        # Copy the file to Django media directory
        try:
            shutil.copy2(file_path, target_path)
            logger.info(f"Successfully copied file to: {target_path}", extra={'event': 'PROCESS_ONET_PDF'})
        except Exception as e:
            logger.error(f"Error copying file to {target_path}: {str(e)}", extra={'event': 'PROCESS_ONET_PDF'})
            return False, None
        
        logger.info(f"Generated new filename: {new_filename}", extra={'event': 'PROCESS_ONET_PDF'})
        return True, new_filename

    except Exception as e:
        logger.error(f"Error processing O*NET PDF {file_path}: {str(e)}", extra={'event': 'PROCESS_ONET_PDF'})
        return False, None

def normalize_name(name):
    """Normalize a name by removing spaces and special characters"""
    if not name:
        return "Unknown_Name"
        
    try:
        # Remove any extra whitespace and convert to title case
        name = " ".join(name.split()).title()
        
        # Replace spaces with underscores
        name = name.replace(" ", "_")
        
        # Remove any special characters except underscores
        name = "".join(c for c in name if c.isalnum() or c == '_')
        
        # Normalize unicode characters to ASCII
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
        
        # Ensure name is not empty after processing
        if not name:
            return "Unknown_Name"
            
        return name
        
    except Exception as e:
        logger.error(f"Error normalizing name: {str(e)}")
        return "Unknown_Name"
