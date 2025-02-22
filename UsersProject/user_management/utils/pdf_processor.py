import os
from datetime import datetime
import re
from PyPDF2 import PdfReader
import logging

# Get scan operations logger
logger = logging.getLogger('scan_operations')

def process_onet_pdf(file_path: str) -> tuple[bool, str]:
    """
    Process an O*NET Interest Profiler PDF file.
    Returns a tuple of (success, new_filename or error_message)
    """
    try:
        # Check if file exists and is a PDF
        if not os.path.exists(file_path) or not file_path.lower().endswith('.pdf'):
            logger.error(f"File {file_path} does not exist or is not a PDF")
            return False, "File does not exist or is not a PDF"

        # Read PDF
        logger.info(f"Reading PDF file: {file_path}")
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        # Check if it's an O*NET Interest Profiler
        if "O*NET Interest Profiler" not in text:
            logger.warning(f"File {file_path} is not an O*NET Interest Profiler PDF")
            return False, "Not an O*NET Interest Profiler PDF"

        # Look for "Printed for:" pattern
        match = re.search(r"Printed for:\s+([A-Za-z\s]+)", text)
        if not match:
            logger.warning(f"Could not find 'Printed for:' in {file_path}")
            return False, "Could not find 'Printed for:' in the document"

        # Extract name
        name = match.group(1).strip()
        logger.info(f"Extracted name from PDF: {name}")
        
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create new filename
        directory = os.path.dirname(file_path)
        new_filename = f"ONET Interest Profiler-{name}-{today}.pdf"
        new_filepath = os.path.join(directory, new_filename)
        
        # Handle duplicate filenames
        counter = 1
        while os.path.exists(new_filepath):
            logger.info(f"File {new_filepath} already exists, trying new name")
            new_filename = f"ONET Interest Profiler-{name}-{today}_{counter}.pdf"
            new_filepath = os.path.join(directory, new_filename)
            counter += 1
        
        # Rename the file
        logger.info(f"Renaming {file_path} to {new_filepath}")
        os.rename(file_path, new_filepath)
        logger.info(f"Successfully renamed PDF to: {new_filename}")
        
        return True, new_filename

    except Exception as e:
        error_msg = f"Error processing PDF {file_path}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

def is_onet_profile(file_path: str) -> bool:
    """
    Quick check if a file is an O*NET Interest Profiler PDF
    """
    try:
        if not os.path.exists(file_path) or not file_path.lower().endswith('.pdf'):
            logger.debug(f"File {file_path} does not exist or is not a PDF")
            return False

        logger.debug(f"Checking if {file_path} is an O*NET Interest Profiler")
        reader = PdfReader(file_path)
        first_page = reader.pages[0].extract_text()
        is_onet = "O*NET Interest Profiler" in first_page
        
        if is_onet:
            logger.info(f"Confirmed {file_path} is an O*NET Interest Profiler")
        else:
            logger.debug(f"File {file_path} is not an O*NET Interest Profiler")
            
        return is_onet

    except Exception as e:
        logger.error(f"Error checking if {file_path} is O*NET PDF: {str(e)}", exc_info=True)
        return False
