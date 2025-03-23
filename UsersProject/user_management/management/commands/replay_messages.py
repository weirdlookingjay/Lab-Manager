from django.core.management.base import BaseCommand
from pathlib import Path
import json

class Command(BaseCommand):
    def handle(self, *args, **options):
        raw_dir = Path(__file__).parent.parent.parent / "raw_messages"
        for f in raw_dir.glob("message_*.json"):
            with open(f) as fp:
                message = json.load(fp)
                # Process message using same logic as websocket handler
                self.process_message(message)