import os
import logging
import uuid
from datetime import datetime

from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import generics
from django.conf import settings
from .authentication import CookieTokenAuthentication
from .models import DocumentTag
from django.http import HttpResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('scan_operations')

class DocumentViewSet(viewsets.ViewSet):
    """ViewSet for managing documents"""
    permission_classes = [AllowAny]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger

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
