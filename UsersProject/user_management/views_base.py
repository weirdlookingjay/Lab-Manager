from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .authentication import CookieTokenAuthentication
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.views import APIView

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