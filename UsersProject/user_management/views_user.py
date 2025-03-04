from rest_framework import viewsets, status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action

from .authentication import CookieTokenAuthentication
from .models import  CustomUser

from .serializers import  UserSerializer


class UserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """ViewSet for managing user operations."""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        """
        Optionally restricts the returned users based on query parameters
        """
        queryset = CustomUser.objects.all().order_by('-date_joined')
        username = self.request.query_params.get('username', None)
        if username is not None:
            queryset = queryset.filter(username__icontains=username)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        users_data = []
        
        for user in queryset:
            # Default status is Active
            status_value = 'Active'
            
            # Check if user is deactivated
            if not user.is_active:
                status_value = 'Deactivated'
            
            users_data.append({
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'created': user.date_joined.strftime('%Y-%m-%d'),
                'status': status_value,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
            })
        
        return Response(users_data)

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        # Generate a random password
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        user.set_password(new_password)
        user.save()
        # In a real application, you would send this password via email
        return Response({'message': 'Password has been reset', 'new_password': new_password})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'message': 'User has been activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': 'User has been deactivated'})

    @action(detail=True, methods=['post'])
    def delete(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.is_deleted = True
        user.save()
        return Response({'message': 'User has been deleted'})

    def create(self, request, *args, **kwargs):
        # Check for existing username
        username = request.data.get('username')
        if CustomUser.objects.filter(username__iexact=username).exists():
            return Response(
                {'error': 'A user with this username already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check for existing email
        email = request.data.get('email')
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            return Response(
                {'error': 'A user with this email address already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Set password properly
            user = serializer.save()
            if 'password' in request.data:
                user.set_password(request.data['password'])
                user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def create_user(self, request):
        # Check for existing username
        username = request.data.get('username')
        if CustomUser.objects.filter(username__iexact=username).exists():
            return Response(
                {'error': 'A user with this username already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check for existing email
        email = request.data.get('email')
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            return Response(
                {'error': 'A user with this email address already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Set password properly
            user = serializer.save()
            if 'password' in request.data:
                user.set_password(request.data['password'])
            
            # Set user role
            role = request.data.get('role')
            if role == 'admin':
                user.is_staff = True
                user.is_superuser = True
            elif role == 'staff':
                user.is_staff = True
                user.is_superuser = False
            else:  # regular user
                user.is_staff = False
                user.is_superuser = False
            
            user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get('password')
        
        if not new_password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics for admin dashboard"""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        superusers = User.objects.filter(is_superuser=True).count()
        
        # Get new users in last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        new_users = User.objects.filter(date_joined__gte=thirty_days_ago).count()

        return Response({
            'totalUsers': total_users,
            'activeUsers': active_users,
            'newUsers30Days': new_users,
            'verifiedUsers': active_users,  # Assuming verified means active
            'staffUsers': staff_users,
            'superUsers': superusers,
            'lockedUsers': User.objects.filter(is_active=False).count(),
            'roleDistribution': {
                'staff': staff_users,
                'superuser': superusers,
                'regular': total_users - staff_users - superusers
            }
        })

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's information"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def suggest(self, request):
        """Get suggested users based on priority"""
        priority = request.query_params.get('priority', 'medium')
        
        # For now, just return all active users
        # In a real implementation, you would filter based on workload, expertise, etc.
        users = CustomUser.objects.filter(is_active=True)
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
