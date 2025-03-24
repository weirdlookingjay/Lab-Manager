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
import dotenv
import sys
import signal
import subprocess
import socket

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
            freq = psutil.cpu_freq()
            
            # Get base and current CPU frequencies
            base_speed = info.get('hz_advertised_float', 
                              freq.max if freq else None)
            current_speed = freq.current if freq else None
            
            # Convert frequencies from MHz to GHz if needed
            if base_speed and base_speed > 1000:
                base_speed /= 1000
            if current_speed and current_speed > 1000:
                current_speed /= 1000
                
            # Use base speed for CPU speed field, fallback to current speed
            speed = base_speed if base_speed else current_speed
                
            return {
                'model': info.get('brand_raw', platform.processor()),
                'architecture': info.get('arch', platform.machine()),
                'cores': psutil.cpu_count(logical=False),
                'threads': psutil.cpu_count(),
                'speed': f"{speed:.1f}" if speed else None,
                'base_speed': f"{base_speed:.1f}" if base_speed else None,
                'current_speed': f"{current_speed:.1f}" if current_speed else None,
                'manufacturer': info.get('brand_raw', 'Unknown').split()[0]
            }
        except ImportError:
            # Fallback if py-cpuinfo is not available
            freq = psutil.cpu_freq()
            current_speed = freq.current if freq else None
            base_speed = freq.max if freq else None
            
            # Convert frequencies from MHz to GHz if needed
            if base_speed and base_speed > 1000:
                base_speed /= 1000
            if current_speed and current_speed > 1000:
                current_speed /= 1000
            
            # Use base speed for CPU speed field, fallback to current speed    
            speed = base_speed if base_speed else current_speed
                
            return {
                'model': platform.processor(),
                'architecture': platform.machine(),
                'cores': psutil.cpu_count(logical=False),
                'threads': psutil.cpu_count(),
                'speed': f"{speed:.1f}" if speed else None,
                'base_speed': f"{base_speed:.1f}" if base_speed else None,
                'current_speed': f"{current_speed:.1f}" if current_speed else None,
                'manufacturer': 'Unknown'
            }

    def get_logged_in_user(self) -> str:
        """Get the currently logged in user, even when running as SYSTEM."""
        try:
            if platform.system() == 'Windows':
                import subprocess
                
                # First try query user to get interactive sessions
                try:
                    result = subprocess.run("query user", capture_output=True, text=True, shell=True)
                    if result.returncode == 0 and result.stdout:
                        lines = result.stdout.strip().split('\n')[1:]  # Skip header
                        for line in lines:
                            parts = line.split()
                            if len(parts) >= 3:
                                username = parts[0]
                                state = parts[3] if len(parts) > 3 else ''
                                if state == 'Active':
                                    logging.info(f"Found active user: {username}")
                                    return username
                except Exception as e:
                    logging.warning(f"Error running query user: {e}")

                # If no active user found, try WMIC as backup
                try:
                    result = subprocess.run("wmic computersystem get username", 
                                        capture_output=True, text=True, shell=True)
                    if result.returncode == 0 and result.stdout:
                        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
                        if len(lines) >= 2:
                            username = lines[1]  # Skip header row
                            if '\\' in username:
                                username = username.split('\\')[-1]
                            if username and username.lower() != 'system':
                                logging.info(f"Found user via WMIC: {username}")
                                return username
                except Exception as e:
                    logging.warning(f"Error running WMIC: {e}")
                
                # Final fallback to environment variables
                try:
                    username = os.getenv('USERNAME')
                    if username and username.upper() != 'SYSTEM':
                        logging.info(f"Found user via environment: {username}")
                        return username
                except Exception as e:
                    logging.warning(f"Error getting username from environment: {e}")
                    
                logging.warning("No interactive user found")
                return "No user logged in"
            
            # For non-Windows systems
            try:
                who_output = subprocess.run(['who'], capture_output=True, text=True)
                if who_output.returncode == 0 and who_output.stdout:
                    # Get the first logged in user
                    user = who_output.stdout.split()[0]
                    if user and user.upper() != 'SYSTEM':
                        logging.info(f"Found user via who command: {user}")
                        return user
            except Exception as e:
                logging.warning(f"Error running who command: {e}")
            
            try:
                user = os.getenv('USER') or os.getenv('USERNAME')
                if user and user.upper() != 'SYSTEM':
                    logging.info(f"Found user via environment: {user}")
                    return user
            except Exception as e:
                logging.warning(f"Error getting username from environment: {e}")
            
            logging.warning("No user found")
            return "No user logged in"
                
        except Exception as e:
            logging.error(f"Error getting current user: {e}", exc_info=True)
            return "Unknown"

    def format_uptime(self, timedelta_obj) -> str:
        """Format uptime into a human-readable string."""
        days = timedelta_obj.days
        hours, remainder = divmod(timedelta_obj.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if not parts:  # If less than a minute
            parts.append(f"{seconds}s")
            
        return " ".join(parts)

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics."""
        try:
            logger = logging.getLogger(__name__)
            logger.info("Collecting system metrics...")
            
            # Get memory information
            memory = psutil.virtual_memory()
            logger.info(f"Memory: Total={memory.total / (1024**3):.1f}GB, Used={memory.used / (1024**3):.1f}GB ({memory.percent}%)")
            
            # Get disk information for the system drive
            system_drive = os.getenv('SystemDrive', 'C:') if platform.system() == 'Windows' else '/'
            disk_usage = psutil.disk_usage(system_drive)
            logger.info(f"Disk ({system_drive}): Total={disk_usage.total / (1024**3):.1f}GB, Used={disk_usage.used / (1024**3):.1f}GB ({disk_usage.percent}%)")

            # Get CPU information
            cpu_info = self.get_cpu_info()
            cpu_percent = psutil.cpu_percent(interval=1)
            logger.info(f"CPU: {cpu_info['model']}, Usage={cpu_percent}%")
            
            # Calculate uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            # Convert bytes to GB
            def bytes_to_gb(bytes_value: int) -> str:
                return f"{bytes_value / (1024 ** 3):.1f}"
            
            metrics = {
                'cpu': {
                    'model': cpu_info['model'],
                    'speed': cpu_info['speed'],
                    'cores': cpu_info['cores'],
                    'threads': cpu_info['threads'],
                    'architecture': cpu_info['architecture'],
                    'manufacturer': cpu_info['manufacturer'],
                    'percent': cpu_percent
                },
                'memory': {
                    'total_bytes': memory.total,
                    'available_bytes': memory.available,
                    'used_bytes': memory.used,
                    'percent': memory.percent,
                    'total_gb': bytes_to_gb(memory.total),
                    'available_gb': bytes_to_gb(memory.available),
                    'used_gb': bytes_to_gb(memory.used)
                },
                'disk': {
                    'total_bytes': disk_usage.total,
                    'free_bytes': disk_usage.free,
                    'used_bytes': disk_usage.used,
                    'percent': disk_usage.percent,
                    'total_gb': bytes_to_gb(disk_usage.total),
                    'free_gb': bytes_to_gb(disk_usage.free),
                    'used_gb': bytes_to_gb(disk_usage.used)
                },
                'system': {
                    'device_class': self.detect_device_class(),
                    'boot_time': int(psutil.boot_time()),
                    'uptime': self.format_uptime(uptime),
                    'os_version': platform.platform(),
                    'logged_in_user': self.get_logged_in_user(),
                    'status': 'online'
                },
                'status': 'online',
                'hostname': platform.node(),
                'ip_address': socket.gethostbyname(socket.gethostname()),
                'last_seen': datetime.now().isoformat(),
                'last_metrics_update': datetime.now().isoformat()
            }

            logger.info("System metrics collected successfully")
            logger.info(f"Sending metrics to relay server: {json.dumps(metrics, indent=2)}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}", exc_info=True)
            # Return partial metrics if possible
            return {
                'system': {
                    'status': 'error',
                    'error': str(e)
                }
            }

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

    async def metrics_loop(self) -> None:
        """Periodically collect and send system metrics."""
        logger = logging.getLogger(__name__)
        while self.running:
            try:
                metrics = await self.collect_system_metrics()
                message = {
                    'type': 'update_metrics',
                    **metrics  # Spread metrics at root level
                }
                logger.info(f"Sending metrics to relay server: {json.dumps(message, indent=2)}")
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error in metrics loop: {e}", exc_info=True)
            await asyncio.sleep(60)  # Update every minute

    async def start(self) -> None:
        """Start the computer agent."""
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to connect to relay server at {self.relay_url}")
        
        try:
            async with websockets.connect(self.relay_url) as websocket:
                self.websocket = websocket
                
                # Send registration message
                registration = {
                    'type': 'register',
                    'client_type': 'agent',
                    'token': self.agent_token,
                    'hostname': platform.node()
                }
                logger.info("Sending registration message")
                await websocket.send(json.dumps(registration))
                
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get('type') == 'auth_success':
                    logger.info("Authentication successful")
                    
                    # Send initial system info
                    metrics = await self.collect_system_metrics()
                    message = {
                        'type': 'update_metrics',
                        **metrics  # Spread metrics at root level
                    }
                    logger.info("Sending initial system info")
                    logger.info(f"Initial metrics: {json.dumps(message, indent=2)}")
                    await websocket.send(json.dumps(message))
                    
                    # Start metrics loop
                    metrics_task = asyncio.create_task(self.metrics_loop())
                    
                    try:
                        while self.running:
                            message = await websocket.recv()
                            data = json.loads(message)
                            await self.handle_command(data)
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("Connection closed by server")
                    finally:
                        metrics_task.cancel()
                else:
                    logger.error("Authentication failed")
        except (websockets.exceptions.ConnectionError, 
                websockets.exceptions.InvalidStatusCode,
                ConnectionRefusedError) as e:
            logger.error(f"Connection error: {str(e)}")
                
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                
        if self.running:
            logger.info(f"Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

    def stop(self) -> None:
        """Stop the computer agent."""
        logger = logging.getLogger(__name__)
        logger.info("Stopping computer agent")
        self.running = False
        # Note: Don't try to close the websocket here
        # It will be closed by the context manager in start()

async def shutdown(agent: ComputerAgent, loop: asyncio.AbstractEventLoop):
    """Handle graceful shutdown of the agent."""
    logging.info("Shutting down...")
    agent.stop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    logging.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def main():
    try:
        # Set up logging for the main process
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # Use the correct logs directory
        log_dir = os.path.join('C:\\Temp\\_deployment\\logs')
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'agent.log')
            # Test if we can write to the log file
            with open(log_file, 'a') as f:
                pass
        except (OSError, IOError) as e:
            print(f"Error: Could not write to {log_dir}: {e}")
            sys.exit(1)
        
        # Set up file handler for all logs (INFO and above)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Set up stream handler for errors only
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setLevel(logging.ERROR)
        stream_handler.setFormatter(logging.Formatter(log_format))
        
        # Remove any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[file_handler, stream_handler]
        )
        
        logger = logging.getLogger(__name__)
        logger.info(f"Logger configured successfully, writing to {log_file}")
        
        # Load environment variables
        dotenv.load_dotenv()
        relay_url = os.getenv('RELAY_URL', 'ws://192.168.72.19:8765')
        agent_token = os.getenv('COMPUTER_AGENT_TOKEN')
        
        logger.info(f"Environment loaded - RELAY_URL: {relay_url}, TOKEN: {'set' if agent_token else 'not set'}")
        
        if not agent_token:
            logger.error("COMPUTER_AGENT_TOKEN environment variable not set")
            sys.exit(1)
            
        # Create and start agent
        agent = ComputerAgent(relay_url, agent_token)
        
        # Windows-compatible way to handle shutdown
        def handle_shutdown(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            agent.stop()
            
        # Register signal handlers if on Windows
        if platform.system() == 'Windows':
            try:
                import win32api
                def handler(type):
                    handle_shutdown(0, None)
                    return True  # Indicate we handled the event
                win32api.SetConsoleCtrlHandler(handler, True)
                logger.info("Registered Windows shutdown handler")
            except ImportError:
                logger.warning("win32api not available, using basic signal handlers")
                signal.signal(signal.SIGINT, handle_shutdown)
                signal.signal(signal.SIGTERM, handle_shutdown)
        else:
            # Unix systems can use basic signal handlers
            signal.signal(signal.SIGINT, handle_shutdown)
            signal.signal(signal.SIGTERM, handle_shutdown)
            
        logger.info(f"Starting computer agent, connecting to {relay_url}")
        await agent.start()
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
