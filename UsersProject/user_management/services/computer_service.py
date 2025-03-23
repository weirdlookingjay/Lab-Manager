import logging
import json
from django.utils import timezone
from django.db import transaction
from ..models import Computer

logger = logging.getLogger(__name__)

class ComputerService:
    @staticmethod
    def update_computer_from_metrics(hostname, metrics_data):
        """Update computer record from metrics data"""
        try:
            logger.info("\n" + "="*80)
            logger.info("PROCESSING METRICS DATA:")
            logger.info(json.dumps(metrics_data, indent=2))
            
            with transaction.atomic():
                computer = Computer.objects.select_for_update().filter(hostname=hostname).first()
                
                # Log current state
                logger.info("Current state:")
                logger.info(f"  hostname: {hostname}")
                logger.info(f"  computer found: {computer is not None}")
                logger.info(f"  is_online: {getattr(computer, 'is_online', False)}")
                
                if not computer:
                    logger.info(f"Creating new computer record for hostname: {hostname}")
                    computer = Computer(hostname=hostname)
                
                # Update fields
                computer.is_online = True  # Set to True when we receive metrics
                computer.last_seen = timezone.now()
                computer.last_metrics_update = timezone.now()
                computer.logged_in_user = metrics_data.get('logged_in_user')
                
                # Get metrics directly from root
                metrics = metrics_data.get('metrics', {})
                
                # CPU info
                cpu_info = metrics.get('cpu', {})
                computer.cpu_usage = cpu_info.get('percent')  
                computer.cpu_model = cpu_info.get('model')
                computer.cpu_cores = cpu_info.get('cores')
                computer.cpu_threads = cpu_info.get('threads')
                
                # Memory info
                memory_info = metrics.get('memory', {})
                if memory_info:
                    computer.total_memory = memory_info.get('total_bytes', computer.total_memory)
                    computer.memory_usage = memory_info.get('percent', computer.memory_usage)
                
                # Disk info
                disk_info = metrics.get('disk', {})
                if disk_info:
                    computer.total_disk = disk_info.get('total_bytes', computer.total_disk)
                    computer.disk_usage = disk_info.get('percent', computer.disk_usage)
                
                # System info
                system_info = metrics.get('system', {})
                computer.os_version = system_info.get('os_version')
                computer.device_class = system_info.get('device_class')
                
                # Store raw metrics for future reference
                computer.metrics = metrics
                
                computer.save()
                
                # Verify update
                logger.info("Updated state:")
                logger.info(f"  hostname: {computer.hostname}")
                logger.info(f"  is_online: {computer.is_online}")
                logger.info(f"  logged_in_user: {computer.logged_in_user}")
                logger.info(f"  cpu_usage: {computer.cpu_usage}")
                logger.info(f"  cpu_model: {computer.cpu_model}")
                logger.info(f"  memory_usage: {computer.memory_usage}")
                logger.info(f"  total_memory: {computer.total_memory}")
                logger.info(f"  disk_usage: {computer.disk_usage}")
                logger.info(f"  total_disk: {computer.total_disk}")
                logger.info(f"  metrics: {json.dumps(computer.metrics, indent=2)}")
                logger.info("="*80 + "\n")
                
                return computer

        except Exception as e:
            logger.error(f"Error updating computer: {e}", exc_info=True)
            raise