from django.core.management.base import BaseCommand
from notifications.models import PDFAttachment
from django.contrib.auth import get_user_model
import os
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Register existing PDFs in the database'

    def handle(self, *args, **options):
        # Get or create a superuser to associate with the PDFs
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write("No superuser found. Please create one first.")
            return

        # Get all PDFs from the directory
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', 'PC5')
        if not os.path.exists(pdf_dir):
            self.stdout.write(f"Directory {pdf_dir} does not exist")
            return

        files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        for file in files:
            file_path = os.path.join('pdfs', 'PC5', file)
            # Check if PDF is already registered
            if not PDFAttachment.objects.filter(original_filename=file).exists():
                full_path = os.path.join(settings.MEDIA_ROOT, 'pdfs', 'PC5', file)
                file_size = os.path.getsize(full_path)
                PDFAttachment.objects.create(
                    file=file_path,
                    original_filename=file,
                    uploaded_by=admin_user,
                    file_size=file_size
                )
                self.stdout.write(f"Registered: {file}")
            else:
                self.stdout.write(f"Already exists: {file}")

        self.stdout.write(self.style.SUCCESS('PDF registration complete'))
