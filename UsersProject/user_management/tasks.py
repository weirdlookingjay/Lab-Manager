from __future__ import absolute_import, unicode_literals
import os
import sys
import json
import logging
import asyncio
import websockets
from datetime import datetime
from celery import shared_task
from django.utils import timezone
from asgiref.sync import sync_to_async
from .models import Computer, AuditLog, LogAggregation, SystemLog
import pandas as pd
from UsersProject.celery import app
from pathlib import Path
from django.conf import settings
import shutil
from .utils.pdf_processor import process_onet_pdf, is_onet_profile
from rest_framework.parsers import JSONParser
from django.db import transaction
import subprocess
from typing import Dict, Any

# Configure logger
logger = logging.getLogger('user_management')

def log_message(message, level='INFO'):
    """Write log message to database and print it."""
    # Get the logger
    logger = logging.getLogger('user_management')
    
    # Log based on level
    if level == 'ERROR':
        logger.error(message)
    elif level == 'WARNING':
        logger.warning(message)
    else:
        logger.info(message)
    
    # Also create log entry in database
    try:
        AuditLog.objects.create(message=message, level=level)
    except Exception as e:
        logger.error(f"Failed to create audit log entry: {str(e)}")

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
                        logging.info(f"Processed O*NET PDF: {result}")
                    else:
                        logging.warning(f"Failed to process O*NET PDF: {result}")
                
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
                logging.info(f"Backed up file: {filename} to {backup_path}")
                
                # Remove original file
                os.remove(source_path)
                logging.info(f"Removed original file: {source_path}")
                
        return True, "File operations completed successfully"
        
    except Exception as e:
        error_message = f"Error in file operations: {str(e)}"
        logging.error(error_message)
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

@app.task(
    name='user_management.tasks.check_and_run_scheduled_scans',
    bind=True,
    max_retries=3,
    time_limit=300,
    soft_time_limit=240,
    acks_late=True,
    reject_on_worker_lost=True,
    task_track_started=True
)
def check_and_run_scheduled_scans(self):
    """Check for and execute any scheduled scans that are due"""
    scan_logger = logging.getLogger('scan_operations')
    scan_logger.info("Starting scheduled scan check...")
    try:
        from user_management.models import ScanSchedule
        from django.utils import timezone
        import time
        import pytz
        from django.db.utils import OperationalError
        
        now_utc = timezone.now()
        est = pytz.timezone('America/New_York')
        now_est = now_utc.astimezone(est)
        
        scan_logger.info(f"Current time - UTC: {now_utc}, EST: {now_est}")
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                with transaction.atomic():
                    all_schedules = (ScanSchedule.objects
                        .select_for_update(nowait=True)
                        .filter(enabled=True)
                        .filter(next_run__lte=now_utc)
                    )
                    scan_logger.info(f"Found {all_schedules.count()} due schedules")
                    
                    for schedule in all_schedules:
                        next_run_utc = schedule.next_run
                        next_run_est = next_run_utc.astimezone(est) if next_run_utc else None
                        
                        scan_logger.info(
                            f"Processing schedule {schedule.id}: time={schedule.time}, "
                            f"next_run UTC={next_run_utc}, EST={next_run_est}"
                        )
                        
                        try:
                            with transaction.atomic():
                                schedule.refresh_from_db()
                                
                                success = start_scan_for_schedule(schedule)
                                
                                if success:
                                    schedule.next_run = schedule.calculate_next_run()
                                    schedule.last_run = now_utc
                                    schedule.last_status = 'success'
                                    schedule.save()
                                    scan_logger.info(f"Updated next run time to {schedule.next_run}")
                                else:
                                    schedule.last_status = 'failed'
                                    schedule.save()
                                    scan_logger.error("Scan failed. Schedule updated with failure status.")
                                    
                        except Exception as e:
                            scan_logger.error(f"Error processing schedule {schedule.id}: {str(e)}", exc_info=True)
                            schedule.last_status = 'error'
                            schedule.save()
                            continue
                            
                break  # Exit retry loop if successful
                    
            except OperationalError as e:
                if attempt < max_retries - 1:
                    scan_logger.warning(f"Database lock conflict, attempt {attempt + 1} of {max_retries}")
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    scan_logger.error("Failed to acquire database lock after max retries")
                    raise
                    
    except Exception as e:
        scan_logger.error(f"Error checking scheduled scans: {str(e)}", exc_info=True)
        raise

def start_scan_for_schedule(schedule):
    """Start a scan for the given schedule."""
    scan_logger = logging.getLogger('scan_operations')
    try:
        computer_ids = list(schedule.computers.values_list('id', flat=True))
        if not computer_ids:
            scan_logger.warning(f"Schedule {schedule.id} has no computers associated")
            return False
            
        scan_logger.info(f"Found {len(computer_ids)} computers to scan: {computer_ids}")
        
        from user_management.views_scan import ScanViewSet
        from rest_framework.test import APIRequestFactory, force_authenticate
        from rest_framework.request import Request
        from django.contrib.auth import get_user_model
        from rest_framework.parsers import JSONParser
        
        scan_viewset = ScanViewSet()
        scan_viewset.format_kwarg = None
        scan_viewset.action_map = {'post': 'start'}
        scan_viewset.action = 'start'
        scan_viewset.detail = False
        scan_viewset.basename = 'scan'
        scan_viewset.logger = scan_logger
        
        factory = APIRequestFactory()
        wsgi_request = factory.post('/api/scan/start/', {'computers': computer_ids}, format='json')
        
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            scan_logger.error("No superuser found to authenticate scheduled scan")
            return False

        force_authenticate(wsgi_request, user=admin_user)
        wsgi_request.META['CONTENT_TYPE'] = 'application/json'
        wsgi_request.META['HTTP_ACCEPT'] = 'application/json'
        request = Request(wsgi_request)
        request.user = admin_user
        request.method = 'POST'
        request.parsers = [JSONParser()]
        
        computers_data = {'computers': [str(computer.id) for computer in schedule.computers.all()]}
        request._data = computers_data
        request._full_data = computers_data
        
        scan_logger.info(f"Starting scan for schedule {schedule.id}")
        response = scan_viewset.start(request)
        
        if response.status_code != 200:
            scan_logger.error(f"Scan failed with status {response.status_code}: {response.data}")
            return False
            
        scan_logger.info(f"Scan initiated successfully. {response.data.get('message', '')}")
        
        max_wait = 240
        check_interval = 5
        wait_time = 0
        
        while wait_time < max_wait:
            if not scan_viewset._scan_in_progress:
                stats = scan_viewset._current_scan_stats
                failed_computers = stats.get('failed_computers', [])
                total_computers = stats.get('total_computers', 0)
                computers_scanned = stats.get('computers_scanned', 0)
                
                if not failed_computers and computers_scanned == total_computers:
                    scan_logger.info(f"Scan completed successfully. Processed {computers_scanned} computers.")
                    return True
                else:
                    scan_logger.error(
                        f"Scan completed with issues. Failed computers: {failed_computers}. "
                        f"Computers scanned: {computers_scanned}/{total_computers}"
                    )
                    return False
                    
            time.sleep(check_interval)
            wait_time += check_interval
            
            if wait_time % 30 == 0:
                scan_logger.info(f"Scan in progress... Time elapsed: {wait_time}s")
        
        scan_logger.error(f"Scan timeout after {max_wait} seconds")
        return False
        
    except Exception as e:
        scan_logger.error(f"Error in scan execution: {str(e)}", exc_info=True)
        return False

def schedule_file_operations(hour: int, minute: int, name: str = "daily_backup"):
    """Schedule file operations to run at a specific time."""
    try:
        run_file_operations.apply_async(eta=datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0))
        
        log_message(f"Scheduled file operations for {hour:02d}:{minute:02d} daily")
        return True
    except Exception as e:
        log_message(f"Error scheduling file operations: {str(e)}", 'ERROR')
        return False

async def handle_message(message_str: str) -> None:
    """Handle incoming message from relay server."""
    try:
        # Parse message
        message = json.loads(message_str)
        message_type = message.get('type')
        
        if not message_type:
            logger.warning(f"Message missing type field: {message}")
            return
            
        # Handle different message types
        if message_type == 'metrics':
            await handle_metrics_message(message.get('data', {}))
        else:
            logger.warning(f"Unknown message type: {message_type}")
            
    except json.JSONDecodeError:
        logger.error(f"Failed to parse message as JSON: {message_str}")
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        logger.error(f"Message: {message_str}")
        logger.error(traceback.format_exc())

async def handle_metrics_message(message: Dict[str, Any]) -> None:
    """Handle incoming metrics message from relay server."""
    try:
        # Extract basic info
        hostname = message.get('hostname')
        ip_address = message.get('ip_address')
        
        if not hostname or not ip_address:
            logger.warning(f"Missing required fields in metrics message: {message}")
            return
            
        # Log raw metrics for debugging
        logger.debug(f"Raw metrics data for {hostname}: {json.dumps(message, indent=2)}")
        
        # Get or create computer
        computer = await sync_to_async(Computer.objects.get_or_create)(
            hostname=hostname,
            defaults={'ip_address': ip_address}
        )[0]
        
        # Update IP if changed
        if computer.ip_address != ip_address:
            computer.ip_address = ip_address
        
        # Update last seen
        computer.last_seen = timezone.now()
        
        # Transform metrics
        metrics = {
            'hostname': hostname,
            'ip_address': ip_address,
            'logged_in_user': message.get('logged_in_user'),
            'cpu': message.get('cpu', {}),
            'memory': message.get('memory', {}),
            'disk': message.get('disk', {}),
            'system': message.get('system', {}),
            'status': 'online',
            'last_seen': computer.last_seen.isoformat(),
            'last_metrics_update': computer.last_seen.isoformat()
        }
        
        # Log transformed metrics
        logger.debug(f"Saving transformed metrics for {hostname}: {json.dumps(metrics, indent=2)}")
        
        # Log current metrics for comparison
        logger.debug(f"Current computer metrics for {hostname}: {json.dumps(computer.metrics, indent=2) if computer.metrics else 'None'}")
        
        # Update computer metrics
        await sync_to_async(computer.update_metrics)(metrics)
        
        # Log updated metrics
        logger.debug(f"Updated computer metrics for {hostname}: {json.dumps(metrics, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error handling metrics message: {str(e)}")
        logger.error(f"Message: {message}")
        logger.error(traceback.format_exc())

async def run_client(relay_url: str, token: str) -> None:
    """Run the WebSocket relay client."""
    try:
        logger.info(f"Attempting to connect to {relay_url}")
        
        async with websockets.connect(relay_url) as websocket:
            logger.info("Connected to relay server")
            
            # Send authentication
            auth_message = json.dumps({
                "type": "auth",
                "token": token
            })
            await websocket.send(auth_message)
            logger.info("Sent authentication message")
            
            # Wait for auth response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('type') != 'auth_success':
                logger.error("Authentication failed")
                return
                
            logger.info("Authentication successful")
            
            # Main message loop
            while True:
                try:
                    message = await websocket.recv()
                    await handle_message(message)
                except websockets.exceptions.ConnectionClosed:
                    logger.error("Connection closed unexpectedly")
                    break
                except Exception as e:
                    logger.error(f"Error in message loop: {str(e)}")
                    logger.error(traceback.format_exc())
                    continue
                    
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"WebSocket error: {str(e)}")
    except Exception as e:
        logger.error(f"Error running client: {str(e)}")
        logger.error(traceback.format_exc())

@app.task
def ensure_relay_client_running():
    """Ensure the relay client is running."""
    try:
        # Get relay URL and token from environment
        relay_url = os.getenv('RELAY_URL', 'ws://192.168.72.19:8765')
        token = os.getenv('TOKEN', 'default_token')
        
        if not relay_url or not token:
            logger.error("Missing RELAY_URL or TOKEN environment variables")
            return
            
        logger.info(f"Environment loaded - RELAY_URL: {relay_url}, TOKEN: {'set' if token else 'not set'}")
        
        # Set up event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        logger.debug(f"Using proactor: {loop._proactor.__class__.__name__}")
        logger.info("Created new event loop")
        
        # Run the client
        loop.run_until_complete(run_client(relay_url, token))
        
    except Exception as e:
        logger.error(f"Error ensuring relay client is running: {str(e)}")
        logger.error(traceback.format_exc())

@app.task
def run_relay_client():
    """Run the WebSocket relay client as a Celery task."""
    try:
        # Configure logging
        logger = logging.getLogger('user_management')
        logger.info("Logger configured successfully")

        # Load environment variables
        relay_url = os.getenv("RELAY_URL", "ws://localhost:8765")
        token = os.getenv("DJANGO_TOKEN")
        if not token:
            raise ValueError("DJANGO_TOKEN environment variable not set")
        logger.info(f"Environment loaded - RELAY_URL: {relay_url}, TOKEN: set")

        # Create and configure event loop
        if sys.platform == 'win32':
            loop = asyncio.ProactorEventLoop()
            logger.debug("Using proactor: IocpProactor")
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info("Created new event loop")

        try:
            # Run the client in the event loop
            loop.run_until_complete(run_client(relay_url, token))
        except Exception as e:
            logger.error(f"Fatal error in relay client: {e}", exc_info=True)
            raise  # Re-raise to let Celery know the task failed
        finally:
            loop.close()
            logger.info("Event loop closed")

    except Exception as e:
        logger.error(f"Critical error in relay client task: {e}", exc_info=True)
        raise  # Re-raise to mark the task as failed

# Removed duplicate beat schedule here since it's already in settings.py

from django.core.cache import cache
from datetime import timedelta
from .services.computer_service import ComputerService

logger = logging.getLogger('user_management')
computer_service = ComputerService()

@app.task
def monitor_relay_server():
    async def connect_and_monitor():
        uri = "ws://192.168.72.19:8765"
        try:
            async with websockets.connect(uri) as websocket:
                # Register as monitor
                reg_message = {
                    "type": "register",
                    "client_type": "monitor",
                    "subscribe": ["metrics"]
                }
                
                await websocket.send(json.dumps(reg_message))
                response = await websocket.recv()
                logger.info("Connected to relay server")
                
                while True:
                    try:
                        # Get raw message
                        raw_message = await websocket.recv()
                        message = json.loads(raw_message)
                       
                        # Only process metrics for specific computer
                        if message.get('type') == 'update_metrics' and message.get('hostname') == '545D9X1':
                            # Log the full message content
                            logger.info(f"Processing metrics update: {json.dumps(message, indent=2)}")
                            
                            # Let service handle database update and logging
                            try:
                                computer_service.update_computer_from_metrics(
                                    hostname=message.get('hostname'),
                                    metrics_data=message
                                )
                                logger.info(f"Successfully updated computer metrics in database for {message.get('hostname')}")
                            except Exception as e:
                                logger.error(f"Failed to update computer metrics: {str(e)}", exc_info=True)
                    
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        
        except Exception as e:
            logger.error(f"Connection error: {e}", exc_info=True)

    asyncio.run(connect_and_monitor())