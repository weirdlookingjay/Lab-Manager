from user_management.utils.scans.onet import process_onet_pdf, extract_name_from_onet
import glob
import os
from datetime import datetime

print('Testing Perfil O*NET file:')
files = glob.glob('//192.168.72.15/C$/Users/Client/Desktop/Perfil_O_NET_Profile_Crystal_Hidalgo_06022025.pdf')
for f in files:
    print(f'\nFile: {f}')
    print('Result:', process_onet_pdf(f))

def test_name_formatting(name, expected_filename):
    """Test name formatting for a given input name"""
    print(f"\nTesting name: {name}")
    # Create a mock PDF content with the test name
    content = f"""
    O*NET Interest Profiler
    Printed for: {name}
    Date: {datetime.now().strftime('%m/%d/%Y')}
    """
    
    # Extract name and process it
    extracted_name = extract_name_from_onet(content)
    print(f"Extracted name: {extracted_name}")
    
    # Create a temporary file path
    temp_path = "test_onet.pdf"
    
    # Test the file naming
    success, filename = process_onet_pdf(temp_path, current_date=datetime.now())
    print(f"Generated filename: {filename}")
    print(f"Expected filename pattern: {expected_filename}")
    print(f"Match: {'✓' if expected_filename in filename else '✗'}")
    print("-" * 50)

# Test cases
test_cases = [
    ("Crystal Hidalgo", "Hidalgo_Crystal"),
    ("Danielar Osario", "Osario_Danielar"),
    ("Deijamin Ar Agones", "Agones_Deijamin Ar"),
    ("Jaiky Guity", "Guity_Jaiky"),
    ("Janet Pizarr O", "O_Janet Pizarr"),
    ("Lena Zayas", "Zayas_Lena"),
    ("Penelope Harris", "Harris_Penelope"),
    ("Victor Sanche Z", "Z_Victor Sanche")
]

print("\nTesting O*NET Name Formatting\n")
print("=" * 50)

for name, expected in test_cases:
    test_name_formatting(name, expected)

print("\nTest complete!")
