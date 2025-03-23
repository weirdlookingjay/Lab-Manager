from django.core.management.base import BaseCommand
from django.conf import settings
import websockets
import json
import asyncio
import logging
import os
from django.utils import timezone
from user_management.models import Computer
from pathlib import Path
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Run the WebSocket relay client'

    def setup_logging(self):
        log_path = Path(settings.BASE_DIR) / 'logs' / 'relay_client.log'
        log_path.parent.mkdir(exist_ok=True)
        
        handlers = [
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers
        )

    def handle(self, *args, **options):
        self.setup_logging()
        asyncio.run(self.run_client())

    async def run_client(self):
        load_dotenv()
        relay_url = os.getenv('RELAY_URL', 'ws://localhost:8765')
        
        while True:
            try:
                async with websockets.connect(relay_url) as websocket:
                    logging.info(f"Connected to relay server at {relay_url}")
                    
                    # Register as Django client
                    await websocket.send(json.dumps({
                        "client_type": "django",
                        "token": os.getenv('DJANGO_TOKEN')
                    }))
                    
                    response = await websocket.recv()
                    logging.info(f"Registration response: {response}")
                    
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self.handle_message(data)
                        except json.JSONDecodeError:
                            logging.error(f"Invalid JSON message: {message}")
                        except Exception as e:
                            logging.error(f"Error handling message: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                logging.info("Connection closed, attempting to reconnect...")
            except Exception as e:
                logging.error(f"Connection error: {e}")
            
            # Wait before attempting to reconnect
            await asyncio.sleep(5)

    async def handle_message(self, message):
        """Handle messages from the relay server"""
        try:
            if message.get('type') == 'metrics':
                computer = Computer.objects.filter(label=message.get('hostname')).first()
                if computer:
                    computer.cpu_percent = message.get('cpu_percent')
                    computer.memory_percent = message.get('memory_percent')
                    computer.disk_usage_percent = message.get('disk_usage_percent')
                    computer.last_metrics_update = message.get('timestamp')
                    computer.last_seen = timezone.now()
                    computer.is_online = True
                    computer.save()
                    logging.info(f"Updated metrics for {computer.label}")
                    
            elif message.get('type') == 'agent_connected':
                computer = Computer.objects.filter(label=message.get('hostname')).first()
                if computer:
                    computer.is_online = True
                    computer.last_seen = timezone.now()
                    computer.save()
                    logging.info(f"Computer {computer.label} connected")
                    
            elif message.get('type') == 'agent_disconnected':
                computer = Computer.objects.filter(label=message.get('hostname')).first()
                if computer:
                    computer.is_online = False
                    computer.save()
                    logging.info(f"Computer {computer.label} disconnected")
                    
        except Exception as e:
            logging.error(f"Error handling message: {e}")
