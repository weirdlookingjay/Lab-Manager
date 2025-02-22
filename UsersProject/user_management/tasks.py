from django.utils import timezone
from celery import shared_task
from .models import Computer, AuditLog, LogAggregation
import pandas as pd
import os
from django.conf import settings
from datetime import datetime
import logging
import shutil
from .utils.pdf_processor import process_onet_pdf, is_onet_profile
from UsersProject.celery import app
from rest_framework.parsers import JSONParser

logger = logging.getLogger(__name__)

def log_message(message, level='INFO'):
    """Write log message to database and print it."""
    AuditLog.objects.create(message=message, level=level)
    print(f"[{timezone.now()}] {level}: {message}")

def process_computer(computer_ip, computer_label):
    """Process a single computer's file operations."""
    from .views import FileOperationsView
    try:
        file_ops = FileOperationsView()
        file_ops.copy_files(computer_ip, computer_label)
        return True
    except Exception as e:
        log_message(f"Error processing computer {computer_label} ({computer_ip}): {str(e)}", 'ERROR')
        return False

def run_file_operations():
    """Main function to read CSV and process each computer."""
    try:
        csv_file = os.path.join(settings.BASE_DIR, settings.CSV_FILE)
        if not os.path.exists(csv_file):
            log_message(f"CSV file not found: {csv_file}", 'ERROR')
            return

        df = pd.read_csv(csv_file)
        for _, row in df.iterrows():
            computer_ip = row.get('IP')
            computer_label = row.get('Label')
            
            if not computer_ip or not computer_label:
                continue

            # Create or update computer record
            computer, created = Computer.objects.get_or_create(
                ip_address=computer_ip,
                defaults={'label': computer_label}
            )

            # Queue the file operation task
            process_computer.delay(computer_ip, computer_label)

        log_message("File operations scheduled for all computers")
        
        # Process O*NET PDFs
        source_dir = settings.SOURCE_DIR
        backup_dir = settings.BACKUP_DIR
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # Get current date for folder structure
        current_date = datetime.now()
        year_month = current_date.strftime('%Y-%m')
        
        # Create year-month folder if it doesn't exist
        backup_month_dir = os.path.join(backup_dir, year_month)
        if not os.path.exists(backup_month_dir):
            os.makedirs(backup_month_dir)
            
        # Process files in source directory
        for filename in os.listdir(source_dir):
            if filename.lower().endswith('.pdf'):
                source_path = os.path.join(source_dir, filename)
                
                # Check if it's an O*NET profile and process it
                if is_onet_profile(source_path):
                    success, result = process_onet_pdf(source_path)
                    if success:
                        logger.info(f"Processed O*NET PDF: {result}")
                    else:
                        logger.warning(f"Failed to process O*NET PDF: {result}")
                
                # Move to backup directory
                backup_path = os.path.join(backup_month_dir, filename)
                counter = 1
                
                # Handle duplicate filenames
                while os.path.exists(backup_path):
                    name, ext = os.path.splitext(filename)
                    new_filename = f"{name}_{counter}{ext}"
                    backup_path = os.path.join(backup_month_dir, new_filename)
                    counter += 1
                
                # Copy file to backup location
                shutil.copy2(source_path, backup_path)
                logger.info(f"Backed up file: {filename} to {backup_path}")
                
                # Remove original file
                os.remove(source_path)
                logger.info(f"Removed original file: {source_path}")
                
        return True, "File operations completed successfully"
        
    except Exception as e:
        error_message = f"Error in file operations: {str(e)}"
        logger.error(error_message)
        return False, error_message

def aggregate_system_logs(period='DAY'):
    """
    Task to aggregate system logs for analysis.
    Aggregates logs for the last period and stores statistics.
    """
    from .models import LogAggregation
    
    try:
        # Calculate time range based on period
        end_time = timezone.now()
        if period == 'HOUR':
            start_time = end_time - timezone.timedelta(hours=1)
        elif period == 'DAY':
            start_time = end_time - timezone.timedelta(days=1)
        elif period == 'WEEK':
            start_time = end_time - timezone.timedelta(weeks=1)
        else:  # MONTH
            start_time = end_time - timezone.timedelta(days=30)

        # Perform aggregation
        LogAggregation.aggregate_logs(period=period, start_time=start_time, end_time=end_time)
        
        log_message(f"Successfully aggregated logs for period: {period}", 'INFO')
    except Exception as e:
        log_message(f"Error aggregating logs: {str(e)}", 'ERROR')

@app.task(name='user_management.tasks.analyze_logs')
def analyze_logs():
    """Background task to analyze logs and generate alerts"""
    from .services.log_analysis import LogAnalysisService
    LogAnalysisService.analyze_logs()

@app.task(name='user_management.tasks.check_and_run_scheduled_scans')
def check_and_run_scheduled_scans():
    """Check for and execute any scheduled scans that are due"""
    # Use the scan_operations logger for all scan-related logging
    scan_logger = logging.getLogger('scan_operations')
    scan_logger.info("Starting scheduled scan check...")
    try:
        from user_management.models import ScanSchedule
        from django.utils import timezone
        import time
        
        now = timezone.localtime()
        scan_logger.info(f"Current time (local): {now}")
        
        # Get all enabled schedules
        all_schedules = ScanSchedule.objects.filter(enabled=True)
        scan_logger.info(f"Found {all_schedules.count()} enabled schedules")
        
        for schedule in all_schedules:
            # Convert next_run to local time for comparison
            next_run_local = timezone.localtime(schedule.next_run) if schedule.next_run else None
            scan_logger.info(f"Schedule {schedule.id}: time={schedule.time}, next_run={schedule.next_run} (UTC), {next_run_local} (local)")
            
            # Check if schedule is due
            if next_run_local and next_run_local <= now:
                scan_logger.info(f"Schedule {schedule.id} is due for execution")
                try:
                    computer_ids = list(schedule.computers.values_list('id', flat=True))
                    if not computer_ids:
                        scan_logger.warning(f"Schedule {schedule.id} has no computers associated")
                        continue
                    
                    scan_logger.info(f"Found {len(computer_ids)} computers to scan: {computer_ids}")
                    
                    # Start the scan directly using ScanViewSet
                    from user_management.views import ScanViewSet
                    from rest_framework.test import APIRequestFactory, force_authenticate
                    from rest_framework.request import Request
                    from django.contrib.auth import get_user_model
                    
                    # Create the viewset and initialize required attributes
                    scan_viewset = ScanViewSet()
                    scan_viewset.format_kwarg = None
                    scan_viewset.action_map = {'post': 'start'}  # Map POST to 'start' action
                    scan_viewset.action = 'start'  # Set the action to 'start'
                    scan_viewset.detail = False
                    scan_viewset.basename = 'scan'
                    
                    # Set the logger to use for scan operations
                    scan_viewset.logger = scan_logger
                    
                    # Create a mock request with the computers data
                    factory = APIRequestFactory()
                    wsgi_request = factory.post('/api/scan/start/', {'computers': computer_ids},
                                             format='json')
                    
                    # Get a superuser to authenticate the request
                    User = get_user_model()
                    admin_user = User.objects.filter(is_superuser=True).first()
                    if not admin_user:
                        scan_logger.error("No superuser found to authenticate scheduled scan")
                        continue

                    # Properly authenticate the request
                    force_authenticate(wsgi_request, user=admin_user)
                    
                    # Create DRF Request object with proper wsgi setup
                    wsgi_request.META['CONTENT_TYPE'] = 'application/json'
                    wsgi_request.META['HTTP_ACCEPT'] = 'application/json'
                    request = Request(wsgi_request)
                    request.user = admin_user
                    request.method = 'POST'
                    request.parsers = [JSONParser()]
                    
                    # Set up request data properly
                    computers_data = {'computers': [str(computer.id) for computer in schedule.computers.all()]}
                    request._data = computers_data
                    request._full_data = computers_data  # DRF uses _full_data internally
                    
                    # Execute the scan
                    scan_logger.info(f"Started scan for schedule {schedule.id}")
                    response = scan_viewset.start(request)
                    
                    if response.status_code == 200:
                        scan_logger.info(f"Scan completed successfully. {response.data.get('message', '')}")
                    else:
                        scan_logger.error(f"Scan failed with status {response.status_code}: {response.data}")
                    
                    # Wait for scan to complete
                    max_wait = 300  # 5 minutes max wait
                    wait_time = 0
                    scan_complete = False
                    scan_success = False
                    
                    while wait_time < max_wait:
                        if not scan_viewset._scan_in_progress:
                            scan_complete = True
                            stats = scan_viewset._current_scan_stats
                            
                            # Check if scan was successful
                            failed_computers = stats.get('failed_computers', [])
                            total_computers = stats.get('total_computers', 0)
                            computers_scanned = stats.get('computers_scanned', 0)
                            
                            if not failed_computers and computers_scanned == total_computers:
                                scan_success = True
                                scan_logger.info(f"Scan completed successfully. Processed {computers_scanned} computers.")
                            else:
                                scan_logger.error(f"Scan completed with issues. Failed computers: {failed_computers}")
                                scan_logger.error(f"Computers scanned: {computers_scanned}/{total_computers}")
                            break
                            
                        time.sleep(5)
                        wait_time += 5
                        scan_logger.info(f"Waiting for scan to complete... ({wait_time}s)")
                    
                    if not scan_complete:
                        scan_logger.error(f"Scan timeout after {max_wait} seconds")
                    elif scan_success:
                        # Only update schedule if scan was successful
                        schedule.last_run = now
                        schedule.next_run = schedule.calculate_next_run()
                        schedule.save()
                        scan_logger.info(f"Updated schedule {schedule.id} next_run to {schedule.next_run} (UTC), {timezone.localtime(schedule.next_run)} (local)")
                    else:
                        scan_logger.error("Scan completed but had failures. Not updating schedule.")
                    
                except Exception as e:
                    scan_logger.error(f"Error processing schedule {schedule.id}: {str(e)}", exc_info=True)
            else:
                scan_logger.info(f"Schedule {schedule.id} is not due yet. Current: {now}, Next run: {next_run_local}")
                
    except Exception as e:
        scan_logger.error(f"Error checking scheduled scans: {str(e)}", exc_info=True)

def schedule_file_operations(hour: int, minute: int, name: str = "daily_backup"):
    """Schedule file operations to run at a specific time."""
    try:
        # Create new schedule
        run_file_operations.apply_async(eta=datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0))
        
        log_message(f"Scheduled file operations for {hour:02d}:{minute:02d} daily")
        return True
    except Exception as e:
        log_message(f"Error scheduling file operations: {str(e)}", 'ERROR')
        return False
