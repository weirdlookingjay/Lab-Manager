import os
from django.core.management.base import BaseCommand
from user_management.models import Computer

class Command(BaseCommand):
    help = 'Import computers from pc_names.txt file'

    def handle(self, *args, **kwargs):
        txt_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), 'pc_names.txt')
        if not os.path.exists(txt_file):
            self.stdout.write(self.style.ERROR(f'pc_names.txt file not found: {txt_file}'))
            return

        try:
            # Delete existing computers first
            Computer.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Deleted existing computers'))

            # Read and parse pc_names.txt
            with open(txt_file, 'r') as f:
                # Skip header line
                next(f)
                for line in f:
                    # Split by whitespace and get IP and label
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip_address = parts[0].strip()
                        label = parts[1].strip()
                        
                        # Skip computers with IP 192.168.72.00
                        if ip_address == '192.168.72.00':
                            self.stdout.write(self.style.WARNING(f'Skipping invalid IP for {label}'))
                            continue

                        Computer.objects.create(
                            ip_address=ip_address,
                            label=label
                        )
                        self.stdout.write(self.style.SUCCESS(f'Created computer {label} with IP {ip_address}'))

            self.stdout.write(self.style.SUCCESS('Successfully imported all computers'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing computers: {str(e)}'))
