import asyncio
import websockets
import logging
import json
import os
import sys
from pathlib import Path
import socket
from dotenv import load_dotenv
from datetime import datetime

class RelayServer:
    def __init__(self, host='0.0.0.0', port=8765):
        """Initialize the relay server."""
        self.host = host
        self.port = port
        self.clients = {}
        self.django_client = None
        self.agent_token = None
        self.django_token = None
        
        # Set up logging first
        self.setup_logging()
        
        # Load environment variables
        self.load_env()
        
        logging.info(f"Relay server initialized on {self.host}:{self.port}")

    def load_env(self):
        """Load environment variables."""
        # Load .env file
        load_dotenv()
        
        # Get and validate agent token
        self.agent_token = os.getenv('COMPUTER_AGENT_TOKEN')
        if not self.agent_token:
            logging.error("COMPUTER_AGENT_TOKEN environment variable not set")
            sys.exit(1)
            
        # Get and validate Django token
        self.django_token = os.getenv('DJANGO_TOKEN')
        if not self.django_token:
            logging.error("DJANGO_TOKEN environment variable not set")
            sys.exit(1)
            
        # Log success but not the token
        logging.info("Environment variables loaded successfully")
        
    def setup_logging(self):
        """Set up logging configuration."""
        try:
            # Ensure we're in the correct directory
            os.chdir(str(Path(__file__).parent))
            
            # Set up log file
            log_path = Path(os.getcwd()) / 'relay.log'
            handlers = [
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
            
            # Configure logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=handlers
            )
            
            logging.info(f"Logging initialized. Log file: {log_path}")
        except Exception as e:
            print(f"Error setting up logging: {e}")
            sys.exit(1)

    @staticmethod
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return False
            except OSError:
                return True

    async def start(self):
        # Ensure we're in the correct directory
        os.chdir(str(Path(__file__).parent))
        
        logging.info("Starting relay server...")
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Working directory: {os.getcwd()}")
        
        # Check if port is already in use
        if self.is_port_in_use(self.port):
            logging.error(f"Port {self.port} is already in use. Please free up the port and try again.")
            sys.exit(1)
            
        try:
            server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                process_request=self.process_request
            )
            logging.info(f"server listening on {self.host}:{self.port}")
            logging.info("Relay server started on port 8765")
            logging.info(f"Log file location: {Path(os.getcwd()) / 'relay.log'}")
            await server.wait_closed()
        except Exception as e:
            logging.error(f"Error in start: {e}", exc_info=True)
            sys.exit(1)

    async def process_request(self, path, request_headers):
        """Process the HTTP request before upgrading to WebSocket."""
        try:
            host = request_headers.headers.get('Host', 'unknown')
            logging.info(f"New connection request from {host}")
        except Exception as e:
            logging.warning(f"Could not get host from headers: {e}")
        return None  # Allow the upgrade to WebSocket

    async def handle_client(self, websocket):
        """Handle a new client connection."""
        try:
            logging.info("connection open")
            
            # Wait for initial registration message
            message = await websocket.recv()
            try:
                # Parse and validate message
                data = json.loads(message)
                client_type = data.get("client_type")
                
                if client_type == "django":
                    # Validate Django token
                    token = data.get("token")
                    if not token:
                        logging.error("Django client missing token")
                        await websocket.close()
                        return
                        
                    if token != self.django_token:
                        logging.error("Invalid Django token")
                        await websocket.close()
                        return
                        
                    logging.info("Django client connected")
                    self.django_client = websocket
                    
                    # Send auth success response
                    await websocket.send(json.dumps({"type": "auth_success"}))
                    logging.info("Sent auth success response")
                    
                    # Handle messages from Django client
                    try:
                        async for message in websocket:
                            await self.relay_message(message, "django")
                    except websockets.exceptions.ConnectionClosed:
                        logging.info("Django client disconnected")
                    finally:
                        self.django_client = None
                    
                elif client_type == "agent":
                    # Validate agent token
                    token = data.get("token")
                    if not token:
                        logging.error("Agent missing token")
                        await websocket.close()
                        return
                        
                    if token != self.agent_token:
                        logging.error("Invalid agent token")
                        await websocket.close()
                        return
                        
                    hostname = data.get("hostname")
                    if not hostname:
                        logging.error("Agent missing hostname")
                        await websocket.close()
                        return
                        
                    logging.info(f"Agent connected from {hostname}")
                    self.clients[hostname] = websocket
                    
                    # Send auth success response
                    await websocket.send(json.dumps({"type": "auth_success"}))
                    logging.info("Sent auth success response")
                    
                    # Handle messages from agent
                    try:
                        async for message in websocket:
                            await self.relay_message(message, "agent", hostname, websocket)
                    except websockets.exceptions.ConnectionClosed:
                        logging.info(f"Agent {hostname} disconnected")
                    finally:
                        if hostname in self.clients:
                            del self.clients[hostname]
                    
                else:
                    logging.error(f"Unknown client type: {client_type}")
                    await websocket.close()
                    return
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in registration message: {e}")
                logging.debug(f"Raw message: {message[:100]}...")  # Log first 100 chars
                await websocket.close()
                
        except Exception as e:
            logging.error(f"Error handling client: {e}", exc_info=True)
            await websocket.close()

    async def relay_message(self, message: str, source_type: str, hostname: str = None, websocket=None) -> None:
        """Relay a message between clients."""
        try:
            message_data = json.loads(message)
            message_type = message_data.get("type")
            
            if not message_type:
                logging.error("Message missing 'type' field")
                logging.debug(f"Received data: {message[:100]}...")  # Log first 100 chars
                return
            
            if source_type == "django":
                # Relay from Django to agent
                target_hostname = message_data.get("target_hostname") or hostname
                if not target_hostname:
                    logging.error("No target hostname provided for Django message")
                    return
                    
                if target_hostname in self.clients:
                    await self.clients[target_hostname].send(message)
                    logging.info(f"Relayed message to agent {target_hostname}")
                else:
                    logging.warning(f"Target agent {target_hostname} not connected")
                    
            elif source_type == "agent":
                # Relay from agent to Django
                if not self.django_client:
                    logging.warning("Django client not connected")
                    return
                    
                # Add hostname to message if not present
                if "hostname" not in message_data:
                    message_data["hostname"] = hostname
                
                try:
                    if message_type in ["system_info", "update_metrics"]:
                        # Get metrics data from message
                        cpu_info = message_data.get("cpu", {})
                        memory_info = message_data.get("memory", {})
                        disk_info = message_data.get("disk", {})
                        system_info = message_data.get("system", {})
                        
                        # Get client IP address from websocket connection
                        ip_address = websocket.remote_address[0]
                        
                        # Log the received metrics
                        logging.info(f"Received metrics from {hostname} ({ip_address}):")
                        logging.info(f"CPU: {json.dumps(cpu_info, indent=2)}")
                        logging.info(f"Memory: {json.dumps(memory_info, indent=2)}")
                        logging.info(f"Disk: {json.dumps(disk_info, indent=2)}")
                        logging.info(f"System: {json.dumps(system_info, indent=2)}")
                        
                        # Forward to Django exactly as received
                        await self.django_client.send(json.dumps({
                            "type": "update_computer",
                            "hostname": hostname,
                            "data": {
                                "label": hostname,
                                "hostname": hostname,
                                "ip_address": ip_address,  # Add IP address
                                "os_version": system_info.get("os_version"),
                                "model": cpu_info.get("model"),
                                "logged_in_user": system_info.get("logged_in_user"),
                                "last_seen": datetime.now().isoformat(),
                                "last_metrics_update": datetime.now().isoformat(),
                                "metrics": {
                                    "cpu": cpu_info,
                                    "memory": memory_info,
                                    "disk": disk_info,
                                    "system": system_info
                                },
                                "status": "online"
                            }
                        }))
                        logging.info(f"Forwarded metrics update for {hostname} to Django")
                        
                    else:
                        # Pass through other message types
                        await self.django_client.send(message)
                        logging.info(f"Relayed {message_type} message from {hostname}")
                        
                except Exception as e:
                    logging.error(f"Failed to relay message: {e}", exc_info=True)
                    
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in message: {e}")
            logging.debug(f"Raw message: {message[:100]}...")  # Log first 100 chars
            
        except Exception as e:
            logging.error(f"Error relaying message: {e}", exc_info=True)

def main():
    server = RelayServer()
    asyncio.run(server.start())

if __name__ == "__main__":
    main()
