import os
from datetime import datetime
import re
from PyPDF2 import PdfReader
import logging

# Get scan operations logger
logger = logging.getLogger('scan_operations')

def is_onet_profile(file_path: str) -> tuple[bool, str]:
    """
    Quick check if a file is an O*NET Interest Profiler PDF
    Returns (is_onet, error_message)
    """
    try:
        logger.debug(f"Attempting to read PDF content from: {file_path}")
        reader = PdfReader(file_path)
        first_page = reader.pages[0].extract_text()
        
        logger.debug("Checking PDF content for O*NET indicators")
        # Check for multiple possible O*NET indicators
        onet_indicators = [
            "O*NET Interest Profiler",
            "O*NET Interest Profile",
            "O*NET Profile",
            "O_NET Interest Profiler",
            "O_NET Profile",
            "O_NET Interest Profile"
        ]
        
        # Convert page text to lowercase for case-insensitive comparison
        page_text = first_page.lower()
        
        # First try exact phrase match
        is_onet = any(indicator.lower() in page_text for indicator in onet_indicators)
        
        # If no match found, try more flexible matching
        if not is_onet:
            # Look for both O*NET and O_NET (with any characters in between)
            basic_indicators = ["o*net", "o_net"]
            has_onet = any(indicator in page_text for indicator in basic_indicators)
            
            # If we found basic O*NET indicator, also check for "interest" and "profiler"
            # to confirm it's an Interest Profiler document
            if has_onet:
                is_onet = "interest" in page_text and "profiler" in page_text
                if is_onet:
                    logger.debug("Found O*NET document using flexible matching")
        
        if is_onet:
            logger.info(f"Confirmed {file_path} is an O*NET Interest Profiler")
            return True, ""
        else:
            logger.debug(f"File {file_path} is not an O*NET Interest Profiler")
            return False, "Not an O*NET file"

    except Exception as e:
        error_msg = f"Error checking if O*NET PDF: {str(e)}"
        logger.error(f"{error_msg} for {file_path}", exc_info=True)
        return False, error_msg

def process_onet_pdf(file_path: str) -> tuple[bool, str]:
    """
    Process an O*NET Interest Profiler PDF file.
    Returns a tuple of (success, new_filename or error_message)
    """
    try:
        # First check if it's an O*NET file
        is_onet, error = is_onet_profile(file_path)
        if not is_onet:
            return False, error

        # Read PDF
        logger.info(f"Reading PDF file: {file_path}")
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        # Look for "Printed for:" pattern with improved regex
        match = re.search(r"Printed\s+for:\s*([A-Za-z\s\-']+?)(?=\n|\s*O\*NET|$)", text, re.IGNORECASE)
        if not match:
            logger.warning(f"Could not find 'Printed for:' in {file_path}")
            return False, "Could not find 'Printed for:' in the document"

        # Extract and format name
        full_name = match.group(1).strip()
        logger.debug(f"Extracted raw name: {repr(full_name)}")

        # Clean up the name
        # Remove multiple spaces and normalize hyphens/apostrophes
        full_name = re.sub(r'\s+', ' ', full_name)
        full_name = re.sub(r'[\-'']+', "'", full_name)
        logger.debug(f"Cleaned name: {repr(full_name)}")

        # Split into first and last name
        name_parts = full_name.split()
        if len(name_parts) < 2:
            return False, f"Invalid name format: {full_name}"

        # Handle special prefixes like 'Mc' and 'Mac'
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])
        
        # Convert to proper case while preserving special prefixes
        def proper_case_name(name):
            special_prefixes = ['Mc', 'Mac']
            for prefix in special_prefixes:
                if name.lower().startswith(prefix.lower()):
                    return prefix + name[len(prefix)].upper() + name[len(prefix)+1:].lower()
            return name.capitalize()

        first_name = proper_case_name(first_name)
        last_name = proper_case_name(last_name)

        # Get current date for filename
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Create new filename - all lowercase with underscores
        new_filename = f"onet_interest_profiler_{first_name.lower()}_{last_name.lower()}_{date_str}.pdf"
        logger.info(f"Generated new filename: {new_filename}")
        
        return True, new_filename

    except Exception as e:
        error_msg = f"Error processing PDF: {str(e)}"
        logger.error(f"{error_msg} for {file_path}", exc_info=True)
        return False, error_msg
