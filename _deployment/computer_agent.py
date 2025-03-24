import os
import json
import logging
import asyncio
import websockets
import psutil
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from base64 import b64encode, b64decode

class ComputerAgent:
    def __init__(self, relay_url: str, agent_token: str):
        self.relay_url = relay_url
        self.agent_token = agent_token
        self.websocket = None
        self.last_metrics_update = None
        self.last_seen = None
        self.running = True

    async def handle_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle commands received from the relay server."""
        command = command_data.get('command')
        command_id = command_data.get('command_id')
        
        try:
            result = None
            if command == 'list_files':
                result = await self.list_files(command_data.get('path', '/'))
            elif command == 'download_file':
                result = await self.download_file(
                    command_data.get('remote_path'),
                    command_data.get('local_path')
                )
            elif command == 'upload_file':
                result = await self.upload_file(
                    command_data.get('local_path'),
                    command_data.get('remote_path'),
                    command_data.get('file_content')
                )
            
            if result:
                await self.send_command_result(command_id, 'completed', result)
            else:
                await self.send_command_result(command_id, 'failed', {'error': 'Unknown command'})
                
        except Exception as e:
            logging.error(f"Error executing command: {e}")
            await self.send_command_result(command_id, 'failed', {'error': str(e)})

    async def list_files(self, path: str) -> Dict[str, Any]:
        """List files in the specified directory."""
        try:
            target_path = Path(path).resolve()
            if not target_path.exists():
                return {'error': 'Path does not exist'}
            
            files = []
            for item in target_path.iterdir():
                try:
                    stat = item.stat()
                    files.append({
                        'name': item.name,
                        'path': str(item),
                        'isDirectory': item.is_dir(),
                        'size': stat.st_size if item.is_file() else None,
                        'modifiedTime': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except (PermissionError, OSError):
                    # Skip files we can't access
                    continue
            
            return {
                'files': sorted(files, key=lambda x: (not x['isDirectory'], x['name'].lower()))
            }
        except Exception as e:
            return {'error': str(e)}

    async def download_file(self, remote_path: str, local_path: str) -> Dict[str, Any]:
        """Copy a file from this computer to the local machine."""
        try:
            src_path = Path(remote_path).resolve()
            if not src_path.exists():
                return {'error': 'Source file does not exist'}
            if not src_path.is_file():
                return {'error': 'Source path is not a file'}
            
            # Read the file content and encode as base64
            with open(src_path, 'rb') as f:
                content = f.read()
                content_b64 = b64encode(content).decode('utf-8')
            
            # Send file content back to be written by Django
            return {
                'content': content_b64,
                'size': len(content),
                'success': True
            }
        except Exception as e:
            return {'error': str(e)}

    async def upload_file(self, local_path: str, remote_path: str, file_content: str) -> Dict[str, Any]:
        """Copy a file from the local machine to this computer."""
        try:
            # Ensure the destination directory exists
            dest_path = Path(remote_path).resolve()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Decode base64 content and write
            content = b64decode(file_content)
            with open(dest_path, 'wb') as f:
                f.write(content)
            
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    def detect_device_class(self) -> str:
        """Detect the device class based on system characteristics."""
        try:
            if platform.system() == 'Darwin':
                return 'Mac'
            elif platform.system() == 'Windows':
                # Check if it's a laptop by looking for battery
                battery = psutil.sensors_battery()
                if battery is not None:
                    return 'Laptop'
                return 'Desktop'
            elif platform.system() == 'Linux':
                # Check for common indicators of different device types
                with open('/sys/class/dmi/id/chassis_type', 'r') as f:
                    chassis_type = int(f.read().strip())
                    # Common chassis types: 
                    # 3: Desktop, 8: Portable, 9,10: Laptop, 30,31,32: Tablet
                    if chassis_type in [9, 10]:
                        return 'Laptop'
                    elif chassis_type == 3:
                        return 'Desktop'
                    elif chassis_type in [30, 31, 32]:
                        return 'Tablet'
            return 'Unknown'
        except:
            return 'Unknown'

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information."""
        try:
            import cpuinfo
            info = cpuinfo.get_cpu_info()
            speed = info.get('hz_advertised_friendly', None)
            base_speed = info.get('hz_actual_friendly', None)
            current_speed = info.get('hz_current_friendly', None)
            
            # Get the model info and extract manufacturer
            model = info.get('brand_raw', platform.processor())
            # Try to extract manufacturer from model string
            manufacturer = None
            if model:
                # Common CPU manufacturer keywords
                manufacturers = ['Intel', 'AMD', 'ARM']
                model_upper = model.upper()
                for m in manufacturers:
                    if m.upper() in model_upper:
                        manufacturer = m
                        break
            
            if not manufacturer:
                # Fallback to first word if no known manufacturer found
                manufacturer = model.split()[0] if model else 'Unknown'
            
            return {
                'model': model,
                'architecture': info.get('arch', platform.machine()),
                'cores': psutil.cpu_count(logical=False),
                'threads': psutil.cpu_count(),
                'speed': f"{speed:.1f}" if speed else None,
                'base_speed': f"{base_speed:.1f}" if base_speed else None,
                'current_speed': f"{current_speed:.1f}" if current_speed else None,
                'manufacturer': manufacturer
            }
        except ImportError:
            # Fallback if py-cpuinfo is not available
            freq = psutil.cpu_freq()
            return {
                'model': platform.processor(),
                'architecture': platform.machine(),
                'cores': psutil.cpu_count(logical=False),
                'threads': psutil.cpu_count(),
                'speed': freq.current if freq else None
            }

    def get_logged_in_user(self) -> str:
        """Get the currently logged in user, even when running as SYSTEM."""
        try:
            if platform.system() == 'Windows':
                # Try checking explorer.exe processes first (most reliable)
                try:
                    import psutil
                    for proc in psutil.process_iter(['name', 'username']):
                        if proc.info['name'] == 'explorer.exe' and proc.info['username']:
                            # Remove domain prefix if present
                            username = proc.info['username']
                            if '\\' in username:
                                username = username.split('\\')[1]
                            return username
                except Exception as e:
                    logging.debug(f"Failed to get user via explorer.exe check: {e}")
                
                # Fallback to environment variables
                try:
                    username = os.environ.get('USERNAME') or os.environ.get('USER')
                    if username and username.lower() != 'system':
                        return username
                except Exception as e:
                    logging.debug(f"Failed to get user from environment: {e}")
            
            # For non-Windows systems or if all else fails
            try:
                return os.getlogin()
            except Exception:
                return "Unknown"
        except Exception as e:
            logging.error(f"Error getting logged in user: {e}")
            return "Unknown"

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics."""
        try:
            memory = psutil.virtual_memory()
            
            # Get disk information for the system drive
            system_drive = os.getenv('SystemDrive', 'C:') if platform.system() == 'Windows' else '/'
            disk_usage = psutil.disk_usage(system_drive)

            # Get CPU information
            cpu_info = self.get_cpu_info()
            
            metrics = {
                'cpu': {
                    'model': cpu_info['model'],
                    'speed': cpu_info['speed'],
                    'cores': cpu_info['cores'],
                    'threads': cpu_info['threads'],
                    'architecture': cpu_info['architecture'],
                    'percent': psutil.cpu_percent(interval=1)
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk_usage.total,
                    'free': disk_usage.free,
                    'used': disk_usage.used,
                    'percent': disk_usage.percent
                },
                'system': {
                    'device_class': self.detect_device_class(),
                    'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                    'uptime': str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())),
                    'os_version': platform.platform(),
                    'logged_in_user': self.get_logged_in_user()
                }
            }

            self.last_metrics_update = datetime.now()
            return metrics
            
        except Exception as e:
            logging.error(f"Error collecting metrics: {e}")
            return None

    async def send_command_result(self, command_id: str, status: str, data: Dict[str, Any]) -> None:
        """Send command execution result back to the relay server."""
        if self.websocket:
            message = {
                'type': 'command_result',
                'command_id': command_id,
                'status': status,
                'data': data
            }
            await self.websocket.send(json.dumps(message))

    async def start(self) -> None:
        """Start the computer agent."""
        while self.running:
            try:
                async with websockets.connect(self.relay_url) as websocket:
                    self.websocket = websocket
                    self.last_seen = datetime.now()

                    # Get CPU info once at startup
                    cpu_info = self.get_cpu_info()
                    
                    # Send initial system info
                    system_info = {
                        'type': 'system_info',
                        'hostname': platform.node(),
                        'os_version': platform.platform(),
                        'model': platform.machine(),
                        'cpu_model': cpu_info['model'],
                        'cpu_architecture': cpu_info['architecture'],
                        'device_class': self.detect_device_class(),
                        'agent_token': self.agent_token,
                        'last_seen': self.last_seen.isoformat()
                    }
                    await websocket.send(json.dumps(system_info))

                    # Start metrics collection loop
                    asyncio.create_task(self.metrics_loop())

                    # Handle incoming messages
                    async for message in websocket:
                        self.last_seen = datetime.now()
                        try:
                            data = json.loads(message)
                            if data.get('type') == 'command':
                                await self.handle_command(data)
                        except json.JSONDecodeError:
                            logging.error("Invalid JSON message received")
                        except Exception as e:
                            logging.error(f"Error handling message: {e}")

            except websockets.exceptions.ConnectionClosed:
                logging.info("Connection closed, attempting to reconnect...")
                await asyncio.sleep(5)
            except Exception as e:
                logging.error(f"Connection error: {e}")
                await asyncio.sleep(5)

    async def metrics_loop(self) -> None:
        """Periodically collect and send system metrics."""
        while self.running:
            try:
                metrics = await self.collect_system_metrics()
                if metrics and self.websocket:
                    await self.websocket.send(json.dumps({
                        'type': 'metrics',
                        'data': metrics,
                        'timestamp': datetime.now().isoformat()
                    }))
            except Exception as e:
                logging.error(f"Error in metrics loop: {e}")
            
            await asyncio.sleep(60)  # Collect metrics every minute

    def stop(self) -> None:
        """Stop the computer agent."""
        self.running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())

def setup_logging():
    """Setup logging configuration"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'computer_agent.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )
    logging.info('Logging initialized')

async def main():
    """Main entry point"""
    setup_logging()  # Setup logging first
    agent = ComputerAgent('ws://192.168.72.19:8765', 'your_agent_token')
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())
