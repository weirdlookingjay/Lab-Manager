import os
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.conf import settings
from django.shortcuts import HttpResponse, get_object_or_404
from django.db.models import Count, Sum
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.exceptions import ValidationError
from django.db import models
from django.db.models import Value

from .authentication import CookieTokenAuthentication
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.authtoken.models import Token
# from .utils.network import scan_network_directory
import logging

from datetime import datetime, timedelta
import re

import subprocess
import time
from PyPDF2 import PdfReader
import json
import unicodedata

from .views_base import BaseAPIView, BaseViewSet

# Get the User model
User = get_user_model()

logger = logging.getLogger(__name__)

from .models import (
    Computer, Tag, SystemLog, AuditLog,
    ScanSchedule, LogAggregation, LogPattern,
    LogAlert, LogCorrelation, FileTransfer,
    Notification, Schedule, DocumentTag,
    PasswordHistory, PasswordPolicy, CustomUser
)
from .serializers import (
    UserSerializer, ComputerSerializer, TagSerializer,
    SystemLogSerializer, AuditLogSerializer,
    NotificationSerializer, ScanScheduleSerializer,
    LogAggregationSerializer, LogPatternSerializer,
    LogAlertSerializer, LogCorrelationSerializer
)


# Configure logging at the top of the file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def notify_scan_error(error_message):
    """Create a notification for scan errors."""
    Notification.objects.create(
        title="Scan Error",
        message=error_message,
        type="error",
        read=False
    )

def notify_scan_started():
    """Create a notification for scan start."""
    Notification.objects.create(
        title="Scan Started",
        message="A new scan has started",
        type="info",
        read=False
    )

def notify_scan_completed():
    """Create a notification for scan completion."""
    Notification.objects.create(
        title="Scan Completed",
        message="The scan has completed successfully",
        type="success",
        read=False
    )

def run_cmd_with_retry(cmd, max_retries=3, delay=2):
    """Run a command with retries and return True if successful."""
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                log_scan_operation(f"Retry attempt {attempt + 1} for command: {cmd}", event="SCAN_RETRY")
            result = subprocess.run(cmd, shell=True, check=True)
            return True
        except subprocess.CalledProcessError:
            if attempt == max_retries - 1:
                return False
            time.sleep(delay)
    return False


def normalize_name(name):
    """Normalize a name by removing spaces and special characters"""
    if not name:
        return None
        
    # Process name in lowercase first
    name = name.strip().lower()
    
    # Replace multiple spaces with single space
    name = ' '.join(name.split())
    
    # Fix common patterns where single letters are split from names
    name = re.sub(r'([a-z]+)\s+([a-z])(?:\s|$)', r'\1\2', name)
    
    # Fix cases where two-letter prefixes are split
    name = re.sub(r'\b([a-z]{2})\s+([a-z]+)\b', r'\1\2', name)
    
    # Convert to title case after fixing patterns
    name = ' '.join(part.capitalize() for part in name.split())
    
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    
    # Remove any remaining special characters
    name = re.sub(r'[^a-zA-Z0-9_]', '', name)
    
    return name if name else "Unknown_Name"


def tag_document(document_name, tag_name):
    """Add a tag to a document."""
    try:
        # Get or create the tag
        tag, _ = Tag.objects.get_or_create(name=tag_name)
        
        # Create document tag
        DocumentTag.objects.get_or_create(
            document_path=document_name,
            tag=tag
        )
        logger.info(f"Added tag '{tag_name}' to document {document_name}")
        return True
    except Exception as e:
        logger.error(f"Error tagging document {document_name}: {str(e)}")
        return False

class AuditLogView(BaseViewSet,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """View for managing audit logs."""
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        """Get all audit logs, optionally filtered by days."""
        # Get all logs, regardless of tags
        queryset = AuditLog.objects.all().order_by('-timestamp')
        
        # Filter by days if specified
        days = self.request.query_params.get('days', None)
        if days is not None:
            try:
                days = int(days)
                cutoff = timezone.now() - timezone.timedelta(days=days)
                queryset = queryset.filter(timestamp__gte=cutoff)
            except ValueError:
                pass
        
        return queryset

class RegisterView(viewsets.ModelViewSet):
    """ViewSet for user registration"""
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    queryset = get_user_model().objects.all()

    def get_template_names(self):
        if self.action == 'list':
            return ['user_management/register.html']
        return []

    def list(self, request, *args, **kwargs):
        return render(request, self.get_template_names()[0])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=400)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing audit logs."""
    queryset = SystemLog.objects.all().order_by('-timestamp')
    serializer_class = SystemLogSerializer
    authentication_classes = []  # No authentication required
    permission_classes = []      # No permissions required
    
    def list(self, request):
        """List audit logs with optional filtering."""
        try:
            # Get query parameters
            level = request.query_params.get('level', None)
            search = request.query_params.get('search', None)
            
            # Start with all logs
            logs = self.queryset
            
            # Apply filters
            if level:
                logs = logs.filter(level=level)
            if search:
                logs = logs.filter(message__icontains=search)
            
            # Paginate results
            page = self.paginate_queryset(logs)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(logs, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=500)

class LogAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing log alerts"""
    queryset = LogAlert.objects.all().order_by('-triggered_at')
    serializer_class = LogAlertSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by acknowledgement status
        acknowledged = self.request.query_params.get('acknowledged')
        if acknowledged is not None:
            queryset = queryset.filter(acknowledged=acknowledged.lower() == 'true')

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(triggered_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(triggered_at__lte=end_date)

        return queryset

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert"""
        alert = self.get_object()
        alert.acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        return Response({'status': 'alert acknowledged'})


class LogAggregationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing aggregated logs"""
    serializer_class = LogAggregationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        queryset = LogAggregation.objects.all()
        
        # Filter by period
        period = self.request.query_params.get('period', None)
        if period:
            queryset = queryset.filter(period=period)

        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        # Filter by level
        level = self.request.query_params.get('level', None)
        if level:
            queryset = queryset.filter(level=level)

        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__lte=end_date)

        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get a summary of aggregated logs"""
        period = request.query_params.get('period', 'DAY')
        days = int(request.query_params.get('days', 7))
        
        end_time = timezone.now()
        start_time = end_time - timezone.timedelta(days=days)
        
        # Get aggregated data
        aggregations = LogAggregation.objects.filter(
            period=period,
            start_time__gte=start_time,
            end_time__lte=end_time
        )

        # Calculate statistics
        total_logs = sum(agg.count for agg in aggregations)
        total_errors = sum(agg.error_count for agg in aggregations)
        total_warnings = sum(agg.warning_count for agg in aggregations)
        
        # Get trend data
        trend_data = aggregations.values('start_time').annotate(
            total=Sum('count'),
            errors=Sum('error_count'),
            warnings=Sum('warning_count')
        ).order_by('start_time')

        # Get top categories
        top_categories = aggregations.values('category').annotate(
            total=Sum('count')
        ).order_by('-total')[:5]

        return Response({
            'total_logs': total_logs,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'error_rate': (total_errors / total_logs * 100) if total_logs > 0 else 0,
            'warning_rate': (total_warnings / total_logs * 100) if total_logs > 0 else 0,
            'trend_data': trend_data,
            'top_categories': top_categories
        })

class LogCorrelationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing log correlations"""
    queryset = LogCorrelation.objects.all().order_by('-created_at')
    serializer_class = LogCorrelationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by correlation type
        correlation_type = self.request.query_params.get('correlation_type')
        if correlation_type:
            queryset = queryset.filter(correlation_type=correlation_type)

        # Filter by confidence score
        min_confidence = self.request.query_params.get('min_confidence')
        if min_confidence:
            queryset = queryset.filter(confidence_score__gte=float(min_confidence))

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset

class LogPatternViewSet(viewsets.ModelViewSet):
    """ViewSet for managing log patterns"""
    serializer_class = LogPatternSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        return LogPattern.objects.all()

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply a log pattern to logs"""
        pattern = self.get_object()
        # Get logs that match the pattern
        matching_logs = SystemLog.objects.filter(message__icontains=pattern.pattern)
        # Update logs with pattern info
        matching_logs.update(pattern=pattern)
        return Response({
            'status': 'pattern applied',
            'matched_logs': matching_logs.count()
        })

    @action(detail=False, methods=['post'])
    def discover(self, request):
        """Discover new log patterns"""
        logs = SystemLog.objects.filter(pattern__isnull=True)
        # TODO: Implement pattern discovery logic
        # This would involve analyzing log messages to find common patterns
        return Response({
            'status': 'pattern discovery initiated',
            'logs_analyzed': logs.count()
        })

class ScanScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing scan schedules"""
    serializer_class = ScanScheduleSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]
    
    logger = logging.getLogger('user_management')

    def get_queryset(self):
        queryset = ScanSchedule.objects.all()
        
        # Filter by user if not admin
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
            
        # Filter by enabled status
        enabled = self.request.query_params.get('enabled')
        if enabled is not None:
            queryset = queryset.filter(enabled=enabled.lower() == 'true')
            
        # Filter by schedule type
        schedule_type = self.request.query_params.get('type')
        if schedule_type:
            queryset = queryset.filter(type=schedule_type)
            
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        """Set the user when creating a new schedule"""
        try:
            self.logger.debug(f"Creating new scan schedule with data: {self.request.data}")
            
            # Check for overlapping schedules
            new_time = serializer.validated_data.get('time')
            new_type = serializer.validated_data.get('type')
            new_days = serializer.validated_data.get('selected_days', [])
            new_date = serializer.validated_data.get('monthly_date')
            
            existing_schedules = ScanSchedule.objects.filter(
                user=self.request.user,
                enabled=True,
                time=new_time
            )
            
            # Check for overlapping schedules based on type
            if new_type == 'daily':
                if existing_schedules.filter(type='daily').exists():
                    raise ValidationError("A daily schedule already exists at this time")
                    
            elif new_type == 'weekly':
                overlapping = existing_schedules.filter(
                    type='weekly'
                ).annotate(
                    days_overlap=models.Func(
                        models.F('selected_days'),
                        Value(new_days),
                        function='jsonb_array_overlap'
                    )
                ).filter(days_overlap=True)
                
                if overlapping.exists():
                    raise ValidationError("A weekly schedule already exists for some of these days at this time")
                    
            elif new_type == 'monthly' and new_date:
                if existing_schedules.filter(type='monthly', monthly_date=new_date).exists():
                    raise ValidationError("A monthly schedule already exists for this date at this time")
            
            serializer.save(user=self.request.user)
            self.logger.debug("Successfully created scan schedule")
            
        except ValidationError as e:
            self.logger.error(f"Validation error creating scan schedule: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to create scan schedule: {str(e)}")
            raise

    def create(self, request, *args, **kwargs):
        """Override create to add detailed error logging"""
        try:
            self.logger.debug(f"Received create request with data: {request.data}")
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                self.logger.error(f"Validation failed: {serializer.errors}")
                return Response({"error": "Failed to create schedule", "details": serializer.errors}, status=400)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=201, headers=headers)
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            self.logger.error(f"Unexpected error in create: {str(e)}")
            return Response({"error": "Failed to create schedule", "details": str(e)}, status=500)

    def list(self, request, *args, **kwargs):
        """Override list method to return schedules directly"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve method to return single schedule in consistent format"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """Enable a scan schedule"""
        schedule = self.get_object()
        schedule.enabled = True
        schedule.save()
        return Response({'status': 'schedule enabled'})

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """Disable a scan schedule"""
        schedule = self.get_object()
        schedule.enabled = False
        schedule.save()
        return Response({'status': 'schedule disabled'})

class LoginView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication needed for login
    parser_classes = [JSONParser]  # Add explicit JSON parser
    
    def post(self, request):
        try:
            logger.info("Login attempt received")
            username = request.data.get('username')
            password = request.data.get('password')
            
            logger.info(f"Login attempt for user: {username}")
            
            if not username or not password:
                return Response({'error': 'Please provide both username and password'},
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Check if account is locked
            try:
                user = CustomUser.objects.get(username=username)
                logger.info(f"Found user: {username}")
                if user.locked_until and user.locked_until > timezone.now():
                    minutes_remaining = int((user.locked_until - timezone.now()).total_seconds() / 60)
                    return Response({
                        'error': f'Account is locked. Try again in {minutes_remaining} minutes.'
                    }, status=status.HTTP_403_FORBIDDEN)
            except CustomUser.DoesNotExist:
                logger.warning(f"User not found: {username}")
                pass  # Don't reveal that the user doesn't exist
            
            user = authenticate(username=username, password=password)
            
            if not user:
                logger.warning(f"Authentication failed for user: {username}")
                return Response({'error': 'Invalid credentials'},
                              status=status.HTTP_401_UNAUTHORIZED)
            
            logger.info(f"User authenticated successfully: {username}")
            
            # Check if password change is required
            if user.require_password_change:
                return Response({
                    'error': 'Password change required',
                    'code': 'password_change_required'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Create or rotate API key
            token, created = Token.objects.get_or_create(user=user)
            if not created:
                # Check if token has expired
                token_age = timezone.now() - token.created
                if token_age.total_seconds() > getattr(settings, 'TOKEN_EXPIRED_AFTER_SECONDS', 86400):
                    # Delete old token and create new one
                    token.delete()
                    token = Token.objects.create(user=user)
            
            # Update last login
            user.last_login = timezone.now()
            user.save()
            
            logger.info(f"Login successful for user: {username}")
            return Response({
                'token': token.key,
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff,
                    'require_password_change': user.require_password_change
                }
            })
        except Exception as e:
            logger.error(f"Error in login view: {str(e)}", exc_info=True)
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            'error': 'Please provide both username and password'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user is not None:
        if user.is_active:
            login(request, user)
            
            # Get or create token
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            })
        else:
            return Response({
                'error': 'This account is not active.'
            }, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=401)
        
    stats = {
        'totalUsers': CustomUser.objects.count(),
        'activeComputers': Computer.objects.filter(is_online=True).count(),
        'totalDocuments': DocumentTag.objects.values('document_path', 'computer').distinct().count(),
        'recentScans': FileTransfer.objects.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(days=1)
        ).count(),
    }
    
    recent_logs = AuditLog.objects.order_by('-timestamp')[:5].values('message', 'timestamp')
    
    return Response({
        'stats': stats,
        'recent_logs': recent_logs
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users(request):
    """Get list of users"""
    users = get_user_model().objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

class ChangePasswordView(APIView):
    """View for changing user password"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'error': 'Invalid old password'}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({'status': 'password changed'})

class LogViewSet(BaseViewSet):
    permission_classes = [AllowAny]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def list(self, request):
        """List all logs"""
        logs = SystemLog.objects.all().order_by('-timestamp')[:100]  # Get latest 100 logs
        serializer = SystemLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics for logs and alerts"""
        # Get counts for different alert types
        warning_count = SystemLog.objects.filter(level='WARNING').count()
        critical_count = SystemLog.objects.filter(level='CRITICAL').count()
        pending_count = SystemLog.objects.filter(status='PENDING').count()
        overdue_count = SystemLog.objects.filter(status='OVERDUE').count()

        # Get activity data for the last 7 days
        today = timezone.now()
        seven_days_ago = today - timezone.timedelta(days=7)
        activity_data = []

        for i in range(7):
            date = seven_days_ago + timezone.timedelta(days=i)
            next_date = date + timezone.timedelta(days=1)
            
            day_data = {
                'date': date.strftime('%Y-%m-%d'),
                'opened': SystemLog.objects.filter(
                    timestamp__gte=date,
                    timestamp__lt=next_date,
                    status='OPEN'
                ).count(),
                'resolved': SystemLog.objects.filter(
                    timestamp__gte=date,
                    timestamp__lt=next_date,
                    status='RESOLVED'
                ).count()
            }
            activity_data.append(day_data)

        # Get computer status
        total_computers = Computer.objects.count()
        up_to_date_computers = Computer.objects.filter(is_online=True).count()

        summary_data = {
            'total_logs': SystemLog.objects.count(),
            'warning_count': warning_count,
            'critical_count': critical_count,
            'pending_count': pending_count,
            'overdue_count': overdue_count,
            'activity_data': activity_data,
            'computer_status': {
                'up_to_date': up_to_date_computers,
                'total': total_computers
            }
        }

        return Response(summary_data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    """Get admin dashboard statistics"""
    User = get_user_model()
    
    # Get total users count
    total_users = User.objects.count()
    
    # Get active users (not deactivated or deleted)
    active_users = User.objects.filter(is_active=True).count()
    
    # Get users created in last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    # Get user role distribution
    user_roles = User.objects.values('role').annotate(count=Count('id'))
    role_counts = {role['role']: role['count'] for role in user_roles}
    
    # Get verified vs unverified users
    verified_users = User.objects.filter(is_verified=True).count()
    
    stats = {
        'totalUsers': total_users,
        'activeUsers': active_users,
        'newUsers30Days': new_users,
        'verifiedUsers': verified_users,
        'roleDistribution': role_counts,
        'staffUsers': User.objects.filter(is_staff=True).count(),
        'superUsers': User.objects.filter(is_superuser=True).count(),
        'lockedUsers': User.objects.filter(locked_until__gt=timezone.now()).count()
    }
    
    return Response(stats)