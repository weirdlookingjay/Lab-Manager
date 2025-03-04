import os
import logging
import threading
import subprocess
import shutil
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from PyPDF2 import PdfReader
from .authentication import CookieTokenAuthentication
from .models import Computer, AuditLog, SystemLog
from .serializers import ComputerSerializer
from .utils.scans.logs import log_scan_operation
from .utils.scans.network import cleanup_network_connections, establish_network_connection, scan_network_directory
from .utils.scans.operations import (
    find_case_insensitive_path, sanitize_filename, check_file_access,
    get_base_filename, is_duplicate_file, clean_up_duplicates,
    copy_file, move_file, delete_file
)
from .utils.scans.onet import (
    extract_name_from_onet, is_duplicate_onet, process_onet_pdf
)

logger = logging.getLogger(__name__)

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

    def _scan_single_computer(self, computer, share_path=None):
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
            if share_path is None:
                share_path = "C$\\Users"  # Default to Users directory
            files = scan_network_directory(computer.ip_address, share_path=share_path, computer_label=computer_label)
            
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
                    success, new_filename = process_onet_pdf(file_path, computer_label=computer_label)
                    if not success:
                        log_scan_operation(f"Error processing O*NET PDF {file_path}: {new_filename}", "error", event="FILE_PROCESSING_ERROR")
                        continue
                        
                    valid_files.append((file_path, new_filename))
                    
                except Exception as file_error:
                    log_scan_operation(f"Error validating file {file_path}: {str(file_error)}", "error", event="FILE_PROCESSING_ERROR")
                    continue
            
            # Only create destination directory if we have valid files to process
            if valid_files:
                # Create destination directory using computer label
                dest_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', computer_label)
                os.makedirs(dest_dir, exist_ok=True)
                log_scan_operation(f"Created destination directory for {computer_label}: {dest_dir}", event="DIRECTORY_CREATED")
                
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
                        log_scan_operation(f"Successfully copied file to: {dest_path}", event="FILE_COPIED")
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

    @action(detail=False, methods=['post'])
    def scan_directory(self, request):
        """Scan a specific directory on the computer."""
        try:
            computer = self.get_queryset().get(pk=request.data.get('computer_id'))
            directory = request.data.get('directory', '')
            
            log_scan_operation(f"Starting directory scan for {computer.label} at path: {directory}")
            
            # Get the destination directory
            dest_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', computer.label)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Scan network directory
            files = scan_network_directory(computer.ip_address, share_path=directory)
            
            if not files:
                log_scan_operation(f"No PDF files found on {computer.label}", "warning", event="NO_FILES_FOUND")
                return Response({"status": "success", "message": "No PDF files found"})
            
            # Process each file
            processed_files = []
            for file_path in files:
                try:
                    # Check if file is accessible
                    access_ok, error = check_file_access(file_path)
                    if not access_ok:
                        log_scan_operation(f"Skipping inaccessible file: {file_path} - {error}", "warning", event="FILE_ACCESS_ERROR")
                        continue
                    
                    # Process PDF based on type
                    filename = os.path.basename(file_path).lower()
                    if 'o_net' in filename or 'onet' in filename:
                        success, new_filename = process_onet_pdf(file_path, computer_label=computer.label)
                    elif 'strengthsprofile' in filename:
                        success, new_filename = process_strengthsprofile_pdf(file_path)
                    else:
                        log_scan_operation(f"Skipping unknown file type: {filename}", "warning", event="UNKNOWN_FILE_TYPE")
                        continue

                    if not success:
                        log_scan_operation(f"Error processing PDF {file_path}: {new_filename}", "error", event="FILE_PROCESSING_ERROR")
                        continue
                    
                    # Check for duplicates
                    if is_duplicate_file(new_filename, dest_dir):
                        log_scan_operation(f"Skipping duplicate file: {new_filename}", "info", event="DUPLICATE_FILE")
                        continue
                    
                    # Copy file to destination
                    dest_path = os.path.join(dest_dir, new_filename)
                    
                    if copy_file(file_path, dest_path):
                        processed_files.append(new_filename)
                    
                except Exception as e:
                    log_scan_operation(f"Error processing file {file_path}: {str(e)}", "error", event="FILE_PROCESSING_ERROR")
                    continue
            
            # Clean up duplicates
            clean_up_duplicates(computer.label)
            
            # Update computer's last scan time
            computer.last_scan = timezone.now()
            computer.save()
            
            # Create audit log entry
            AuditLog.objects.create(
                message=f"Scanned {len(processed_files)} files from {computer.label}",
                level="info",
                category="SCAN",
                event="SCAN_COMPLETE"
            )
            
            return Response({
                "status": "success",
                "message": f"Successfully processed {len(processed_files)} files",
                "processed_files": processed_files
            })
            
        except Computer.DoesNotExist:
            return Response({"error": "Computer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_scan_operation(f"Error during scan: {str(e)}", "error", event="SCAN_ERROR")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            try:
                cleanup_network_connections()
                log_scan_operation(f"Network connections cleaned up", event="NETWORK_CLEANUP")
            except Exception as e:
                log_scan_operation(f"Error cleaning up network connections: {str(e)}", "error", event="NETWORK_ERROR")
