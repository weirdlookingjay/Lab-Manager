from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source='file.url', read_only=True)
    
    class Meta:
        model = Document
        fields = ['id', 'filename', 'created_at', 'size', 'url']
        read_only_fields = ['id', 'created_at', 'size', 'url']
