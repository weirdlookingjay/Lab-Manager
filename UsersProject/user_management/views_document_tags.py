from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Tag, DocumentTag
from .serializers import TagSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins

class DocumentTagViewSet(GenericViewSet, mixins.ListModelMixin):
    """
    ViewSet for managing document tags.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()

    @action(detail=False, methods=['get'])
    def document_tags(self, request):
        path = request.query_params.get('path')
        computer = request.query_params.get('computer')
        
        if not path or not computer:
            return Response(
                {"error": "Both path and computer parameters are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        doc_tags = DocumentTag.objects.filter(document_path=path, computer=computer)
        tags = [dt.tag for dt in doc_tags]
        serializer = TagSerializer(tags, many=True)
        return Response({"tags": serializer.data})

    @action(detail=False, methods=['post'])
    def add(self, request):
        path = request.data.get('path')
        computer = request.data.get('computer')
        tag_id = request.data.get('tag_id')
        
        if not all([path, computer, tag_id]):
            return Response(
                {"error": "path, computer, and tag_id are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        tag = get_object_or_404(Tag, id=tag_id)
        
        doc_tag, created = DocumentTag.objects.get_or_create(
            document_path=path,
            computer=computer,
            tag=tag
        )
        
        return Response({"success": True})

    @action(detail=False, methods=['post'])
    def remove(self, request):
        path = request.data.get('path')
        computer = request.data.get('computer')
        tag_id = request.data.get('tag_id')
        
        if not all([path, computer, tag_id]):
            return Response(
                {"error": "path, computer, and tag_id are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        doc_tag = get_object_or_404(
            DocumentTag, 
            document_path=path,
            computer=computer,
            tag_id=tag_id
        )
        doc_tag.delete()
        
        return Response({"success": True})

    @action(detail=False, methods=['get'])
    def tags(self, request):
        return self.list(request)

    @action(detail=False, methods=['post'])
    def create_tag(self, request):
        name = request.data.get('name')
        color = request.data.get('color')
        
        if not name:
            return Response(
                {"error": "name is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        tag = Tag.objects.create(
            name=name,
            color=color or '#3B82F6'  # Default to blue if no color provided
        )
        
        serializer = TagSerializer(tag)
        return Response(serializer.data)
