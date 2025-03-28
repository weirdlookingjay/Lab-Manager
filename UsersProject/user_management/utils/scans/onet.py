import os
import logging
from datetime import datetime
import unicodedata
import shutil
from PyPDF2 import PdfReader
from .logs import log_scan_operation
import re

logger = logging.getLogger(__name__)

# Common patterns to skip in names
skip_patterns = [
    'test', 'sample', 'example', 'demo',
    'unknown', 'anonymous', 'unnamed',
    'user', 'student', 'client',
    'profile', 'report', 'results'
]

# Common name particles that might be part of surnames
name_particles = {
    'ar', 'de', 'del', 'dela', 'della', 'der', 'di', 'du', 'el',
    'la', 'le', 'san', 'santa', 'santo', 'st', 'ter', 'van', 'von',
    'da', 'das', 'do', 'dos', 'das', 'de la', 'del', 'della', 'der',
    'mac', 'mc', 'ben', 'ibn', 'al'
}

def validate_name(name):
    """Validate and clean a name extracted from O*NET PDF.
    
    Args:
        name: The name string to validate
        
    Returns:
        Cleaned and validated name string, or None if invalid
    """
    if not name:
        return None
        
    # Clean and normalize whitespace only
    name = " ".join(name.split())
    
    # Basic validation rules
    if any(pattern in name.lower() for pattern in skip_patterns):
        return None
        
    # Split into words
    words = name.split()
    if not words:
        return None
        
    # Process words and handle name particles
    result_words = []
    i = 0
    while i < len(words):
        current_word = words[i].lower()
        
        # Handle cases where we have remaining words
        if i < len(words) - 1:
            next_word = words[i + 1].lower()
            
            # Case 1: Current word is a name particle
            if current_word in name_particles:
                # Join particle with next word
                combined = words[i] + words[i+1]
                result_words.append(combined[0].upper() + combined[1:].lower())
                i += 2
                continue
                
            # Case 2: Next word is a single letter (likely part of surname)
            if len(next_word) == 1:
                # Join current word with the single letter
                combined = words[i] + words[i+1]
                result_words.append(combined[0].upper() + combined[1:].lower())
                i += 2
                continue
                
            # Case 3: Current word ends with 'r' or 'rr' and next word starts with 'o' (e.g. "pizarr o")
            if (current_word.endswith('r') or current_word.endswith('rr')) and next_word.startswith('o'):
                # Join the words
                combined = words[i] + words[i+1]
                result_words.append(combined[0].upper() + combined[1:].lower())
                i += 2
                continue
                
            # Case 4: Next word is a single letter followed by more words
            if len(next_word) == 1 and i < len(words) - 2:
                # Join all parts of the surname
                combined = "".join(words[i:i+3])
                result_words.append(combined[0].upper() + combined[1:].lower())
                i += 3
                continue
        
        # Regular word - capitalize first letter
        result_words.append(words[i][0].upper() + words[i][1:].lower())
        i += 1
    
    result = " ".join(result_words)
    
    # Final validation
    if not result or len(result.replace(" ", "")) < 2:
        return None
        
    return result

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
        english_patterns = [
            "printed for:", "printed for", "name:", "name",
            "profile for:", "profile for", "report for:", "report for"
        ]
        spanish_patterns = [
            "copia impresa para:", "impreso para:", "nombre:", "nombre",
            "copia impr esa par a:", "impreso par a:", "reporte para:", "reporte para"
        ]
        
        # Skip patterns - these indicate lines we should not treat as names
        skip_patterns = [
            "perfil de intereses", "o*net", "onet", "interest profiler",
            "character strengths", "page", "página", "fecha", "date",
            "report", "reporte", "results", "resultados"
        ]
        
        # First try exact patterns at start of lines
        for idx, line in enumerate(lines[:15]):  # Check first 15 lines
            line = line.strip()
            if not line:
                continue
                
            lower_line = line.lower()
            
            # Skip if line contains any skip patterns
            if any(pattern in lower_line for pattern in skip_patterns):
                continue
                
            # Handle English and Spanish versions
            for pattern in english_patterns + spanish_patterns:
                if pattern in lower_line:
                    name = line.split(":", 1)[1].strip() if ":" in line else line.replace(pattern, "", 1).strip()
                    validated_name = validate_name(name)
                    if validated_name:
                        logger.info(f"Successfully extracted name from O*NET: {validated_name}", extra={'event': 'PARSE_ONET_PDF'})
                        return validated_name
        
        # If no pattern match, check first non-empty line if it looks like a name
        for line in lines[:3]:  # Check first 3 lines for potential name
            validated_name = validate_name(line)
            if validated_name:
                logger.info(f"Extracted name from line: {validated_name}", extra={'event': 'PARSE_ONET_PDF'})
                return validated_name
                        
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

def generate_onet_filename(name, date_str):
    """Generate standardized filename for O*NET Interest Profiler PDFs.
    
    Args:
        name: The extracted name from the PDF
        date_str: Date string in MMDDYYYY format
        
    Returns:
        Standardized filename string
    """
    if not name or not date_str:
        return None
        
    # Split into name components and clean
    name_parts = name.split()
    if len(name_parts) < 2:
        return None
        
    # Keep original name order - first name followed by last name
    filename = f"O_NET_Interest_Profiler_{name.replace(' ', '_')}_{date_str}.pdf"
    
    return filename

def process_onet_pdf(file_path, current_date=None, computer_label=None):
    """
    Process O*NET Interest Profiler PDF and return tuple of (success, new_filename).
    
    Args:
        file_path: Path to the PDF file
        current_date: Optional date to use for filename (defaults to now)
        computer_label: Label of the computer being scanned (required)
    """
    try:
        # Skip non-O*NET files
        filename = os.path.basename(file_path).lower()
        if not any(x in filename for x in ['o_net', 'o*net', 'onet', 'perfil_o_net', 'perfil onet']):
            logger.info(f"Skipping non-O*NET file: {filename}")
            return False, None
            
        # Skip VIA and other non-Interest Profiler PDFs
        if any(x in filename for x in ['via character', 'job zones', 'score report', 'clearinghouse']):
            logger.info(f"Skipping non-Interest Profiler file: {filename}")
            return False, None

        # Extract name from PDF
        reader = PdfReader(file_path)
        content = ""
        for page in reader.pages:
            content += page.extract_text()
        name = extract_name_from_onet(content)
        if not name:
            logger.info(f"Could not extract name from O*NET PDF: {file_path}")
            return False, None
            
        logger.info(f"Successfully extracted name from O*NET: {name}")
        
        # Generate standardized filename
        if current_date is None:
            current_date = datetime.now()
        date_str = current_date.strftime("%m%d%Y")
        
        new_filename = generate_onet_filename(name, date_str)
        
        # Get Django media root for storing files
        from django.conf import settings
        
        # Use provided computer label or fall back to "unknown" if not provided
        dest_dir = os.path.join(settings.MEDIA_ROOT, "pdfs", computer_label or "unknown")
        os.makedirs(dest_dir, exist_ok=True)
        
        dest_path = os.path.join(dest_dir, new_filename)
        
        # Check if file already exists
        if os.path.exists(dest_path):
            logger.info(f"File already exists, skipping: {new_filename}")
            return True, new_filename
            
        # Copy file to destination
        shutil.copy2(file_path, dest_path)
        logger.info(f"Successfully copied file to: {dest_path}")
        logger.info(f"Generated new filename: {new_filename}")
        
        return True, new_filename
        
    except Exception as e:
        logger.error(f"Error processing O*NET PDF {file_path}: {str(e)}")
        return False, None

def normalize_name(name):
    """Normalize a name by removing spaces and special characters"""
    if not name:
        return "Unknown_Name"
        
    try:
        # Remove any extra whitespace but preserve original spacing
        name = " ".join(name.split())
        
        # Replace spaces with underscores while preserving name components
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
