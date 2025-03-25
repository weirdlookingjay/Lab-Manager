# Lab Manager

A distributed system for monitoring and managing computers in a lab environment. The system consists of three main components: Computer Agent, Relay Server, and Django Backend with React Frontend.

## System Architecture

```
┌─────────────┐     WebSocket     ┌──────────────┐      HTTP      ┌──────────────┐
│ Computer    │<----------------->│    Relay     │<-------------->│    Django    │
│   Agent     │     Connection    │    Server    │      API       │   Backend    │
└─────────────┘                   └──────────────┘                └──────────────┘
                                                                        ↑
                                                                        │
                                                                        │ HTTP/API
                                                                        ↓
                                                                 ┌──────────────┐
                                                                 │    React     │
                                                                 │   Frontend   │
                                                                 └──────────────┘
```

## Components

### 1. Computer Agent

The Computer Agent is a Python application that runs on each monitored computer. It:

- Collects system metrics (CPU, Memory, Disk usage, etc.)
- Reports system information (OS version, uptime, network status)
- Maintains a WebSocket connection to the Relay Server
- Executes commands received from the server
- Provides real-time updates about the computer's status

Key features:
- Real-time system monitoring
- Secure WebSocket communication
- Command execution capabilities
- Automatic reconnection handling
- System metrics collection using psutil

### 2. Relay Server

The Relay Server acts as an intermediary between Computer Agents and the Django Backend. It:

- Manages WebSocket connections from multiple Computer Agents
- Routes messages between Agents and the Django Backend
- Maintains connection state and handles reconnections
- Provides real-time message routing
- Authenticates agents and the Django client

Key features:
- WebSocket server implementation
- Message routing and queueing
- Connection state management
- Security token validation
- Real-time bidirectional communication

### 3. Django Backend

The Django Backend provides the API and business logic layer. It:

- Stores computer information and metrics in a database
- Provides REST API endpoints for the frontend
- Manages user authentication and authorization
- Processes and validates incoming data
- Handles business logic and data persistence

Key features:
- REST API endpoints
- Database management
- User authentication
- Data validation and processing
- Business logic implementation

### 4. React Frontend

The React Frontend provides the user interface. It:

- Displays real-time computer metrics
- Shows system information in an organized layout
- Provides interactive controls for managing computers
- Updates automatically as new data arrives
- Offers a responsive and modern UI

Key features:
- Real-time metric updates
- Responsive design
- Modern UI components
- WebSocket integration
- Interactive data visualization

## Data Flow

1. Computer Agent collects system metrics and information
2. Agent sends data to Relay Server via WebSocket
3. Relay Server forwards data to Django Backend
4. Django Backend processes and stores the data
5. Frontend retrieves data through Django API
6. UI updates in real-time with new information

## Security

- WebSocket connections are authenticated using tokens
- API endpoints require authentication
- Sensitive data is encrypted in transit
- Access control is managed through Django
- Agents validate server identity

## Setup and Installation

[Add installation instructions here]

## Configuration

[Add configuration details here]

## Development

[Add development setup instructions here]

## Contributing

[Add contribution guidelines here]

## License

[Add license information here]
