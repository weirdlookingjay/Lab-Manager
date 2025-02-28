import os
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.conf import settings
from django.shortcuts import HttpResponse, get_object_or_404
from django.db.models import Count, Sum
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from .authentication import CookieTokenAuthentication
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.authtoken.models import Token
from .utils.network import scan_network_directory
import logging
import glob
import shutil
from datetime import datetime, timedelta
import re
import uuid
import threading
import subprocess
import time
import msvcrt
import random
import string
from PyPDF2 import PdfReader
import json
import unicodedata

# Get the User model
User = get_user_model()

logger = logging.getLogger(__name__)

from .models import (
    Computer, Tag, SystemLog, AuditLog,
    ScanSchedule, LogAggregation, LogPattern,
    LogAlert, LogCorrelation, FileTransfer,
    Notification, Schedule, DocumentTag,
    PasswordHistory, PasswordPolicy, CustomUser
)
from .serializers import (
    UserSerializer, ComputerSerializer, TagSerializer,
    SystemLogSerializer, AuditLogSerializer,
    NotificationSerializer, ScanScheduleSerializer,
    LogAggregationSerializer, LogPatternSerializer,
    LogAlertSerializer, LogCorrelationSerializer
)

# Base classes for views
class BaseViewSet(viewsets.GenericViewSet):
    """Base ViewSet with CORS handling"""
    permission_classes = [AllowAny]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    
    def options(self, request, *args, **kwargs):
        response = Response()
        response["Allow"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

class BaseAPIView(APIView):
    """Base API View with CORS handling"""
    permission_classes = [AllowAny]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    
    def options(self, request, *args, **kwargs):
        response = Response()
        response["Allow"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

# Configure logging at the top of the file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_scan_operation(message, level="info", event=None):
    """Log scan operations to both file and database."""
    try:
        # Get current date for log file name
        current_date = datetime.now().strftime('%Y%m%d')
        scan_log_path = os.path.join(settings.BASE_DIR, 'logs', f'scan_operations_{current_date}.log')
        
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(scan_log_path), exist_ok=True)
        
        # Format the message with timestamp
        timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
        formatted_msg = f"{timestamp} {message}"
        
        # Log to scan operations log file
        with open(scan_log_path, 'a') as f:
            f.write(formatted_msg + '\n')
        
        # Also log to copy_log.txt
        with open(os.path.join(settings.BASE_DIR, 'copy_log.txt'), 'a') as f:
            f.write(formatted_msg + '\n')
            
        # Save to database - ensure event is not None
        if event is None:
            # Set a default event based on the message or level
            if level.upper() == 'ERROR':
                event = 'SCAN_ERROR'
            else:
                event = 'SCAN_INFO'  # Default event for non-error messages
                
        try:
            SystemLog.objects.create(
                timestamp=timezone.now(),
                message=message,
                level=level.upper(),
                category="FILE_SCAN",
                event=event
            )
        except Exception as db_error:
            print(f"Error saving to database: {str(db_error)}")
            raise
            
        # Print to console for immediate feedback
        print(formatted_msg)
            
    except Exception as e:
        print(f"Error logging: {str(e)}")
        raise  # Re-raise the exception to make sure we don't silently fail

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

def notify_scan_error(error_message):
    """Create a notification for scan errors."""
    Notification.objects.create(
        title="Scan Error",
        message=error_message,
        type="error",
        read=False
    )

def notify_scan_started():
    """Create a notification for scan start."""
    Notification.objects.create(
        title="Scan Started",
        message="A new scan has started",
        type="info",
        read=False
    )

def notify_scan_completed():
    """Create a notification for scan completion."""
    Notification.objects.create(
        title="Scan Completed",
        message="The scan has completed successfully",
        type="success",
        read=False
    )

def run_cmd_with_retry(cmd, max_retries=3, delay=2):
    """Run a command with retries and return True if successful."""
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                log_scan_operation(f"Retry attempt {attempt + 1} for command: {cmd}", event="SCAN_RETRY")
            result = subprocess.run(cmd, shell=True, check=True)
            return True
        except subprocess.CalledProcessError:
            if attempt == max_retries - 1:
                return False
            time.sleep(delay)
    return False

def cleanup_network_connections():
    """Clean up network connections."""
    try:
        # List current connections
        log_scan_operation("Listing current network connections", event="NETWORK_CHECK")
        result = subprocess.run('net use', shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Parse output to find and disconnect existing connections
            connections = result.stdout.split('\n')
            for line in connections:
                if '\\\\' in line:  # Line contains a network path
                    # Extract the network path
                    path = line.split()[1]
                    log_scan_operation(f"Disconnecting from {path}", event="NETWORK_CLEANUP")
                    # Disconnect the connection
                    subprocess.run(f'net use {path} /delete /y', shell=True, check=False)
    except Exception as e:
        log_scan_operation(f"Error cleaning up network connections: {str(e)}", "error", event="NETWORK_ERROR")

def establish_network_connection(computer_ip, username='Client', password=None):
    """Authenticate to the remote computer using net use."""
    try:
        # Clean up any existing connections first
        cleanup_network_connections()
        
        # First try with computer's credentials if provided
        if username and password:
            connect_cmd = f'net use \\\\{computer_ip}\\C$ /user:"{username}" "{password}" /persistent:no /y'
            result = subprocess.run(connect_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                log_scan_operation(f"Successfully connected to \\\\{computer_ip}\\C$ with computer credentials", event="NETWORK_CONNECTED")
                return True
                
        # If computer credentials failed or weren't provided, try admin credentials
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_password = os.getenv('ADMIN_PASSWORD')
        
        if not admin_username or not admin_password:
            log_scan_operation("Admin credentials not found in environment variables", "error", event="NETWORK_ERROR")
            return False
            
        connect_cmd = f'net use \\\\{computer_ip}\\C$ /user:"{admin_username}" "{admin_password}" /persistent:no /y'
        result = subprocess.run(connect_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            log_scan_operation(f"Successfully connected to \\\\{computer_ip}\\C$ with admin credentials", event="NETWORK_CONNECTED")
            return True
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            log_scan_operation(f"Failed to connect to {computer_ip} with both sets of credentials: {error_msg}", "error", event="NETWORK_ERROR")
            return False
            
    except Exception as e:
        log_scan_operation(f"Error connecting to {computer_ip}: {str(e)}", "error", event="NETWORK_ERROR")
        return False

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

def extract_name_from_onet(content):
    """Extract name from O*NET Interest Profiler PDF content."""
    try:
        lines = content.split('\n')
        
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if not line:
                continue
                
            lower_line = line.lower()
            if "printed for:" in lower_line:
                name = line.split(":", 1)[1].strip()
                if name and len(name.split()) >= 2:
                    logger.info(f"Extracted name from O*NET: {name}", extra={'event': 'PARSE_ONET_PDF'})
                    return name
            elif "copia impresa para:" in lower_line:
                name = line.split(":", 1)[1].strip()
                if name and len(name.split()) >= 2:
                    logger.info(f"Extracted name from O*NET: {name}", extra={'event': 'PARSE_ONET_PDF'})
                    return name
                    
        return None
        
    except Exception as e:
        logger.error(f"Error parsing O*NET PDF: {str(e)}", extra={'event': 'PARSE_ONET_PDF'})
        return None

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

def normalize_name(name):
    """Normalize a name by removing spaces and special characters"""
    if not name:
        return None
        
    # Process name in lowercase first
    name = name.strip().lower()
    
    # Replace multiple spaces with single space
    name = ' '.join(name.split())
    
    # Fix common patterns where single letters are split from names
    name = re.sub(r'([a-z]+)\s+([a-z])(?:\s|$)', r'\1\2', name)
    
    # Fix cases where two-letter prefixes are split
    name = re.sub(r'\b([a-z]{2})\s+([a-z]+)\b', r'\1\2', name)
    
    # Convert to title case after fixing patterns
    name = ' '.join(part.capitalize() for part in name.split())
    
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    
    # Remove any remaining special characters
    name = re.sub(r'[^a-zA-Z0-9_]', '', name)
    
    return name if name else "Unknown_Name"

def process_onet_pdf(file_path, current_date=None):
    """Process O*NET Interest Profiler PDF and return new filename."""
    try:
        # First read the PDF content
        reader = PdfReader(file_path)
        content = ""
        for page in reader.pages:
            content += page.extract_text()

        # Skip if this is specifically a Job Zones document
        content_lines = content.splitlines()
        
        # Check if "Job Zones" appears as a main heading (by itself on a line)
        # We look at the first few lines where headings typically appear
        for line in content_lines[:10]:
            if line.strip().lower() == 'job zones':
                logger.info(f"Skipping Job Zones document: {file_path}", extra={'event': 'PROCESS_ONET_PDF'})
                return False, "Job Zones document - not processing"

        # Now extract name from the content
        name = extract_name_from_onet(content)
        if not name:
            logger.error(f"Could not extract name from O*NET PDF: {file_path}")
            return False, "Could not extract name from PDF" 

        # Normalize name for filename
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
        name = normalize_name(name)
        
        # Get current date if not provided
        if not current_date:
            current_date = datetime.now()
        
        # Format date as MMDDYYYY
        date_str = current_date.strftime("%m%d%Y")
        
        # Create new filename in required format using the normalized name directly
        new_filename = f"O_NET_Interest_Profiler_{name}_{date_str}.pdf"
        
        logger.info(f"Generated new filename: {new_filename}")
        return True, new_filename
        
    except Exception as e:
        logger.error(f"Error processing O*NET PDF {file_path}: {str(e)}")
        return False, str(e)

def tag_document(document_name, tag_name):
    """Add a tag to a document."""
    try:
        # Get or create the tag
        tag, _ = Tag.objects.get_or_create(name=tag_name)
        
        # Create document tag
        DocumentTag.objects.get_or_create(
            document_path=document_name,
            tag=tag
        )
        logger.info(f"Added tag '{tag_name}' to document {document_name}")
        return True
    except Exception as e:
        logger.error(f"Error tagging document {document_name}: {str(e)}")
        return False

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
                logger.error(f"Error deleting duplicate file {old_file}: {str(e)}")

class UserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """ViewSet for managing user operations."""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        """
        Optionally restricts the returned users based on query parameters
        """
        queryset = CustomUser.objects.all().order_by('-date_joined')
        username = self.request.query_params.get('username', None)
        if username is not None:
            queryset = queryset.filter(username__icontains=username)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        users_data = []
        
        for user in queryset:
            # Default status is Active
            status_value = 'Active'
            
            # Check if user is deactivated
            if not user.is_active:
                status_value = 'Deactivated'
            
            users_data.append({
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'created': user.date_joined.strftime('%Y-%m-%d'),
                'status': status_value,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
            })
        
        return Response(users_data)

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        # Generate a random password
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        user.set_password(new_password)
        user.save()
        # In a real application, you would send this password via email
        return Response({'message': 'Password has been reset', 'new_password': new_password})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'message': 'User has been activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': 'User has been deactivated'})

    @action(detail=True, methods=['post'])
    def delete(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.is_deleted = True
        user.save()
        return Response({'message': 'User has been deleted'})

    def create(self, request, *args, **kwargs):
        # Check for existing username
        username = request.data.get('username')
        if CustomUser.objects.filter(username__iexact=username).exists():
            return Response(
                {'error': 'A user with this username already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check for existing email
        email = request.data.get('email')
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            return Response(
                {'error': 'A user with this email address already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Set password properly
            user = serializer.save()
            if 'password' in request.data:
                user.set_password(request.data['password'])
                user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def create_user(self, request):
        # Check for existing username
        username = request.data.get('username')
        if CustomUser.objects.filter(username__iexact=username).exists():
            return Response(
                {'error': 'A user with this username already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check for existing email
        email = request.data.get('email')
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            return Response(
                {'error': 'A user with this email address already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Set password properly
            user = serializer.save()
            if 'password' in request.data:
                user.set_password(request.data['password'])
            
            # Set user role
            role = request.data.get('role')
            if role == 'admin':
                user.is_staff = True
                user.is_superuser = True
            elif role == 'staff':
                user.is_staff = True
                user.is_superuser = False
            else:  # regular user
                user.is_staff = False
                user.is_superuser = False
            
            user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get('password')
        
        if not new_password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics for admin dashboard"""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        superusers = User.objects.filter(is_superuser=True).count()
        
        # Get new users in last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        new_users = User.objects.filter(date_joined__gte=thirty_days_ago).count()

        return Response({
            'totalUsers': total_users,
            'activeUsers': active_users,
            'newUsers30Days': new_users,
            'verifiedUsers': active_users,  # Assuming verified means active
            'staffUsers': staff_users,
            'superUsers': superusers,
            'lockedUsers': User.objects.filter(is_active=False).count(),
            'roleDistribution': {
                'staff': staff_users,
                'superuser': superusers,
                'regular': total_users - staff_users - superusers
            }
        })

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's information"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def suggest(self, request):
        """Get suggested users based on priority"""
        priority = request.query_params.get('priority', 'medium')
        
        # For now, just return all active users
        # In a real implementation, you would filter based on workload, expertise, etc.
        users = CustomUser.objects.filter(is_active=True)
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)

class ComputerViewSet(viewsets.ModelViewSet):
    """ViewSet for managing computers"""
    queryset = Computer.objects.all()
    serializer_class = ComputerSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def list(self, request):
        """List computers based on context."""
        context = request.query_params.get('context')
        computers = self.get_queryset()

        # If context is 'documents', only return computers that have documents
        if context == 'documents':
            base_dir = settings.DESTINATION_ROOT
            computers_with_docs = []
            
            for computer in computers:
                computer_dir = os.path.join(base_dir, computer.label)
                if os.path.exists(computer_dir):
                    # Check if directory has any PDF files
                    try:
                        has_pdfs = any(f.lower().endswith('.pdf') for f in os.listdir(computer_dir))
                        if has_pdfs:
                            computers_with_docs.append(computer)
                    except Exception as e:
                        logger.error(f"Error checking PDFs in {computer_dir}: {str(e)}")
            
            computers = computers_with_docs

        # Update online status before returning
        for computer in computers:
            computer.is_online = True  # TODO: Implement real online status check

        serializer = self.get_serializer(computers, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Add a new computer."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Remove a computer."""
        try:
            computer = self.get_queryset().get(pk=pk)
            computer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Computer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def perform_create(self, serializer):
        """Additional actions when creating a computer."""
        computer = serializer.save()
        # Log the creation
        AuditLog.objects.create(
            message=f'Computer {computer.label} ({computer.ip_address}) added to system',
            level='info'
        )

    def get_queryset(self):
        """Get filtered queryset based on request parameters."""
        queryset = Computer.objects.all()
        
        # Filter by online status
        is_online = self.request.query_params.get('online', None)
        if is_online is not None:
            queryset = queryset.filter(is_online=is_online.lower() == 'true')
            
        # Filter by search term
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(label__icontains=search) |
                Q(ip_address__icontains=search) |
                Q(model__icontains=search)
            )
            
        return queryset.order_by('label')

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update computer status."""
        computer = self.get_object()
        computer.is_online = request.data.get('is_online', computer.is_online)
        computer.last_seen = timezone.now()
        computer.save()
        return Response(self.get_serializer(computer).data)

    @action(detail=True, methods=['post'])
    def scan_directory(self, request, pk=None):
        """Scan a specific directory on the computer."""
        computer = self.get_object()
        directory = request.data.get('directory', '')
        try:
            log_scan_operation(f"Starting directory scan for {computer.name} at path: {directory}")
            
            # Get the destination directory
            dest_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', computer.name)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Scan network directory
            files = scan_network_directory(computer.ip_address, share_path=directory)
            
            if not files:
                log_scan_operation(f"No PDF files found on {computer.name}", "warning", event="NO_FILES_FOUND")
                success = True  # Consider this a successful scan, just with no files
                return success
                
            # Validate files and collect processable ones
            valid_files = []
            for file_path in files:
                try:
                    # Check if file is accessible
                    if not check_file_access(file_path):
                        log_scan_operation(f"Skipping inaccessible file: {file_path}", "warning", event="FILE_ACCESS_ERROR")
                        continue
                    
                    # Process O*NET PDF to get new filename
                    success, new_filename = process_onet_pdf(file_path)
                    if not success:
                        log_scan_operation(f"Error processing O*NET PDF {file_path}: {new_filename}", "error", event="FILE_PROCESSING_ERROR")
                        continue
                        
                    valid_files.append((file_path, new_filename))
                    
                except Exception as file_error:
                    log_scan_operation(f"Error validating file {file_path}: {str(file_error)}", "error", event="FILE_PROCESSING_ERROR")
                    continue
            
            # Only create destination directory if we have valid files to process
            if valid_files:
                dest_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', computer.name)
                os.makedirs(dest_dir, exist_ok=True)
                log_scan_operation(f"Created destination directory: {dest_dir}", event="DIRECTORY_CREATED")
                
                # Process valid files
                processed_count = 0
                for file_path, new_filename in valid_files:
                    try:
                        # Check for duplicates before copying
                        if is_duplicate_onet(dest_dir, new_filename):
                            log_scan_operation(f"Skipping duplicate O*NET file: {new_filename}", "info", event="DUPLICATE_FILE")
                            continue
                            
                        # Create destination path with new filename
                        dest_path = os.path.join(dest_dir, new_filename)
                        
                        # Copy file to destination with new name
                        shutil.copy2(file_path, dest_path)
                        log_scan_operation(f"Copied and renamed file: {os.path.basename(file_path)} -> {new_filename}", event="FILE_RENAMED")
                        processed_count += 1
                        
                    except Exception as copy_error:
                        log_scan_operation(f"Error copying file {file_path}: {str(copy_error)}", "error", event="FILE_PROCESSING_ERROR")
                        continue
                
                log_scan_operation(f"Successfully processed {processed_count} files from {computer.name}", event="SCAN_SUCCESS")
            else:
                log_scan_operation(f"No valid files to process from {computer.name}", "warning", event="NO_VALID_FILES")
            
            success = True
            
        except Exception as e:
            log_scan_operation(f"Error scanning {computer.name}: {str(e)}", "error", event="SCAN_ERROR")
            success = False
            
        finally:
            try:
                # Always try to disconnect and log the result
                self._disconnect_computer(computer)
                log_scan_operation(f"Successfully disconnected from {computer.name}", event="DISCONNECT_SUCCESS")
            except Exception as disconnect_error:
                log_scan_operation(f"Error disconnecting from {computer.name}: {str(disconnect_error)}", "error", event="DISCONNECT_ERROR")
                
        return success

    @action(detail=True, methods=['post'])
    def scan_directory(self, request, pk=None):
        """Scan a specific directory on the computer."""
        computer = self.get_object()
        directory = request.data.get('directory', '')
        try:
            log_scan_operation(f"Starting directory scan for {computer.name} at path: {directory}")
            
            # Get the destination directory
            dest_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', computer.name)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Scan network directory
            files = scan_network_directory(computer.ip_address, share_path=directory)
            
            if not files:
                log_scan_operation(f"No PDF files found on {computer.name}", "warning", event="NO_FILES_FOUND")
                success = True  # Consider this a successful scan, just with no files
                return success
                
            # Validate files and collect processable ones
            valid_files = []
            for file_path in files:
                try:
                    # Check if file is accessible
                    if not check_file_access(file_path):
                        log_scan_operation(f"Skipping inaccessible file: {file_path}", "warning", event="FILE_ACCESS_ERROR")
                        continue
                    
                    # Process O*NET PDF to get new filename
                    success, new_filename = process_onet_pdf(file_path)
                    if not success:
                        log_scan_operation(f"Error processing O*NET PDF {file_path}: {new_filename}", "error", event="FILE_PROCESSING_ERROR")
                        continue
                        
                    valid_files.append((file_path, new_filename))
                    
                except Exception as file_error:
                    log_scan_operation(f"Error validating file {file_path}: {str(file_error)}", "error", event="FILE_PROCESSING_ERROR")
                    continue
            
            # Only create destination directory if we have valid files to process
            if valid_files:
                dest_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', computer.name)
                os.makedirs(dest_dir, exist_ok=True)
                log_scan_operation(f"Created destination directory: {dest_dir}", event="DIRECTORY_CREATED")
                
                # Process valid files
                processed_count = 0
                for file_path, new_filename in valid_files:
                    try:
                        # Check for duplicates before copying
                        if is_duplicate_onet(dest_dir, new_filename):
                            log_scan_operation(f"Skipping duplicate O*NET file: {new_filename}", "info", event="DUPLICATE_FILE")
                            continue
                            
                        # Create destination path with new filename
                        dest_path = os.path.join(dest_dir, new_filename)
                        
                        # Copy file to destination with new name
                        shutil.copy2(file_path, dest_path)
                        log_scan_operation(f"Copied and renamed file: {os.path.basename(file_path)} -> {new_filename}", event="FILE_RENAMED")
                        processed_count += 1
                        
                    except Exception as copy_error:
                        log_scan_operation(f"Error copying file {file_path}: {str(copy_error)}", "error", event="FILE_PROCESSING_ERROR")
                        continue
                
                log_scan_operation(f"Successfully processed {processed_count} files from {computer.name}", event="SCAN_SUCCESS")
            else:
                log_scan_operation(f"No valid files to process from {computer.name}", "warning", event="NO_VALID_FILES")
            
            success = True
            
        except Exception as e:
            log_scan_operation(f"Error scanning {computer.name}: {str(e)}", "error", event="SCAN_ERROR")
            success = False
            
        finally:
            try:
                # Always try to disconnect and log the result
                self._disconnect_computer(computer)
                log_scan_operation(f"Successfully disconnected from {computer.name}", event="DISCONNECT_SUCCESS")
            except Exception as disconnect_error:
                log_scan_operation(f"Error disconnecting from {computer.name}: {str(disconnect_error)}", "error", event="DISCONNECT_ERROR")
                
        return success

class AuditLogView(BaseViewSet,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """View for managing audit logs."""
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        """Get all audit logs, optionally filtered by days."""
        # Get all logs, regardless of tags
        queryset = AuditLog.objects.all().order_by('-timestamp')
        
        # Filter by days if specified
        days = self.request.query_params.get('days', None)
        if days is not None:
            try:
                days = int(days)
                cutoff = timezone.now() - timezone.timedelta(days=days)
                queryset = queryset.filter(timestamp__gte=cutoff)
            except ValueError:
                pass
        
        return queryset

class RegisterView(viewsets.ModelViewSet):
    """ViewSet for user registration"""
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    queryset = get_user_model().objects.all()

    def get_template_names(self):
        if self.action == 'list':
            return ['user_management/register.html']
        return []

    def list(self, request, *args, **kwargs):
        return render(request, self.get_template_names()[0])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=400)

class ScanViewSet(viewsets.ViewSet):
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    _scan_in_progress = False
    _scan_queue = []
    _current_scan_stats = {
            'processed_pdfs': 0,
            'computers_scanned': 0,
            'total_computers': 0,
            'start_time': None,
            'estimated_completion': None,
            'per_computer_progress': {},
            'failed_computers': [],
            'retry_attempts': {}
        }
    MAX_RETRIES = 3
    SCAN_TIMEOUT = 3600

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure data directory exists
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.logger = logging.getLogger('scan_operations')

    def parse_onet_pdf(self, content):
        """Extract name from O*NET PDF content with improved validation and edge case handling"""
        try:
            import re
            self.logger.info(f"Parsing O*NET PDF content: {content[:200]}...", extra={'event': 'PARSE_ONET_PDF'})
            
            # First verify this is a valid O*NET Career List document
            required_markers = [
                ['Printed for:', 'Copia impresa para:'],  # English and Spanish
                ['O*NET'],  
                ['Career List', 'Lista de Carreras']  # English and Spanish
            ]
            
            # Check that at least one variant of each required marker is present
            for marker_variants in required_markers:
                if not any(marker in content for marker in marker_variants):
                    self.logger.warning(f"Missing required markers {marker_variants} in O*NET PDF", extra={'event': 'PARSE_ONET_PDF'})
                    return None
            
            # Try to extract name after English or Spanish marker
            name_markers = ['Printed for:', 'Copia impresa para:']
            raw_name = None
            for marker in name_markers:
                if marker in content:
                    # Get everything after marker up to the next newline or O*NET/Perfil
                    raw_name = content.split(marker)[1].split('\n')[0]
                    raw_name = raw_name.split('O*NET')[0].split('Perfil')[0]
                    break
                    
            if not raw_name:
                self.logger.warning("Could not find name after any known markers", extra={'event': 'PARSE_ONET_PDF'})
                return None
                
            self.logger.debug(f"Raw name after marker split: {repr(raw_name)}", extra={'event': 'PARSE_ONET_PDF'})
            
            # Clean spaces and remove any non-letter characters
            name = raw_name.strip()
            self.logger.debug(f"Name after strip: {repr(name)}", extra={'event': 'PARSE_ONET_PDF'})
            
            # Remove any non-letter characters except spaces and hyphens
            name = re.sub(r'[^a-zA-Z\s\-]', '', name)
            self.logger.debug(f"Name after removing non-letters: {repr(name)}", extra={'event': 'PARSE_ONET_PDF'})
            
            # Normalize spaces (including multiple spaces)
            name = re.sub(r'\s+', ' ', name).strip()
            self.logger.debug(f"Name after normalizing spaces: {repr(name)}", extra={'event': 'PARSE_ONET_PDF'})
            
            # Convert to lowercase for consistent processing
            name = name.lower()
            
            # Handle split prefixes first (e.g. "ar agones" -> "aragones")
            # Look for specific prefix patterns   
            name = re.sub(r'\b([a-z]{2})\s+([a-z]+)\b', r'\1\2', name)
            
            # Handle split letters at end of words (e.g., "sanche z" -> "sanchez")
            name = re.sub(r'(\w+)\s+([a-z])(?=\s|$)', r'\1\2', name)
            
            # Handle Spanish name prefixes with pattern matching
            name = re.sub(r'\b(de)\s*l?\s*(os|as?)\b', r'de \2', name)
            name = re.sub(r'\b(de)\s*la\b', r'de la', name)
            
            # Handle Mc/Mac variations with pattern matching
            name = re.sub(r'\b(mc|mac)\s*donald\b', lambda m: 'macdonald' if m.group(1) == 'mac' else 'mcdonald', name)
            
            # Convert to title case for final output
            name = ' '.join(part.capitalize() for part in name.split())
            
            # Validate name format
            if name and len(name.split()) >= 2:
                self.logger.info(f"Successfully extracted and formatted name: {name}", extra={'event': 'PARSE_ONET_PDF'})
                return name
            else:
                self.logger.warning(f"Invalid name format - too few parts: {name}", extra={'event': 'PARSE_ONET_PDF'})
                return None
            
        except Exception as e:
            self.logger.error(f"Error parsing O*NET PDF: {str(e)}", extra={'event': 'PARSE_ONET_PDF'})
            return None

    def parse_perfil_pdf(self, content):
        """Extract name from Perfil PDF content"""
        try:
            import re
            self.logger.info(f"Parsing Perfil PDF content: {repr(content[:500])}...", extra={'event': 'PARSE_PERFIL_PDF'})
            
            # Normalize spaces in content first
            normalized_content = re.sub(r'\s+', ' ', content)
            self.logger.debug(f"Normalized content: {repr(normalized_content[:200])}", extra={'event': 'PARSE_PERFIL_PDF'})
            
            # Try multiple regex patterns to handle different formats
            patterns = [
                # Standard format
                r'Copia\s+impr?e?s[ao]\s*par[ao]?\s*:?\s*([a-zA-ZáéíóúñÁÉÍÓÚÑ\s\-]+?)(?=\n|Perfil|$)',
                # Alternative format sometimes seen
                r'(?:Impreso|Imprimido)\s+para\s*:?\s*([a-zA-ZáéíóúñÁÉÍÓÚÑ\s\-]+?)(?=\n|Perfil|$)',
                # Backup pattern with just the name
                r'(?:Perfil\s+de\s+)?([a-zA-ZáéíóúñÁÉÍÓÚÑ\s\-]{2,50}?)(?=\n|Perfil|$)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, normalized_content, re.IGNORECASE)
                if match:
                    raw_name = match.group(1)
                    self.logger.debug(f"Raw name from regex: {repr(raw_name)}", extra={'event': 'PARSE_PERFIL_PDF'})
                    
                    # Clean spaces and remove any non-letter characters while preserving Spanish characters
                    name = raw_name.strip()
                    name = re.sub(r'[^a-zA-ZáéíóúñÁÉÍÓÚÑ\s\-]', '', name)
                    name = re.sub(r'\s+', ' ', name).strip()
                    self.logger.debug(f"Name after cleaning: {repr(name)}", extra={'event': 'PARSE_PERFIL_PDF'})
                    
                    # Validate name length and content
                    if name and len(name.split()) >= 1 and len(name) >= 2:
                        self.logger.info(f"Found name in Perfil: {name}", extra={'event': 'PARSE_PERFIL_PDF'})
                        return name
                    
            self.logger.warning("No valid name found in Perfil PDF", extra={'event': 'PARSE_PERFIL_PDF'})
            return None
        
        except Exception as e:
            self.logger.error(f"Error parsing Perfil PDF: {str(e)}", extra={'event': 'PARSE_PERFIL_PDF'})
            return None

    def parse_strengthsprofile_pdf(self, content):
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
                    self.logger.info(f"Extracted name from StrengthsProfile: {line}", extra={'event': 'PARSE_STRENGTHSPROFILE_PDF'})
                    return line
            return None
        
        except Exception as e:
            self.logger.error(f"Error parsing StrengthsProfile PDF: {str(e)}", extra={'event': 'PARSE_STRENGTHSPROFILE_PDF'})
            return None

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

    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a scan operation for specified computers"""
        from django.core.exceptions import ObjectDoesNotExist
        
        # Handle both request.data and _data for compatibility
        data = request.data if hasattr(request, 'data') else getattr(request, '_data', {})
        computers = data.get('computers', [])
        
        if not computers:
            return Response({"error": "No computers specified"}, status=400)

        # Convert computers to list of Computer objects
        try:
            computer_objects = []
            for computer_id in computers:
                try:
                    computer = Computer.objects.get(id=int(computer_id))
                    computer_objects.append(computer)
                except (ObjectDoesNotExist, ValueError) as e:
                    return Response({"error": f"Invalid computer ID: {computer_id}"}, status=400)
            
            if not computer_objects:
                return Response({"error": "No valid computers found"}, status=400)
                
            if self._scan_in_progress:
                return Response({"error": "Scan already in progress"}, status=400)

            self._scan_in_progress = True
            self._current_scan_stats = {
                'processed_pdfs': 0,
                'computers_scanned': 0,
                'total_computers': len(computer_objects),
                'start_time': timezone.now(),
                'estimated_completion': None,
                'per_computer_progress': {},
                'failed_computers': [],
                'retry_attempts': {}
            }

            # Start scan in background thread
            thread = threading.Thread(target=self._scan_thread, args=(computer_objects,))
            thread.daemon = True
            thread.start()
            self.logger.info(f"Started scan thread for {len(computer_objects)} computers", extra={'event': 'SCAN_START'})

            return Response({
                "message": f"Scan started for {len(computer_objects)} computers",
                "scan": self._current_scan_stats
            })
            
        except Exception as e:
            self.logger.error(f"Error starting scan: {str(e)}", extra={'event': 'SCAN_ERROR'})
            self._scan_in_progress = False
            return Response({"error": f"Failed to start scan: {str(e)}"}, status=500)

    @action(detail=False, methods=['get'])
    def folders(self, request):
        """Get list of folders that contain PDFs"""
        try:
            folders = []
            base_dir = settings.DESTINATION_ROOT
            
            for folder in os.listdir(base_dir):
                folder_path = os.path.join(base_dir, folder)
                if os.path.isdir(folder_path):
                    # Check if folder contains any PDFs
                    try:
                        has_pdfs = any(f.lower().endswith('.pdf') for f in os.listdir(folder_path))
                        if has_pdfs:
                            # Get PDF count and total size
                            pdf_count = sum(1 for f in os.listdir(folder_path) 
                                         if f.lower().endswith('.pdf'))
                            total_size = sum(os.path.getsize(os.path.join(folder_path, f))
                                          for f in os.listdir(folder_path)
                                          if f.lower().endswith('.pdf'))
                            
                            folders.append({
                                'name': folder,
                                'path': folder_path,
                                'pdf_count': pdf_count,
                                'total_size': total_size
                            })
                    except Exception as e:
                        logger.error(f"Error processing folder {folder_path}: {str(e)}")

            return Response(folders)
            
        except Exception as e:
            self.logger.error(f"Error listing folders: {str(e)}", extra={'event': 'FOLDER_LIST_ERROR'})
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get current scan status with detailed statistics."""
        if not self._scan_in_progress:
            return Response({
                "status": "idle",
                "message": "No scan in progress",
                "scanning": False
            })

        # Calculate estimated completion time
        if self._current_scan_stats['computers_scanned'] > 0:
            elapsed = (timezone.now() - self._current_scan_stats['start_time']).total_seconds()
            avg_time_per_computer = elapsed / self._current_scan_stats['computers_scanned']
            remaining_computers = self._current_scan_stats['total_computers'] - self._current_scan_stats['computers_scanned']
            estimated_remaining_seconds = avg_time_per_computer * remaining_computers
            self._current_scan_stats['estimated_completion'] = (
                timezone.now() + estimated_remaining_seconds
            ).isoformat()

        return Response({
            "status": "running",
            "message": "Scan in progress",
            "scanning": True,
            "stats": self._current_scan_stats,
            "queue_length": len(self._scan_queue)
        })

    @action(detail=False, methods=['post'])
    def stop(self, request):
        """Stop the current scan."""
        if self._scan_in_progress:
            self._scan_in_progress = False
            self._scan_queue.clear()  # Clear the queue
            return Response({"message": "Scan stopped"})
        return Response({"message": "No scan in progress"})

    def _disconnect_computer(self, computer):
        """Disconnect from a specific computer's network share"""
        try:
            ip = computer.ip_address if hasattr(computer, 'ip_address') else computer
            network_path = fr'\\{ip}\c$'
            self.logger.info(f"Disconnecting from {getattr(computer, 'label', ip)} ({network_path})", extra={'event': 'DISCONNECT_COMPUTER'})
            result = subprocess.run(['net', 'use', network_path, '/delete', '/y'], 
                         capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"Successfully disconnected from {getattr(computer, 'label', ip)}", extra={'event': 'DISCONNECT_COMPUTER'})
            else:
                # If the error is that we're not connected, that's fine
                if "The network connection could not be found" not in result.stderr:
                    self.logger.warning(f"Disconnect command for {getattr(computer, 'label', ip)} returned: {result.stderr}", extra={'event': 'DISCONNECT_COMPUTER'})
        except Exception as e:
            self.logger.error(f"Error disconnecting from {getattr(computer, 'label', ip)}: {str(e)}", extra={'event': 'DISCONNECT_COMPUTER'})

    def _connect_to_computer(self, computer):
        """Establish network connection to computer"""
        return establish_network_connection(computer.ip_address)

    def _scan_single_computer(self, computer):
        """
        Scan a single computer for PDF files.
        Returns True if scan was successful, False otherwise.
        """
        success = False
        computer_label = getattr(computer, 'label', computer.ip_address)
        try:
            log_scan_operation(f"Starting scan for computer {computer_label}", event="SCAN_START")
            
            # Connect to the computer
            if not self._connect_to_computer(computer):
                log_scan_operation(f"Failed to connect to {computer_label}", "error", event="CONNECTION_ERROR")
                return False
                
            # Scan for PDF files
            log_scan_operation(f"Searching for PDF files on {computer_label}", event="SCAN_SEARCH")
            files = scan_network_directory(computer.ip_address)
            
            if not files:
                log_scan_operation(f"No PDF files found on {computer_label}", "warning", event="NO_FILES_FOUND")
                success = True  # Consider this a successful scan, just with no files
                return success
                
            # Validate files and collect processable ones
            valid_files = []
            for file_path in files:
                try:
                    # Check if file is accessible
                    if not check_file_access(file_path):
                        log_scan_operation(f"Skipping inaccessible file: {file_path}", "warning", event="FILE_ACCESS_ERROR")
                        continue
                    
                    # Process O*NET PDF to get new filename
                    success, new_filename = process_onet_pdf(file_path)
                    if not success:
                        log_scan_operation(f"Error processing O*NET PDF {file_path}: {new_filename}", "error", event="FILE_PROCESSING_ERROR")
                        continue
                        
                    valid_files.append((file_path, new_filename))
                    
                except Exception as file_error:
                    log_scan_operation(f"Error validating file {file_path}: {str(file_error)}", "error", event="FILE_PROCESSING_ERROR")
                    continue
            
            # Only create destination directory if we have valid files to process
            if valid_files:
                dest_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', computer_label)
                os.makedirs(dest_dir, exist_ok=True)
                log_scan_operation(f"Created destination directory: {dest_dir}", event="DIRECTORY_CREATED")
                
                # Process valid files
                processed_count = 0
                for file_path, new_filename in valid_files:
                    try:
                        # Check for duplicates before copying
                        if is_duplicate_onet(dest_dir, new_filename):
                            log_scan_operation(f"Skipping duplicate O*NET file: {new_filename}", "info", event="DUPLICATE_FILE")
                            continue
                            
                        # Create destination path with new filename
                        dest_path = os.path.join(dest_dir, new_filename)
                        
                        # Copy file to destination with new name
                        shutil.copy2(file_path, dest_path)
                        log_scan_operation(f"Copied and renamed file: {os.path.basename(file_path)} -> {new_filename}", event="FILE_RENAMED")
                        processed_count += 1
                        
                    except Exception as copy_error:
                        log_scan_operation(f"Error copying file {file_path}: {str(copy_error)}", "error", event="FILE_PROCESSING_ERROR")
                        continue
                
                log_scan_operation(f"Successfully processed {processed_count} files from {computer_label}", event="SCAN_SUCCESS")
            else:
                log_scan_operation(f"No valid files to process from {computer_label}", "warning", event="NO_VALID_FILES")
            
            success = True
            
        except Exception as e:
            log_scan_operation(f"Error scanning {computer_label}: {str(e)}", "error", event="SCAN_ERROR")
            success = False
            
        finally:
            try:
                # Always try to disconnect and log the result
                self._disconnect_computer(computer)
                log_scan_operation(f"Successfully disconnected from {computer_label}", event="DISCONNECT_SUCCESS")
            except Exception as disconnect_error:
                log_scan_operation(f"Error disconnecting from {computer_label}: {str(disconnect_error)}", "error", event="DISCONNECT_ERROR")
                
        return success

    def _scan_thread(self, computers):
        """Background thread for scanning."""
        try:
            total = len(computers)
            self.logger.info(f"Starting scan thread for {total} computers", extra={'event': 'SCAN_START'})
            self._current_scan_stats = {
                'processed_pdfs': 0,
                'computers_scanned': 0,
                'total_computers': total,
                'start_time': timezone.now(),
                'estimated_completion': None,
                'per_computer_progress': {},
                'failed_computers': [],
                'retry_attempts': {}
            }
            
            for i, computer in enumerate(computers, 1):
                if not self._scan_in_progress:
                    self.logger.info("Scan cancelled", extra={'event': 'SCAN_CANCELLED'})
                    break
                
                # Update progress before starting each computer
                computer_label = getattr(computer, 'label', computer.ip_address)
                self.logger.info(f"Starting scan for computer {computer_label} ({i} of {total})", extra={'event': 'COMPUTER_SCAN_START'})
                self._current_scan_stats['per_computer_progress'][computer_label] = 0
                
                try:
                    # Do the scan with retry logic
                    success = self._scan_single_computer(computer)
                    if success:
                        self.logger.info(f"Successfully completed scan for {computer_label}", extra={'event': 'COMPUTER_SCAN_SUCCESS'})
                        self._current_scan_stats['computers_scanned'] += 1
                        self._current_scan_stats['per_computer_progress'][computer_label] = 100
                    else:
                        self.logger.error(f"Failed to complete scan for {computer_label}", extra={'event': 'COMPUTER_SCAN_FAILURE'})
                        self._current_scan_stats['failed_computers'].append(computer_label)
                except Exception as e:
                    self.logger.error(f"Error scanning {computer_label}: {str(e)}", extra={'event': 'COMPUTER_SCAN_ERROR'})
                    self._current_scan_stats['failed_computers'].append(computer_label)
                    continue
                
                # Update estimated completion time
                if i > 1:
                    elapsed = (timezone.now() - self._current_scan_stats['start_time']).total_seconds()
                    avg_time_per_computer = elapsed / i
                    remaining_computers = total - i
                    estimated_remaining_seconds = avg_time_per_computer * remaining_computers
                    self.logger.info(f"Estimated completion time: {estimated_remaining_seconds}", extra={'event': 'ESTIMATED_COMPLETION_TIME'})
                    self._current_scan_stats['estimated_completion'] = estimated_remaining_seconds

            self.logger.info(f"Scan thread completed. Successfully scanned {self._current_scan_stats['computers_scanned']} of {total} computers", extra={'event': 'SCAN_COMPLETE'})

        finally:
            self._scan_in_progress = False
            self.logger.info("Marked scan as complete", extra={'event': 'SCAN_COMPLETE'})

    @action(detail=False, methods=['get', 'post', 'put', 'delete'])
    def schedule(self, request):
        """Get, create, update, or delete the current user's scan schedule"""
        if request.method == 'GET':
            try:
                schedule = ScanSchedule.objects.get(user=request.user)
                serializer = ScanScheduleSerializer(schedule)
                return Response({'schedule': serializer.data})
            except ScanSchedule.DoesNotExist:
                return Response({'detail': 'No schedule found'}, status=404)
        
        elif request.method in ['POST', 'PUT']:
            logger.info(f"Received schedule update request. Data: {request.data}")
            try:
                schedule = ScanSchedule.objects.get(user=request.user)
                logger.info(f"Found existing schedule: {schedule.id}")
                serializer = ScanScheduleSerializer(schedule, data=request.data, partial=True)
            except ScanSchedule.DoesNotExist:
                logger.info("No existing schedule found, creating new one")
                serializer = ScanScheduleSerializer(data=request.data)
            
            if not serializer.is_valid():
                logger.error(f"Validation errors: {serializer.errors}")
                return Response({'errors': serializer.errors}, status=400)
            
            try:
                instance = serializer.save(user=request.user)
                logger.info(f"Schedule saved successfully. ID: {instance.id}")
                return Response({'schedule': serializer.data}, status=201 if request.method == 'POST' else 200)
            except Exception as e:
                logger.error(f"Error saving schedule: {str(e)}")
                return Response({'error': str(e)}, status=400)
        
        elif request.method == 'DELETE':
            try:
                schedule = ScanSchedule.objects.get(user=request.user)
                schedule.delete()
                return Response({'status': 'Schedule deleted successfully'})
            except ScanSchedule.DoesNotExist:
                return Response({'status': 'No schedule exists'})

    @action(detail=True, methods=['post'])
    def run_schedule(self, request, pk=None):
        """Execute a scan schedule immediately"""
        try:
            schedule = ScanSchedule.objects.get(pk=pk)
        except ScanSchedule.DoesNotExist:
            return Response({'error': 'Schedule not found'}, status=404)
        
        if not schedule.computers.exists():
            return Response(
                {'error': 'No computers selected for this schedule'},
                status=400
            )

        if self._scan_in_progress:
            return Response({"error": "Scan already in progress"}, status=400)

        # Get the computers for this schedule
        computers = list(schedule.computers.all())
        
        # Initialize scan stats with string computer labels
        computer_progress = {str(computer.label): 0 for computer in computers}
        
        self._scan_in_progress = True
        self._current_scan_stats = {
            'processed_pdfs': 0,
            'computers_scanned': 0,
            'total_computers': len(computers),
            'start_time': timezone.now(),
            'estimated_completion': None,
            'per_computer_progress': computer_progress,
            'failed_computers': [],
            'retry_attempts': {}
        }

        try:
            # Start scan in background thread
            thread = threading.Thread(target=self._scan_thread, args=(computers,))
            thread.daemon = True
            thread.start()

            return Response({
                'status': 'Scan started successfully',
                'scan': self._current_scan_stats
            })
            
        except Exception as e:
            self._scan_in_progress = False
            logger.error(f"Failed to start scan: {str(e)}", extra={'event': 'SCAN_START_ERROR'})
            return Response(
                {'error': f'Failed to start scan: {str(e)}'},
                status=500
            )

class TagViewSet(mixins.ListModelMixin,
              mixins.CreateModelMixin,
              mixins.DestroyModelMixin,
              BaseViewSet):
    """ViewSet for managing tags"""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    
    def list(self, request):
        """Get all tags"""
        tags = Tag.objects.all()
        return Response([{
            'id': tag.id,
            'name': tag.name,
            'color': tag.color,
            'created_at': tag.created_at
        } for tag in tags])

    def create(self, request):
        """Create a new tag"""
        name = request.data.get('name')
        color = request.data.get('color', '#3B82F6')
        
        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            tag = Tag.objects.create(name=name, color=color)
            return Response({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'created_at': tag.created_at
            })
        except IntegrityError:
            return Response({'error': 'Tag already exists'}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Delete a tag"""
        try:
            tag = Tag.objects.get(id=pk)
            tag.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Tag.DoesNotExist:
            return Response({'error': 'Tag not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def add_to_document(self, request):
        """Add a tag to a document"""
        tag_id = request.data.get('tag_id')
        document_path = request.data.get('document_path')
        computer = request.data.get('computer')
        
        if not all([tag_id, document_path, computer]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            tag = Tag.objects.get(id=tag_id)
            doc_tag = DocumentTag.objects.create(
                document_path=document_path,
                computer=computer,
                tag=tag
            )
            return Response({
                'id': doc_tag.id,
                'tag': {
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color
                }
            })
        except Tag.DoesNotExist:
            return Response({'error': 'Tag not found'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'error': 'Document already has this tag'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def remove_from_document(self, request):
        """Remove a tag from a document"""
        tag_id = request.data.get('tag_id')
        document_path = request.data.get('document_path')
        computer = request.data.get('computer')
        
        if not all([tag_id, document_path, computer]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            doc_tag = DocumentTag.objects.get(
                tag_id=tag_id,
                document_path=document_path,
                computer=computer
            )
            doc_tag.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DocumentTag.DoesNotExist:
            return Response({'error': 'Document does not have this tag'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def document_tags(self, request):
        """Get tags for a specific document"""
        document_path = request.query_params.get('document_path')
        computer = request.query_params.get('computer')
        
        if not all([document_path, computer]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
        
        doc_tags = DocumentTag.objects.filter(
            document_path=document_path,
            computer=computer
        ).select_related('tag')
        
        return Response([{
            'id': dt.tag.id,
            'name': dt.tag.name,
            'color': dt.tag.color
        } for dt in doc_tags])

class DocumentViewSet(viewsets.ViewSet):
    """ViewSet for managing documents"""
    permission_classes = [AllowAny]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def list(self, request):
        """List all documents with advanced filtering and sorting."""
        try:
            # Get query parameters
            computer = request.query_params.get('computer', None)
            search = request.query_params.get('search', '')
            sort_by = request.query_params.get('sort_by', 'name')
            sort_order = request.query_params.get('sort_order', 'asc')
            page = int(request.query_params.get('page', 1))
            per_page = int(request.query_params.get('per_page', 10))

            if computer == 'null':
                computer = None

            # Get all PDF files in the computer directory
            documents = []
            base_dir = os.path.join(settings.DESTINATION_ROOT)
            
            # If computer is specified, only look in that computer's folder
            if computer:
                computer_dirs = [os.path.join(base_dir, computer)]
            else:
                # Otherwise look in all computer folders
                try:
                    computer_dirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) 
                                   if os.path.isdir(os.path.join(base_dir, d))]
                except Exception as e:
                    logger.error(f"Error listing base directory {base_dir}: {str(e)}")
                    computer_dirs = []

            self.logger.info(f"Searching directories: {computer_dirs}")
            
            for computer_dir in computer_dirs:
                computer_name = os.path.basename(computer_dir)
                if os.path.exists(computer_dir):
                    try:
                        for filename in os.listdir(computer_dir):
                            if filename.lower().endswith('.pdf'):
                                file_path = os.path.join(computer_dir, filename)
                                
                                # Get tags for this document
                                doc_tags = DocumentTag.objects.filter(
                                    document_path=file_path,
                                    computer=computer_name
                                ).select_related('tag')
                                
                                tags = [{
                                    'id': tag.tag.id,
                                    'name': tag.tag.name,
                                    'color': tag.tag.color
                                } for tag in doc_tags]
                                
                                # Format size to be human readable
                                size = os.path.getsize(file_path)
                                
                                # Format date in a more readable way
                                modified_date = datetime.fromtimestamp(os.path.getmtime(file_path))
                                
                                documents.append({
                                    'id': str(uuid.uuid4()),
                                    'name': filename,
                                    'path': file_path,
                                    'size': size,
                                    'created': modified_date.isoformat(),
                                    'tags': tags
                                })
                    except Exception as e:
                        logger.error(f"Error processing directory {computer_dir}: {str(e)}")

            # Filter documents by search query
            if search:
                documents = [doc for doc in documents if search.lower() in doc['name'].lower()]

            # Sort documents
            reverse = sort_order.lower() == 'desc'
            if sort_by == 'name':
                documents.sort(key=lambda x: x['name'].lower(), reverse=reverse)
            elif sort_by == 'size':
                documents.sort(key=lambda x: x['size'], reverse=reverse)
            elif sort_by == 'created':
                documents.sort(key=lambda x: x['created'], reverse=reverse)

            # Calculate pagination
            total_items = len(documents)
            total_pages = (total_items + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            
            # Get documents for current page
            documents_page = documents[start_idx:end_idx]

            return Response({
                'documents': documents_page,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_items': total_items,
                    'per_page': per_page
                }
            })

        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def download(self, request):
        """Download or preview a specific document."""
        try:
            path = request.query_params.get('path')
            preview = request.query_params.get('preview', 'false').lower() == 'true'
            
            if not path:
                return Response({'error': 'Path parameter is required'}, status=400)
            
            # If path is relative to a computer folder, construct full path
            if not os.path.isabs(path):
                # Split path into computer and filename
                parts = path.split('\\')
                if len(parts) >= 2:
                    computer = parts[0]
                    filename = parts[-1]
                    path = os.path.join(settings.DESTINATION_ROOT, computer, filename)
            
            # Verify file exists
            if not os.path.exists(path):
                return Response({'error': f'File not found: {path}'}, status=404)
            
            # Open and return the file
            with open(path, 'rb') as f:
                file_data = f.read()
                
            response = HttpResponse(file_data, content_type='application/pdf')
            
            if not preview:
                # For downloads, set content-disposition to attachment
                filename = os.path.basename(path)
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error in document download: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NotificationViewSet(BaseViewSet,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        """Get notifications ordered by timestamp"""
        return Notification.objects.all().order_by('-timestamp')

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(read=False).count()
        return Response({'count': count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a notification"""
        notification = self.get_object()
        notification.archived = True
        notification.save()
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Unarchive a notification"""
        notification = self.get_object()
        notification.archived = False
        notification.save()
        return Response({'status': 'success'})

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing audit logs."""
    queryset = SystemLog.objects.all().order_by('-timestamp')
    serializer_class = SystemLogSerializer
    authentication_classes = []  # No authentication required
    permission_classes = []      # No permissions required
    
    def list(self, request):
        """List audit logs with optional filtering."""
        try:
            # Get query parameters
            level = request.query_params.get('level', None)
            search = request.query_params.get('search', None)
            
            # Start with all logs
            logs = self.queryset
            
            # Apply filters
            if level:
                logs = logs.filter(level=level)
            if search:
                logs = logs.filter(message__icontains=search)
            
            # Paginate results
            page = self.paginate_queryset(logs)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(logs, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=500)

class LogAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing log alerts"""
    queryset = LogAlert.objects.all().order_by('-triggered_at')
    serializer_class = LogAlertSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by acknowledgement status
        acknowledged = self.request.query_params.get('acknowledged')
        if acknowledged is not None:
            queryset = queryset.filter(acknowledged=acknowledged.lower() == 'true')

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(triggered_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(triggered_at__lte=end_date)

        return queryset

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert"""
        alert = self.get_object()
        alert.acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        return Response({'status': 'alert acknowledged'})


class LogAggregationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing aggregated logs"""
    serializer_class = LogAggregationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        queryset = LogAggregation.objects.all()
        
        # Filter by period
        period = self.request.query_params.get('period', None)
        if period:
            queryset = queryset.filter(period=period)

        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        # Filter by level
        level = self.request.query_params.get('level', None)
        if level:
            queryset = queryset.filter(level=level)

        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__lte=end_date)

        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get a summary of aggregated logs"""
        period = request.query_params.get('period', 'DAY')
        days = int(request.query_params.get('days', 7))
        
        end_time = timezone.now()
        start_time = end_time - timezone.timedelta(days=days)
        
        # Get aggregated data
        aggregations = LogAggregation.objects.filter(
            period=period,
            start_time__gte=start_time,
            end_time__lte=end_time
        )

        # Calculate statistics
        total_logs = sum(agg.count for agg in aggregations)
        total_errors = sum(agg.error_count for agg in aggregations)
        total_warnings = sum(agg.warning_count for agg in aggregations)
        
        # Get trend data
        trend_data = aggregations.values('start_time').annotate(
            total=Sum('count'),
            errors=Sum('error_count'),
            warnings=Sum('warning_count')
        ).order_by('start_time')

        # Get top categories
        top_categories = aggregations.values('category').annotate(
            total=Sum('count')
        ).order_by('-total')[:5]

        return Response({
            'total_logs': total_logs,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'error_rate': (total_errors / total_logs * 100) if total_logs > 0 else 0,
            'warning_rate': (total_warnings / total_logs * 100) if total_logs > 0 else 0,
            'trend_data': trend_data,
            'top_categories': top_categories
        })

class LogCorrelationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing log correlations"""
    queryset = LogCorrelation.objects.all().order_by('-created_at')
    serializer_class = LogCorrelationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by correlation type
        correlation_type = self.request.query_params.get('correlation_type')
        if correlation_type:
            queryset = queryset.filter(correlation_type=correlation_type)

        # Filter by confidence score
        min_confidence = self.request.query_params.get('min_confidence')
        if min_confidence:
            queryset = queryset.filter(confidence_score__gte=float(min_confidence))

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset

class LogPatternViewSet(viewsets.ModelViewSet):
    """ViewSet for managing log patterns"""
    serializer_class = LogPatternSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        return LogPattern.objects.all()

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply a log pattern to logs"""
        pattern = self.get_object()
        # Get logs that match the pattern
        matching_logs = SystemLog.objects.filter(message__icontains=pattern.pattern)
        # Update logs with pattern info
        matching_logs.update(pattern=pattern)
        return Response({
            'status': 'pattern applied',
            'matched_logs': matching_logs.count()
        })

    @action(detail=False, methods=['post'])
    def discover(self, request):
        """Discover new log patterns"""
        logs = SystemLog.objects.filter(pattern__isnull=True)
        # TODO: Implement pattern discovery logic
        # This would involve analyzing log messages to find common patterns
        return Response({
            'status': 'pattern discovery initiated',
            'logs_analyzed': logs.count()
        })

class ScanScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing scan schedules"""
    serializer_class = ScanScheduleSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    
    logger = logging.getLogger('user_management')

    def get_queryset(self):
        queryset = ScanSchedule.objects.all()
        
        # Filter by user if not admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
            
        # Filter by enabled status
        enabled = self.request.query_params.get('enabled')
        if enabled is not None:
            queryset = queryset.filter(enabled=enabled.lower() == 'true')
            
        # Filter by schedule type
        schedule_type = self.request.query_params.get('type')
        if schedule_type:
            queryset = queryset.filter(type=schedule_type)
            
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """Set the user when creating a new schedule"""
        try:
            self.logger.debug(f"Creating new scan schedule with data: {self.request.data}")
            serializer.save(user=self.request.user)
            self.logger.debug("Successfully created scan schedule")
        except Exception as e:
            self.logger.error(f"Failed to create scan schedule: {str(e)}")
            raise

    def create(self, request, *args, **kwargs):
        """Override create to add detailed error logging"""
        try:
            self.logger.debug(f"Received create request with data: {request.data}")
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                self.logger.error(f"Validation failed: {serializer.errors}")
                return Response({"error": "Failed to create schedule", "details": serializer.errors}, status=400)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)
        except Exception as e:
            self.logger.error(f"Unexpected error in create: {str(e)}")
            return Response({"error": "Failed to create schedule", "details": str(e)}, status=500)

    def list(self, request, *args, **kwargs):
        """Override list method to return schedules directly"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve method to return single schedule in consistent format"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'schedule': serializer.data})

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """Enable a scan schedule"""
        schedule = self.get_object()
        schedule.enabled = True
        schedule.save()
        return Response({'status': 'schedule enabled'})

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """Disable a scan schedule"""
        schedule = self.get_object()
        schedule.enabled = False
        schedule.save()
        return Response({'status': 'schedule disabled'})

    @action(detail=False, methods=['get', 'post', 'put', 'delete'])
    def current(self, request):
        """Get, create, update, or delete the current user's scan schedule"""
        if request.method == 'GET':
            try:
                schedule = ScanSchedule.objects.get(user=request.user)
                serializer = self.get_serializer(schedule)
                return Response({'schedule': serializer.data})
            except ScanSchedule.DoesNotExist:
                return Response({'detail': 'No schedule found'}, status=404)
        
        elif request.method in ['POST', 'PUT']:
            logger.info(f"Received schedule update request. Data: {request.data}")
            try:
                schedule = ScanSchedule.objects.get(user=request.user)
                logger.info(f"Found existing schedule: {schedule.id}")
                serializer = self.get_serializer(schedule, data=request.data, partial=True)
            except ScanSchedule.DoesNotExist:
                logger.info("No existing schedule found, creating new one")
                serializer = self.get_serializer(data=request.data)
            
            if not serializer.is_valid():
                logger.error(f"Validation errors: {serializer.errors}")
                return Response({'errors': serializer.errors}, status=400)
            
            try:
                instance = serializer.save(user=request.user)
                logger.info(f"Schedule saved successfully. ID: {instance.id}")
                return Response({'schedule': serializer.data}, status=201 if request.method == 'POST' else 200)
            except Exception as e:
                logger.error(f"Error saving schedule: {str(e)}")
                return Response({'error': str(e)}, status=400)
        
        elif request.method == 'DELETE':
            try:
                schedule = ScanSchedule.objects.get(user=request.user)
                schedule.delete()
                return Response({'status': 'Schedule deleted successfully'})
            except ScanSchedule.DoesNotExist:
                return Response({'status': 'No schedule exists'})

    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Execute a scan schedule immediately"""
        import threading
        import subprocess
        import time
        from django.utils import timezone
        
        schedule = self.get_object()
        
        if not schedule.computers.exists():
            return Response(
                {'error': 'No computers selected for this schedule'},
                status=400
            )

        if self._scan_in_progress:
            return Response({"error": "Scan already in progress"}, status=400)
            
        # Get the ScanViewSet instance
        scan_viewset = ScanViewSet()
        
        if scan_viewset._scan_in_progress:
            return Response({"error": "Scan already in progress"}, status=400)
            
        # Get the computers for this schedule
        computers = list(schedule.computers.all())
        
        # Initialize scan stats with string computer labels
        computer_progress = {str(computer.label): 0 for computer in computers}
        
        scan_viewset._scan_in_progress = True
        scan_viewset._current_scan_stats = {
            'processed_pdfs': 0,
            'computers_scanned': 0,
            'total_computers': len(computers),
            'start_time': timezone.now(),
            'estimated_completion': None,
            'per_computer_progress': computer_progress,
            'failed_computers': [],
            'retry_attempts': {}
        }

        try:
            # Start scan in background thread
            thread = threading.Thread(target=scan_viewset._scan_thread, args=(computers,))
            thread.daemon = True
            thread.start()
            self.logger.info(f"Started scan thread for {len(computers)} computers")

            return Response({
                'status': 'Scan started successfully',
                'scan': scan_viewset._current_scan_stats
            })
            
        except Exception as e:
            scan_viewset._scan_in_progress = False
            logger.error(f"Failed to start scan: {str(e)}", extra={'event': 'SCAN_START_ERROR'})
            return Response(
                {'error': f'Failed to start scan: {str(e)}'},
                status=500
            )

class LoginView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication needed for login
    parser_classes = [JSONParser]  # Add explicit JSON parser
    
    def post(self, request):
        try:
            logger.info("Login attempt received")
            username = request.data.get('username')
            password = request.data.get('password')
            
            logger.info(f"Login attempt for user: {username}")
            
            if not username or not password:
                return Response({'error': 'Please provide both username and password'},
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Check if account is locked
            try:
                user = CustomUser.objects.get(username=username)
                logger.info(f"Found user: {username}")
                if user.locked_until and user.locked_until > timezone.now():
                    minutes_remaining = int((user.locked_until - timezone.now()).total_seconds() / 60)
                    return Response({
                        'error': f'Account is locked. Try again in {minutes_remaining} minutes.'
                    }, status=status.HTTP_403_FORBIDDEN)
            except CustomUser.DoesNotExist:
                logger.warning(f"User not found: {username}")
                pass  # Don't reveal that the user doesn't exist
            
            user = authenticate(username=username, password=password)
            
            if not user:
                logger.warning(f"Authentication failed for user: {username}")
                return Response({'error': 'Invalid credentials'},
                              status=status.HTTP_401_UNAUTHORIZED)
            
            logger.info(f"User authenticated successfully: {username}")
            
            # Check if password change is required
            if user.require_password_change:
                return Response({
                    'error': 'Password change required',
                    'code': 'password_change_required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Create or rotate API key
            token, created = Token.objects.get_or_create(user=user)
            if not created:
                # Check if token has expired
                token_age = timezone.now() - token.created
                if token_age.total_seconds() > getattr(settings, 'TOKEN_EXPIRED_AFTER_SECONDS', 86400):
                    # Delete old token and create new one
                    token.delete()
                    token = Token.objects.create(user=user)
            
            # Update last login
            user.last_login = timezone.now()
            user.save()
            
            logger.info(f"Login successful for user: {username}")
            return Response({
                'token': token.key,
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff,
                    'require_password_change': user.require_password_change
                }
            })
        except Exception as e:
            logger.error(f"Error in login view: {str(e)}", exc_info=True)
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            'error': 'Please provide both username and password'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user is not None:
        if user.is_active:
            login(request, user)
            
            # Get or create token
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            })
        else:
            return Response({
                'error': 'This account is not active.'
            }, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=401)
        
    stats = {
        'totalUsers': CustomUser.objects.count(),
        'activeComputers': Computer.objects.filter(is_online=True).count(),
        'totalDocuments': DocumentTag.objects.values('document_path', 'computer').distinct().count(),
        'recentScans': FileTransfer.objects.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(days=1)
        ).count(),
    }
    
    recent_logs = AuditLog.objects.order_by('-timestamp')[:5].values('message', 'timestamp')
    
    return Response({
        'stats': stats,
        'recent_logs': recent_logs
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users(request):
    """Get list of users"""
    users = get_user_model().objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

class ChangePasswordView(APIView):
    """View for changing user password"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'error': 'Invalid old password'}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({'status': 'password changed'})

class LogViewSet(BaseViewSet):
    permission_classes = [AllowAny]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def list(self, request):
        """List all logs"""
        logs = SystemLog.objects.all().order_by('-timestamp')[:100]  # Get latest 100 logs
        serializer = SystemLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics for logs and alerts"""
        # Get counts for different alert types
        warning_count = SystemLog.objects.filter(level='WARNING').count()
        critical_count = SystemLog.objects.filter(level='CRITICAL').count()
        pending_count = SystemLog.objects.filter(status='PENDING').count()
        overdue_count = SystemLog.objects.filter(status='OVERDUE').count()

        # Get activity data for the last 7 days
        today = timezone.now()
        seven_days_ago = today - timezone.timedelta(days=7)
        activity_data = []

        for i in range(7):
            date = seven_days_ago + timezone.timedelta(days=i)
            next_date = date + timezone.timedelta(days=1)
            
            day_data = {
                'date': date.strftime('%Y-%m-%d'),
                'opened': SystemLog.objects.filter(
                    timestamp__gte=date,
                    timestamp__lt=next_date,
                    status='OPEN'
                ).count(),
                'resolved': SystemLog.objects.filter(
                    timestamp__gte=date,
                    timestamp__lt=next_date,
                    status='RESOLVED'
                ).count()
            }
            activity_data.append(day_data)

        # Get computer status
        total_computers = Computer.objects.count()
        up_to_date_computers = Computer.objects.filter(is_online=True).count()

        summary_data = {
            'total_logs': SystemLog.objects.count(),
            'warning_count': warning_count,
            'critical_count': critical_count,
            'pending_count': pending_count,
            'overdue_count': overdue_count,
            'activity_data': activity_data,
            'computer_status': {
                'up_to_date': up_to_date_computers,
                'total': total_computers
            }
        }

        return Response(summary_data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    """Get admin dashboard statistics"""
    User = get_user_model()
    
    # Get total users count
    total_users = User.objects.count()
    
    # Get active users (not deactivated or deleted)
    active_users = User.objects.filter(is_active=True).count()
    
    # Get users created in last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    # Get user role distribution
    user_roles = User.objects.values('role').annotate(count=Count('id'))
    role_counts = {role['role']: role['count'] for role in user_roles}
    
    # Get verified vs unverified users
    verified_users = User.objects.filter(is_verified=True).count()
    
    stats = {
        'totalUsers': total_users,
        'activeUsers': active_users,
        'newUsers30Days': new_users,
        'verifiedUsers': verified_users,
        'roleDistribution': role_counts,
        'staffUsers': User.objects.filter(is_staff=True).count(),
        'superUsers': User.objects.filter(is_superuser=True).count(),
        'lockedUsers': User.objects.filter(locked_until__gt=timezone.now()).count()
    }
    
    return Response(stats)