import asyncio
import websockets
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def capture_relay_data():
    uri = "ws://192.168.72.19:8765"
    output_file = Path(__file__).parent / "relay_data_all.json"
    all_messages = []
    
    try:
        logger.debug(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to relay server")
            
            # Simplified registration as Django client
            reg_message = {
                "type": "register",
                "client_type": "django",
                "token": "django_client"
            }
            
            logger.debug(f"Sending registration: {reg_message}")
            await websocket.send(json.dumps(reg_message))
            
            response = await websocket.recv()
            logger.info(f"Registration response: {response}")
            
            while True:
                logger.debug("Waiting for next message...")
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30)
                    logger.info(f"Raw message received: {message[:200]}...")  # First 200 chars
                    
                    data = json.loads(message)
                    data['capture_timestamp'] = datetime.now().isoformat()
                    all_messages.append(data)
                    
                    # Log message details
                    msg_type = data.get('type', 'unknown')
                    logger.info(f"Message type: {msg_type}")
                    
                    if msg_type == 'metrics':
                        hostname = data.get('hostname', 'unknown')
                        user = data.get('logged_in_user', 'none')
                        logger.info(f"Metrics from {hostname}, user: {user}")
                    
                    # Save to file
                    with open(output_file, 'w') as f:
                        json.dump(all_messages, f, indent=2)
                        
                except asyncio.TimeoutError:
                    logger.debug("No message received in 30 seconds")
                    continue
                    
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"WebSocket connection closed: {e}")
    except Exception as e:
        logger.error(f"Connection error: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(capture_relay_data())
    except KeyboardInterrupt:
        logger.info("Capture stopped by user")
    except Exception as e:
        logger.error(f"Main error: {e}", exc_info=True)