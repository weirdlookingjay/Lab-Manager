import asyncio
import websockets
import json
import logging
import os
import sys
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from .models import Computer, SystemLog, Command
from django.utils import timezone

logger = logging.getLogger(__name__)

class RelayClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.uri = "ws://192.168.72.19:8765"
            self.websocket = None
            self.is_connected = False
            self.relay_url = getattr(settings, 'RELAY_URL', 'ws://your-relay-server:8765')
            self.channel_layer = get_channel_layer()
            self.initialized = True

    async def connect(self):
        # Only connect in the main Django process
        if 'RUN_MAIN' not in os.environ:
            return

        try:
            # Connect
            print("\nConnecting to relay server...")
            self.websocket = await websockets.connect(self.uri)
            print("Connected!")

            # Register as monitor client
            reg_message = {
                "type": "register",
                "client_type": "django",
                "token": getattr(settings, 'DJANGO_TOKEN', 'JXpV2Tl9UR1LQrhnhPQrzJ6GPCFlnEIzzlAkN3PkeT8'),
                "subscribe": ["metrics", "update_metrics"]
            }
            
            print("\nSending registration:")
            print(json.dumps(reg_message, indent=2))
            await self.websocket.send(json.dumps(reg_message))
            
            response = await self.websocket.recv()
            print("\nRegistration response:")
            print(response)
            
            # Handle messages
            while True:
                try:
                    msg = await self.websocket.recv()
                    print("\n" + "="*80)
                    print("NEW RELAY MESSAGE RECEIVED:")
                    print("-"*80)
                    print(msg)  # Raw message
                    print("="*80 + "\n")
                    sys.stdout.flush()  # Force print to show immediately
                    
                    # Process the message
                    try:
                        data = json.loads(msg)
                        message_type = data.get('type')
                        if message_type in ['metrics', 'update_metrics']:  # Handle both message types
                            metrics_data = data.get('data', {})
                            logged_in_user = data.get('logged_in_user')
                            agent_hostname = data.get('hostname')
                            if not metrics_data:
                                logging.warning(f"Metrics message missing data: {data}")
                                return

                            ip_address = metrics_data.get('ip_address')
                            if not ip_address:
                                logging.warning(f"Metrics missing IP address: {data}")
                                return

                            try:
                                # First try to find computer by IP (since it's unique)
                                computer = await sync_to_async(Computer.objects.filter(ip_address=ip_address).first)()

                                if computer:
                                    # Update system information
                                    computer.device_class = metrics_data.get('device_class', computer.device_class)
                                    computer.model = metrics_data.get('model', computer.model)
                                    computer.os_version = metrics_data.get('os_version', computer.os_version)
                                    computer.logged_in_user = logged_in_user
                                    computer.hostname = agent_hostname
                                    computer.boot_time = metrics_data.get('boot_time', computer.boot_time)
                                    computer.system_uptime = metrics_data.get('system_uptime', computer.system_uptime)

                                    # Update metrics
                                    metrics = computer.metrics or {}

                                    # Update CPU metrics
                                    if 'cpu' in metrics_data:
                                        cpu_info = metrics_data['cpu']
                                        metrics['cpu'] = {
                                            'model': cpu_info.get('model'),
                                            'speed': cpu_info.get('speed'),
                                            'cores': cpu_info.get('cores'),
                                            'threads': cpu_info.get('threads'),
                                            'architecture': cpu_info.get('architecture'),
                                            'percent': cpu_info.get('percent', 0)
                                        }

                                    # Update memory metrics
                                    if 'memory' in metrics_data:
                                        memory_info = metrics_data['memory']
                                        metrics['memory'] = {
                                            'total': memory_info.get('total'),
                                            'available': memory_info.get('available'),
                                            'used': memory_info.get('used'),
                                            'percent': memory_info.get('percent', 0)
                                        }

                                    # Update disk metrics
                                    if 'disk' in metrics_data:
                                        disk_info = metrics_data['disk']
                                        metrics['disk'] = {
                                            'total': disk_info.get('total'),
                                            'free': disk_info.get('free'),
                                            'used': disk_info.get('used'),
                                            'percent': disk_info.get('percent', 0)
                                        }

                                    computer.metrics = metrics
                                    computer.last_metrics_update = timezone.now()
                                    await sync_to_async(computer.save)()
                                    logging.info(f"Updated metrics for computer {computer.label} - Status: Online")

                                    # Create a system log entry for the metrics update
                                    await sync_to_async(SystemLog.objects.create)(
                                        computer=computer,
                                        category='COMPUTER_STATUS',
                                        event='COMPUTER_ONLINE',
                                        level='INFO',
                                        message=f"Computer {computer.label} reported metrics",
                                        details=metrics
                                    )
                                else:
                                    # Create new computer with default label = PC{N} and store hostname
                                    # Get next available PC number
                                    last_pc = await sync_to_async(Computer.objects.filter(label__startswith='PC').order_by('-label').first)()
                                    next_num = 1
                                    if last_pc:
                                        try:
                                            last_num = int(last_pc.label[2:])
                                            next_num = last_num + 1
                                        except ValueError:
                                            pass
                                    
                                    new_label = f'PC{next_num}'
                                    computer = await sync_to_async(Computer.objects.create)(
                                        label=new_label,
                                        hostname=agent_hostname,
                                        ip_address=ip_address,
                                        os_version=metrics_data.get('os_version', ''),
                                        model=metrics_data.get('model', ''),
                                        device_class=metrics_data.get('device_class', ''),
                                        boot_time=metrics_data.get('boot_time', ''),
                                        system_uptime=metrics_data.get('system_uptime', ''),
                                        last_metrics_update=timezone.now(),
                                        last_seen=timezone.now(),
                                        is_online=True
                                    )
                                    logging.info(f"Created new computer {new_label} with hostname {agent_hostname} ({ip_address})")
                                    return

                            except Exception as e:
                                logging.error(f"Error processing metrics: {str(e)}", exc_info=True)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON message received")
                    except Exception as e:
                        print(f"Error processing message: {e}")
                    
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed by relay server")
                    break
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    continue
                
        except Exception as e:
            print(f"Relay connection error: {e}")
            self.is_connected = False

# Global relay client instance
relay_client = RelayClient()

def start_relay_client():
    """Start the relay client in a background task"""
    asyncio.run(relay_client.connect())
