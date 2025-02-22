from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Document
from .serializers import DocumentSerializer
import os

# Create your views here.

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Document.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        document = self.get_object()
        file_path = document.file.path
        
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{document.filename}"'
                return response
        
        return Response({'error': 'File not found'}, status=404)
