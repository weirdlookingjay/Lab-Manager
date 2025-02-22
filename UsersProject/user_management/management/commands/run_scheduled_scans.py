from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from user_management.models import ScanSchedule
from user_management.views import ScanViewSet
from user_management.utils import notify_scan_started, notify_scan_completed, notify_scan_error
from django.core.mail import send_mail
import logging
import threading

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run scheduled scans that are due'
    
    def __init__(self):
        super().__init__()
        self.scan_lock = threading.Lock()
        self.max_concurrent_scans = 3  # Limit concurrent scans
        self.active_scans = 0
        self.scan_semaphore = threading.Semaphore(self.max_concurrent_scans)

    def handle(self, *args, **options):
        now = timezone.now()
        schedules = ScanSchedule.objects.filter(enabled=True, next_run__lte=now)
        
        if not schedules.exists():
            self.stdout.write('No scheduled scans are due')
            return

        scan_viewset = ScanViewSet()
        threads = []
        
        for schedule in schedules:
            try:
                self.stdout.write(f'Processing schedule: {schedule}')
                
                # Get computers for this schedule
                computer_ids = list(schedule.computers.values_list('id', flat=True))
                if not computer_ids:
                    self.stdout.write(self.style.WARNING(
                        f'Schedule {schedule.id} has no computers associated with it'
                    ))
                    continue

                # Create thread for this schedule
                thread = threading.Thread(
                    target=self._run_schedule_scan,
                    args=(scan_viewset, schedule, computer_ids)
                )
                threads.append(thread)
                thread.start()

            except Exception as e:
                error_msg = f'Error processing schedule {schedule.id}: {str(e)}'
                self.stdout.write(self.style.ERROR(error_msg))
                logger.error(error_msg)
                notify_scan_error(error_msg, user=schedule.user)

        # Wait for all scans to complete
        for thread in threads:
            thread.join()

    def _run_schedule_scan(self, scan_viewset, schedule, computer_ids):
        """Run a single schedule's scan with proper resource management"""
        # Acquire semaphore to limit concurrent scans
        with self.scan_semaphore:
            try:
                # Try to acquire the scan lock
                if not self._try_start_scan(scan_viewset):
                    error_msg = 'Another scan is already in progress'
                    logger.error(error_msg)
                    notify_scan_error(error_msg, user=schedule.user)
                    return

                # Initialize scan stats
                scan_viewset._current_scan_stats = {
                    'processed_pdfs': 0,
                    'renamed_pdfs': 0,
                    'computers_scanned': 0,
                    'total_computers': len(computer_ids),
                    'start_time': timezone.now(),
                    'estimated_completion': None,
                    'per_computer_progress': {},
                    'failed_computers': [],
                    'retry_attempts': {}
                }

                # Send initial notifications
                notify_scan_started(user=schedule.user)
                if schedule.email_notification and schedule.email_addresses:
                    self._send_email_notification(
                        schedule,
                        'Scheduled Scan Started',
                        f'A scheduled scan has been started for {len(computer_ids)} computers.'
                    )

                # Run the scan
                scan_viewset._scan_thread(computer_ids)
                
                # Update schedule only if scan completed successfully
                now = timezone.now()
                schedule.last_run = now
                schedule.next_run = schedule.calculate_next_run()
                schedule.save()

                # Send completion notifications
                notify_scan_completed(user=schedule.user)
                if schedule.email_notification and schedule.email_addresses:
                    self._send_email_notification(
                        schedule,
                        'Scheduled Scan Completed',
                        f'The scheduled scan for {len(computer_ids)} computers has completed.'
                    )

            except Exception as e:
                error_msg = f'Error during scan for schedule {schedule.id}: {str(e)}'
                logger.error(error_msg)
                notify_scan_error(error_msg, user=schedule.user)
                if schedule.email_notification and schedule.email_addresses:
                    self._send_email_notification(
                        schedule,
                        'Scheduled Scan Error',
                        f'An error occurred during the scheduled scan: {str(e)}'
                    )

            finally:
                # Always release the scan lock
                with self.scan_lock:
                    scan_viewset._scan_in_progress = False

    def _try_start_scan(self, scan_viewset):
        """Try to acquire the scan lock and start a new scan"""
        with self.scan_lock:
            if scan_viewset._scan_in_progress:
                return False
            scan_viewset._scan_in_progress = True
            return True

    def _send_email_notification(self, schedule, subject, message):
        """Send an email notification with proper error handling"""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=schedule.email_addresses,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f'Failed to send email notification for schedule {schedule.id}: {str(e)}')
