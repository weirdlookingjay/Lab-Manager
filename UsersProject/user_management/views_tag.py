from rest_framework import status, mixins
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action

from .views_base import BaseViewSet

from .authentication import CookieTokenAuthentication

from .serializers import TagSerializer

from .models import Tag

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
