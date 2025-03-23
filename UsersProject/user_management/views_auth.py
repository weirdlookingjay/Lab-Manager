from django.contrib.auth import logout, authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.parsers import JSONParser
from rest_framework import status
from .authentication import CookieTokenAuthentication

class LoginView(APIView):
    """View for user login."""
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [JSONParser]

    def post(self, request):
        """Handle login request."""
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            
            if not username or not password:
                return Response({
                    'error': 'Please provide both username and password'
                }, status=status.HTTP_400_BAD_REQUEST)

            user = authenticate(username=username, password=password)
            
            if not user:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
            # Create or get the auth token
            token, _ = Token.objects.get_or_create(user=user)
            
            # Create response with user info and token
            response = Response({
                'token': token.key,  # Include token in response body
                'user': {
                    'id': user.pk,
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff
                }
            })
            
            # Also set token in cookie
            response.set_cookie(
                'auth_token',
                token.key,
                httponly=True,
                secure=True,
                samesite='Strict'
            )
            
            return response
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutView(APIView):
    """View for user logout."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def post(self, request):
        """Handle logout request."""
        try:
            if request.auth:
                request.auth.delete()
            logout(request)
            response = Response({'detail': 'Successfully logged out'})
            response.delete_cookie('auth_token')
            return response
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
