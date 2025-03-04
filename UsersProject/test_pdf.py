import os
import logging
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UsersProject.settings')
django.setup()

from user_management.utils.pdf_processor import is_onet_profile

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Test the PDF
pdf_path = os.path.join('scans', 'test.pdf')
print(f"Testing PDF: {pdf_path}")
is_onet, error = is_onet_profile(pdf_path)
print(f"Is O*NET: {is_onet}")
if error:
    print(f"Error: {error}")
