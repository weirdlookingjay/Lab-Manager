import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q
from django.db import transaction
from ..models import SystemLog, LogPattern, LogAlert, LogCorrelation

# Get both general and scan-specific loggers
logger = logging.getLogger(__name__)
scan_logger = logging.getLogger('scan_operations')

class LogAnalysisService:
    """Service for analyzing logs, detecting patterns, and generating alerts"""

    @staticmethod
    def analyze_logs():
        """Main method to analyze logs and generate alerts"""
        scan_logger.info("Starting log analysis for scan operations")
        LogAnalysisService._detect_patterns()
        LogAnalysisService._correlate_events()
        LogAnalysisService._cleanup_old_correlations()
        scan_logger.info("Completed log analysis for scan operations")

    @staticmethod
    def _detect_patterns():
        """Detect patterns in logs and generate alerts"""
        patterns = LogPattern.objects.filter(enabled=True)
        
        for pattern in patterns:
            # Skip if in cooldown period
            if pattern.last_triggered and timezone.now() < pattern.last_triggered + timedelta(minutes=pattern.cooldown_minutes):
                continue

            # Log scan-related pattern detection
            if pattern.category == 'FILE_SCAN':
                scan_logger.info(f"Analyzing pattern: {pattern.name}")

            matched_logs = []
            if pattern.pattern_type == 'SEQUENCE':
                matched_logs = LogAnalysisService._detect_sequence_pattern(pattern)
            elif pattern.pattern_type == 'THRESHOLD':
                matched_logs = LogAnalysisService._detect_threshold_pattern(pattern)
            elif pattern.pattern_type == 'CORRELATION':
                matched_logs = LogAnalysisService._detect_correlation_pattern(pattern)

            if matched_logs and len(matched_logs) >= pattern.alert_threshold:
                # Log scan-related alerts
                if pattern.category == 'FILE_SCAN':
                    scan_logger.warning(f"Pattern {pattern.name} matched {len(matched_logs)} logs")
                LogAnalysisService._create_alert(pattern, matched_logs)

    @staticmethod
    def _detect_sequence_pattern(pattern):
        """Detect sequence of events matching pattern conditions"""
        conditions = pattern.conditions
        if 'sequence' not in conditions:
            return []

        sequence = conditions['sequence']
        window_minutes = conditions.get('window_minutes', 60)
        start_time = timezone.now() - timedelta(minutes=window_minutes)

        # Get logs within time window
        logs = SystemLog.objects.filter(
            timestamp__gte=start_time
        ).order_by('timestamp')

        # Log scan-related sequence detection
        if pattern.category == 'FILE_SCAN':
            scan_logger.info(f"Analyzing sequence pattern over {window_minutes} minute window")

        # Find sequences matching the pattern
        matched_logs = []
        current_sequence = []
        sequence_index = 0

        for log in logs:
            if LogAnalysisService._log_matches_condition(log, sequence[sequence_index]):
                current_sequence.append(log)
                sequence_index += 1
                
                if sequence_index == len(sequence):
                    matched_logs.extend(current_sequence)
                    # Log scan-related sequence completion
                    if pattern.category == 'FILE_SCAN':
                        scan_logger.info(f"Found matching sequence of {len(sequence)} events")
                    current_sequence = []
                    sequence_index = 0
            else:
                current_sequence = []
                sequence_index = 0
                if LogAnalysisService._log_matches_condition(log, sequence[0]):
                    current_sequence.append(log)
                    sequence_index = 1

        return matched_logs

    @staticmethod
    def _detect_threshold_pattern(pattern):
        """Detect when log events exceed a threshold"""
        conditions = pattern.conditions
        if 'criteria' not in conditions or 'threshold' not in conditions:
            return []

        window_minutes = conditions.get('window_minutes', 60)
        start_time = timezone.now() - timedelta(minutes=window_minutes)

        # Log scan-related threshold detection
        if pattern.category == 'FILE_SCAN':
            scan_logger.info(f"Checking threshold pattern over {window_minutes} minute window")

        # Build query from criteria
        query = Q(timestamp__gte=start_time)
        for key, value in conditions['criteria'].items():
            query &= Q(**{key: value})

        logs = SystemLog.objects.filter(query)
        count = logs.count()
        
        # Log scan-related threshold results
        if pattern.category == 'FILE_SCAN':
            scan_logger.info(f"Found {count} matching events (threshold: {conditions['threshold']})")
        
        if count >= conditions['threshold']:
            return list(logs)
        return []

    @staticmethod
    def _detect_correlation_pattern(pattern):
        """Detect correlated events based on pattern conditions"""
        conditions = pattern.conditions
        if 'primary_criteria' not in conditions or 'related_criteria' not in conditions:
            return []

        window_minutes = conditions.get('window_minutes', 60)
        start_time = timezone.now() - timedelta(minutes=window_minutes)

        # Log scan-related correlation detection
        if pattern.category == 'FILE_SCAN':
            scan_logger.info(f"Analyzing correlation pattern over {window_minutes} minute window")

        # Find primary events
        primary_query = Q(timestamp__gte=start_time)
        for key, value in conditions['primary_criteria'].items():
            primary_query &= Q(**{key: value})
        
        primary_logs = SystemLog.objects.filter(primary_query)
        
        # For each primary event, find related events
        matched_logs = []
        for primary_log in primary_logs:
            related_query = Q(
                timestamp__gte=primary_log.timestamp,
                timestamp__lte=primary_log.timestamp + timedelta(minutes=conditions.get('correlation_window_minutes', 5))
            )
            for key, value in conditions['related_criteria'].items():
                related_query &= Q(**{key: value})
            
            related_logs = SystemLog.objects.filter(related_query)
            if related_logs.exists():
                matched_logs.append(primary_log)
                matched_logs.extend(related_logs)

        return matched_logs

    @staticmethod
    def _create_alert(pattern, matched_logs):
        """Create an alert for matched pattern"""
        with transaction.atomic():
            alert = LogAlert.objects.create(
                pattern=pattern,
                details={
                    'matched_count': len(matched_logs),
                    'first_match': matched_logs[0].timestamp.isoformat(),
                    'last_match': matched_logs[-1].timestamp.isoformat()
                }
            )
            alert.matched_logs.set(matched_logs)
            
            pattern.last_triggered = timezone.now()
            pattern.save()

            # Log scan-related alert creation
            if pattern.category == 'FILE_SCAN':
                scan_logger.warning(
                    f"Created alert for pattern '{pattern.name}' with {len(matched_logs)} correlated logs"
                )

    @staticmethod
    def _correlate_events():
        """Find and store correlated events"""
        # Look for events in the last hour
        start_time = timezone.now() - timedelta(hours=1)
        logs = SystemLog.objects.filter(timestamp__gte=start_time)

        # Group logs by computer and find related events
        computers = logs.values('computer').distinct()
        for computer in computers:
            computer_logs = logs.filter(computer=computer['computer']).order_by('timestamp')
            
            # Find authentication followed by file access patterns
            auth_logs = computer_logs.filter(category='AUTH')
            for auth_log in auth_logs:
                # Look for file access events within 5 minutes of auth
                file_logs = computer_logs.filter(
                    category='FILE_ACCESS',
                    timestamp__gt=auth_log.timestamp,
                    timestamp__lte=auth_log.timestamp + timedelta(minutes=5)
                )
                
                if file_logs.exists():
                    LogCorrelation.objects.create(
                        primary_log=auth_log,
                        correlation_type='AUTH_FILE_ACCESS',
                        confidence_score=0.8
                    ).related_logs.set(file_logs)

            # Find scan start/completion patterns
            scan_start_logs = computer_logs.filter(event='SCAN_STARTED')
            for start_log in scan_start_logs:
                # Look for scan completion within 30 minutes
                completion_logs = computer_logs.filter(
                    event='SCAN_COMPLETED',
                    timestamp__gt=start_log.timestamp,
                    timestamp__lte=start_log.timestamp + timedelta(minutes=30)
                )
                
                if completion_logs.exists():
                    LogCorrelation.objects.create(
                        primary_log=start_log,
                        correlation_type='SCAN_LIFECYCLE',
                        confidence_score=1.0
                    ).related_logs.set(completion_logs)

    @staticmethod
    def _cleanup_old_correlations():
        """Remove correlations older than 7 days"""
        cutoff = timezone.now() - timedelta(days=7)
        LogCorrelation.objects.filter(created_at__lt=cutoff).delete()

    @staticmethod
    def _log_matches_condition(log, condition):
        """Check if a log entry matches a condition"""
        for key, value in condition.items():
            if getattr(log, key, None) != value:
                return False
        return True
