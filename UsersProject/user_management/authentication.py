from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CookieTokenAuthentication(TokenAuthentication):
    """
    Token authentication that also checks for token in cookies
    """
    def authenticate(self, request):
        # First try to get the token from the Authorization header
        auth = super().authenticate(request)
        if auth is not None:
            return auth
            
        # If no token in header, try to get it from cookies
        token = request.COOKIES.get('token')
        if not token:
            return None

        # Get the token key
        token_key = token

        # Get the user from the token
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=token_key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        if not token.user.is_active:
            raise AuthenticationFailed('User inactive or deleted')

        return (token.user, token)
