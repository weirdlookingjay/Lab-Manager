import asyncio
import websockets
import json
import logging
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class RelayClient:
    def __init__(self, relay_url):
        self.relay_url = relay_url
        self.django_token = os.getenv('DJANGO_TOKEN')
        if not self.django_token:
            raise ValueError("DJANGO_TOKEN environment variable not set")
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )

    async def handle_agent_metrics(self, data):
        """Handle metrics received from an agent"""
        try:
            hostname = data.get('hostname')
            metrics = data.get('data', {})
            logger.info(f"Received metrics from {hostname}: {metrics}")
            # TODO: Store metrics in your Django models
            # You can implement this based on your database schema
        except Exception as e:
            logger.error(f"Error handling metrics: {e}", exc_info=True)

    async def connect(self):
        """Connect to relay server and handle messages"""
        while True:
            try:
                logger.info(f"Connecting to relay server at {self.relay_url}")
                async with websockets.connect(self.relay_url) as websocket:
                    # Register as Django client with token
                    await websocket.send(json.dumps({
                        "client_type": "django",
                        "token": self.django_token
                    }))
                    logger.info("Sent authentication message")

                    # Wait for auth success response
                    response = await websocket.recv()
                    try:
                        data = json.loads(response)
                        if data.get('type') != 'auth_success':
                            logger.error(f"Authentication failed: {data}")
                            await asyncio.sleep(5)
                            continue
                        logger.info("Authentication successful")
                    except json.JSONDecodeError:
                        logger.error("Invalid authentication response")
                        await asyncio.sleep(5)
                        continue

                    # Handle incoming messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            message_type = data.get('type')

                            if message_type == 'update_metrics':
                                await self.handle_agent_metrics(data)
                            elif message_type == 'update_computer':
                                logger.info(f"Received computer update: {data}")
                            else:
                                logger.warning(f"Unknown message type: {message_type}")

                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON in message: {e}")
                        except Exception as e:
                            logger.error(f"Error handling message: {e}", exc_info=True)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed, attempting to reconnect...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Connection error: {e}", exc_info=True)
                await asyncio.sleep(5)

class Command(BaseCommand):
    help = 'Run the relay server client to receive agent metrics'

    def handle(self, *args, **options):
        # Load environment variables
        load_dotenv()
        
        relay_url = os.getenv('RELAY_URL', 'ws://localhost:8765')
        client = RelayClient(relay_url)
        
        # Run the client
        asyncio.run(client.connect())
