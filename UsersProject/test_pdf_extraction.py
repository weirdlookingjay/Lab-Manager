import os
import sys
import django
import logging

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UsersProject.settings')
django.setup()

from user_management.pdf_processor import PDFProcessor
from user_management.scan_views import ScanViewSet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pdf_extraction():
    # Test with the StrengthsProfile test PDF
    pdf_path = os.path.join(os.path.dirname(__file__), 'data', 'StrengthsProfile-test.pdf')
    
    # Test PDFProcessor directly
    logger.info("Testing PDFProcessor directly...")
    processor = PDFProcessor()
    name = processor.extract_name_with_ocr(pdf_path)
    logger.info(f"PDFProcessor result: {name}")
    
    # Test through ScanViewSet
    logger.info("\nTesting through ScanViewSet...")
    scan_view = ScanViewSet()
    name = scan_view.extract_name_with_ocr(pdf_path)  # pdf_processor is initialized in __init__
    logger.info(f"ScanViewSet result: {name}")
    
    # Verify the results
    expected_name = "Crystal Hidalgo"
    if name == expected_name:
        logger.info(f"✓ Test passed - correctly extracted name: {name}")
    else:
        logger.error(f"✗ Test failed - expected '{expected_name}' but got '{name}'")

if __name__ == '__main__':
    test_pdf_extraction()
