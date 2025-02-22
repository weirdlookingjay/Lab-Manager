import os
import re
import PyPDF2
from datetime import datetime
from .logging import log_scan_operation

def process_onet_pdf(file_path):
    """
    Process an O*NET PDF file and rename it according to the content.
    Returns (success, new_name) tuple.
    """
    try:
        log_scan_operation(f"Opening PDF: {file_path}")
        with open(file_path, 'rb') as file:
            # Create PDF reader object
            reader = PyPDF2.PdfReader(file)
            
            # Get text from first page
            text = reader.pages[0].extract_text()
            
            # Look for O*NET code pattern (XX-XXXX.XX)
            onet_pattern = r'\d{2}-\d{4}\.\d{2}'
            match = re.search(onet_pattern, text)
            
            if not match:
                log_scan_operation(f"No O*NET code found in {file_path}", "warning")
                return False, None
                
            onet_code = match.group(0)
            
            # Look for title (usually follows the O*NET code)
            title_pattern = r'\d{2}-\d{4}\.\d{2}\s+(.*?)(?:\n|$)'
            title_match = re.search(title_pattern, text)
            
            if not title_match:
                log_scan_operation(f"No title found in {file_path}", "warning")
                return False, None
                
            title = title_match.group(1).strip()
            
            # Clean title for filename
            title = re.sub(r'[^\w\s-]', '', title)
            title = re.sub(r'[-\s]+', '_', title)
            
            # Create new filename
            timestamp = datetime.now().strftime('%Y%m%d')
            new_name = f"{onet_code}_{title}_{timestamp}.pdf"
            
            # Get directory and create new path
            directory = os.path.dirname(file_path)
            new_path = os.path.join(directory, new_name)
            
            # Rename file
            os.rename(file_path, new_path)
            log_scan_operation(f"Successfully renamed {os.path.basename(file_path)} to {new_name}")
            
            return True, new_name
            
    except Exception as e:
        log_scan_operation(f"Error processing PDF {file_path}: {str(e)}", "error")
        return False, None
