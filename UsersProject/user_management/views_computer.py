from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response

from .authentication import CookieTokenAuthentication
from .models import (
    Computer, AuditLog,

)

from .serializers import ComputerSerializer


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