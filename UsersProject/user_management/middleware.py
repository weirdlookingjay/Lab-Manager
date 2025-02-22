from django.utils import timezone
from .models import UserSession, CustomUser, LoginAttempt, PasswordPolicy
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponse

# Try to import user-agents, but don't fail if it's not installed
try:
    import user_agents
    USER_AGENTS_INSTALLED = True
except ImportError:
    USER_AGENTS_INSTALLED = False

class SessionTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if it's an API request
        is_api_request = request.path.startswith('/api/')
        
        if request.user.is_authenticated and not is_api_request:
            # Get or create session record
            session_key = request.session.session_key
            if session_key:
                # Get user agent info
                user_agent_string = request.META.get('HTTP_USER_AGENT', '')
                if USER_AGENTS_INSTALLED:
                    user_agent = user_agents.parse(user_agent_string)
                    device_type = 'mobile' if user_agent.is_mobile else 'tablet' if user_agent.is_tablet else 'desktop'
                else:
                    device_type = 'unknown'
                
                # Get IP address
                ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR')
                if ',' in ip_address:  # If multiple IP addresses, take the first one
                    ip_address = ip_address.split(',')[0].strip()
                
                try:
                    # Update or create session record
                    session, created = UserSession.objects.get_or_create(
                        session_key=session_key,
                        user=request.user,
                        defaults={
                            'ip_address': ip_address,
                            'user_agent': user_agent_string,
                            'device_type': device_type,
                        }
                    )
                    
                    if not created:
                        session.last_activity = timezone.now()
                        session.save()
                except Exception as e:
                    # Log the error but don't break the request
                    print(f"Error tracking session: {e}")
        
        return response

class LoginAttemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only track login attempts for login endpoint
        if request.path == '/api/login/' and request.method == 'POST':
            username = request.POST.get('username')
            success = response.status_code == 200
            
            if username:
                try:
                    user = CustomUser.objects.get(username=username)
                    
                    # Record login attempt
                    LoginAttempt.objects.create(
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        success=success,
                        failure_reason=None if success else 'Invalid credentials'
                    )
                    
                    if not success:
                        # Increment failed login attempts
                        user.failed_login_attempts += 1
                        
                        # Check if account should be locked
                        policy = PasswordPolicy.get_policy()
                        if user.failed_login_attempts >= policy.max_login_attempts:
                            user.locked_until = timezone.now() + timezone.timedelta(minutes=policy.lockout_duration_minutes)
                            response.data = {'error': f'Account locked for {policy.lockout_duration_minutes} minutes due to too many failed attempts'}
                            response.status_code = 403
                        
                        user.save()
                    else:
                        # Reset failed attempts on successful login
                        user.failed_login_attempts = 0
                        user.locked_until = None
                        user.save()
                        
                except CustomUser.DoesNotExist:
                    pass  # Don't reveal that the user doesn't exist
                
        return response

class PasswordPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            policy = PasswordPolicy.get_policy()
            
            # Check if password change is required
            if request.user.require_password_change and not request.path.startswith('/api/change-password/'):
                response = JsonResponse({
                    'error': 'Password change required',
                    'code': 'password_change_required'
                }, status=403)
                return response
            
            # Check if password is expired
            if request.user.last_password_change:
                days_since_change = (timezone.now() - request.user.last_password_change).days
                if days_since_change > policy.password_expiry_days:
                    request.user.require_password_change = True
                    request.user.save()
                    
                    if not request.path.startswith('/api/change-password/'):
                        response = JsonResponse({
                            'error': 'Password expired',
                            'code': 'password_expired'
                        }, status=403)
                        return response
        
        return self.get_response(request)

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if it's an admin API request
        if request.path.startswith('/api/admin/'):
            # Check if user is authenticated and is staff
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            if not request.user.is_staff:
                return JsonResponse({'error': 'Staff access required'}, status=403)
        
        return self.get_response(request)

class CustomCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = HttpResponse(status=200)
            response["Access-Control-Allow-Origin"] = "http://localhost:3000"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken, Accept, X-Requested-With"
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Max-Age"] = "86400"  # 24 hours
            return response
        
        # Handle actual request
        response = self.get_response(request)
        
        # Add CORS headers to all responses
        if not response.has_header('Access-Control-Allow-Origin'):
            response["Access-Control-Allow-Origin"] = "http://localhost:3000"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken, Accept, X-Requested-With"
            response["Access-Control-Allow-Credentials"] = "true"
        
        return response
