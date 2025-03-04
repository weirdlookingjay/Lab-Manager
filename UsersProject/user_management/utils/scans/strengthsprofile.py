import os
import re
import logging
from datetime import datetime
from PyPDF2 import PdfReader
from .logs import log_scan_operation

logger = logging.getLogger(__name__)

def extract_name_from_strengthsprofile(content):
    """Extract name from StrengthsProfile PDF content"""
    try:
        lines = content.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if not line or len(line) > 50:  # Skip empty lines or too long lines
                continue
            if any(marker in line.lower() for marker in ['printed for:', 'copia impresa para:']):
                continue
            if line:
                logger.info(f"Extracted name from StrengthsProfile: {line}", extra={'event': 'PARSE_STRENGTHSPROFILE_PDF'})
                return line
        return None
        
    except Exception as e:
        logger.error(f"Error parsing StrengthsProfile PDF: {str(e)}", extra={'event': 'PARSE_STRENGTHSPROFILE_PDF'})
        return None

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

def process_strengthsprofile_pdf(file_path, current_date=None):
    """Process StrengthsProfile PDF and return new filename."""
    try:
        # First read the PDF content
        reader = PdfReader(file_path)
        content = reader.pages[0].extract_text()

        # Extract name from the content
        name = extract_name_from_strengthsprofile(content)
        if not name:
            logger.error(f"Could not extract name from StrengthsProfile PDF: {file_path}")
            return False, "Could not extract name from PDF"

        # Get current date if not provided
        if not current_date:
            current_date = datetime.now()
        
        # Format date as MM-DD-YYYY
        date_str = current_date.strftime("%m-%d-%Y")
        
        # Create new filename
        new_filename = f"StrengthsProfile_{name}-{date_str}.pdf"
        
        logger.info(f"Generated new filename: {new_filename}")
        return True, new_filename
        
    except Exception as e:
        logger.error(f"Error processing StrengthsProfile PDF {file_path}: {str(e)}")
        return False, str(e)