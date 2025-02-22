from django.core.management.base import BaseCommand
from notifications.models import PDFAttachment
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Check PDFs in directory vs database'

    def handle(self, *args, **options):
        # Get all PDFs from the database
        db_pdfs = PDFAttachment.objects.all()
        self.stdout.write(f"PDFs in database: {db_pdfs.count()}")
        for pdf in db_pdfs:
            self.stdout.write(f"- {pdf.original_filename} (ID: {pdf.id})")

        # Get all PDFs from the directory
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', 'PC5')
        if os.path.exists(pdf_dir):
            files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
            self.stdout.write(f"\nPDFs in directory: {len(files)}")
            for file in files:
                self.stdout.write(f"- {file}")
        else:
            self.stdout.write(f"\nDirectory {pdf_dir} does not exist")
