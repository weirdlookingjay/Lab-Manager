# Computer Management Relay Server

This service enables communication between the Django backend and remote computer agents across different network segments.

## Installation

1. Clone the repository
2. Create and configure the environment:
   ```bash
   # Copy environment template
   copy .env.template .env
   
   # Edit .env with your settings:
   # - RELAY_URL: WebSocket URL for the relay server
   # - COMPUTER_AGENT_TOKEN: Authentication token
   ```

3. Run the setup script:
   ```bash
   setup_relay.bat
   ```

## Development

1. Activate the virtual environment:
   ```bash
   .\relay_env\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Service Management

The relay server runs as a Windows service named "RelayServer". You can manage it using NSSM:

```bash
# Check status
nssm status RelayServer

# Start service
nssm start RelayServer

# Stop service
nssm stop RelayServer

# Remove service
nssm remove RelayServer confirm
```

## Logs

Service logs are written to `relay.log` in the installation directory.

## Security

- The relay server uses token-based authentication
- Communication is done via WebSocket
- Firewall rules are automatically configured for port 8765
- Service runs under LocalSystem account for proper permissions
