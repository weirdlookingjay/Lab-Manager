import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from user_management.models import Computer

class Command(BaseCommand):
    help = 'Update computer status in database from local file and ping'

    def handle(self, *args, **options):
        status_file = os.path.join(settings.BASE_DIR, 'computer_status.json')
        
        if not os.path.exists(status_file):
            self.stdout.write(self.style.WARNING('Status file not found'))
            return
            
        try:
            with open(status_file, 'r') as f:
                status_data = json.load(f)
                
            # Update database
            computers_updated = 0
            for computer_label, status in status_data.items():
                try:
                    # Ping the computer to check current status
                    computer_ip = status.get('ip')
                    if computer_ip:
                        response = os.system(f"ping -n 1 -w 1000 {computer_ip}")
                        is_online = response == 0
                        
                        computer = Computer.objects.get(label=computer_label)
                        computer.is_online = is_online
                        if is_online:
                            computer.last_seen = timezone.now()
                        computer.save()
                        computers_updated += 1
                        
                        # Update status file with new status
                        status_data[computer_label]['is_online'] = is_online
                        status_data[computer_label]['last_updated'] = timezone.now().isoformat()
                        
                except Computer.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Computer not found: {computer_label}')
                    )
            
            # Write updated status back to file
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                    
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {computers_updated} computers')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating computer status: {str(e)}')
            )
