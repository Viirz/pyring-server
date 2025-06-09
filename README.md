# Pyring Server

A secure agent management system built with Flask that provides centralized control and monitoring of distributed agents through encrypted communication channels.

## Overview

Pyring Server is a web-based command and control platform designed for managing remote agents with enterprise-grade security features. The system uses PGP encryption for all agent communications and provides a modern web interface for agent management, command execution, and monitoring.

## Features

### 🔐 Security
- **PGP Encryption**: All agent communications are encrypted and signed using RSA-2048 PGP keys
- **JWT Authentication**: Secure user authentication with token-based sessions
- **Password Hashing**: Argon2 password hashing for user accounts
- **Request Validation**: Input sanitization and validation for all endpoints

### 👥 Agent Management
- **Agent Registration**: Automated agent onboarding with unique UUID assignment
- **Key Management**: Automatic PGP keypair generation for each agent
- **Status Monitoring**: Real-time agent health and connectivity tracking
- **Command Execution**: Secure remote command execution with encrypted responses

### 📊 Dashboard
- **Web Interface**: Modern, responsive dashboard for agent management
- **Real-time Status**: Live agent status updates (OK, Unreachable, Recovery)
- **Agent Details**: Detailed view of individual agent information
- **Filtering**: Filter agents by status for quick management

### 🔧 System Features
- **MongoDB Integration**: Robust data storage for agents, users, and logs
- **Scheduled Tasks**: Background job scheduling with APScheduler
- **Logging**: Comprehensive logging system for audit trails
- **Docker Support**: Containerized deployment with Docker Compose

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │  Pyring         │    │   Remote        │
│                 │◄──►│    Server       │◄──►│   Agents        │
│   Dashboard     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │    MongoDB      │
                       │   Database      │
                       └─────────────────┘
```

## Technology Stack

- **Backend**: Python 3.12 + Flask
- **WSGI Server**: Gunicorn (production) / Flask dev server (development)
- **Database**: MongoDB 4.0.8
- **Encryption**: GnuPG with python-gnupg
- **Authentication**: JWT + Argon2
- **Frontend**: HTML5, CSS3, JavaScript
- **Containerization**: Docker + Docker Compose
- **Scheduling**: APScheduler

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Task_Force/server
   ```

2. **Run the installation script**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

   This will:
   - Build the Docker containers
   - Generate server PGP keys
   - Start the MongoDB database
   - Launch the Flask application

3. **Access the application**
   - Open your browser and navigate to `http://localhost:5000`
   - Create your first user account (registration required on first run)

### Manual Setup

If you prefer manual installation:

```bash
# Build and start containers
docker compose up -d --build

# Check container status
docker compose ps

# View logs
docker compose logs -f flask
```

## Configuration

### Environment Variables

The application uses the following environment variables (configured in `docker-compose.yml`):

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_GUNICORN` | Use Gunicorn WSGI server | `true` |
| `MONGODB_DATABASE` | Database name | `flaskdb` |
| `MONGODB_USERNAME` | Database username | `mongodbuser` |
| `MONGODB_PASSWORD` | Database password | `mongo123` |
| `MONGODB_HOSTNAME` | Database hostname | `mongodb` |
| `JWT_SECRET` | JWT signing secret | `supersecure123` |

### Security Considerations

⚠️ **Important**: Before deploying to production:

1. Change the default MongoDB credentials
2. Generate a new JWT secret key
3. Use HTTPS/TLS for web traffic
4. Implement proper firewall rules
5. Regular backup of PGP keys and database

## API Documentation

### Authentication Endpoints

- `POST /api/users/register` - Register new user (first user only)
- `POST /api/users/login` - User login
- `POST /api/users/logout` - User logout
- `POST /api/users/change_password` - Change user password

### Agent Management

- `POST /api/agents/` - Create new agent
- `GET /api/agents/<uuid>/command` - Get pending commands for agent
- `POST /api/agents/<uuid>/command` - Send command to agent

### Agent Communication

- `POST /agents` - Agent status updates and command responses
- `POST /logs` - Agent log submissions

### Web Routes

- `/` - Home/Registration page
- `/login` - Login page
- `/dashboard` - Main dashboard
- `/agent/<uuid>` - Agent detail page
- `/account` - Account management

## Agent Communication Protocol

Agents communicate with the server using encrypted PGP messages:

1. **Agent Registration**: Server generates unique UUID and PGP keypair
2. **Status Updates**: Agents send encrypted status (codes 1, 2, 5, 6)
3. **Command Retrieval**: Agents request pending commands (status 5)
4. **Command Response**: Agents submit command results (status 6)
5. **Log Submission**: Agents send system logs via `/logs` endpoint

### Status Codes

- `1`: Agent OK
- `2`: Agent in Recovery mode
- `5`: Agent requesting commands
- `6`: Agent submitting command response

## File Structure

```
server/
├── app/
│   ├── routes/
│   │   ├── api/
│   │   │   ├── agents_api.py      # Agent API endpoints
│   │   │   └── users_api.py       # User API endpoints
│   │   ├── agents_routes.py       # Agent communication
│   │   ├── logs_routes.py         # Log handling
│   │   └── web_routes.py          # Web interface
│   ├── services/
│   │   └── db_service.py          # Database operations
│   ├── static/                    # CSS, JS, images
│   ├── template/                  # HTML templates
│   ├── utils/
│   │   ├── agent_utils.py         # Agent utilities
│   │   ├── jwt_utils.py           # JWT handling
│   │   ├── pgp_utils.py           # PGP operations
│   │   ├── request_utils.py       # Input validation
│   │   └── scheduler.py           # Task scheduling
│   ├── Dockerfile
│   ├── main.py                    # Application entry point
│   └── requirements.txt
├── docker-compose.yml
├── install.sh
├── uninstall.sh
└── README.md
```

## Development

### Running in Development Mode

The server can run in two modes: **production** (using Gunicorn WSGI server) or **development** (using Flask's built-in server).

#### For Development with Flask's Built-in Server

1. **Modify environment variables** in `docker-compose.yml`:
   ```yaml
   environment:
     USE_GUNICORN: "false"
     APP_ENV: "dev"
     APP_DEBUG: "True"
   ```

2. **Rebuild and restart**:
   ```bash
   docker compose down
   docker compose up -d --build
   ```

#### For Production with Gunicorn (Default)

1. **Keep default environment variables** in `docker-compose.yml`:
   ```yaml
   environment:
     USE_GUNICORN: "true"
     APP_ENV: "prod"
     APP_DEBUG: "False"
   ```

2. **Start the application**:
   ```bash
   docker compose up -d --build
   ```

### Server Configuration

- **Gunicorn Mode** (`USE_GUNICORN=true`): 
  - Uses 4 worker processes
  - 120-second timeout
  - Optimized for production workloads
  - Better performance and stability

- **Flask Development Mode** (`USE_GUNICORN=false`):
  - Single-threaded Flask development server
  - Easier debugging and development
  - Auto-reloading on code changes (when debug=True)

### Adding New Features

1. Create new routes in appropriate blueprint files
2. Add database operations to `db_service.py`
3. Update templates and static files as needed
4. Test with encrypted agent communication

## Troubleshooting

### Common Issues

**Container won't start**
```bash
# Check logs
docker compose logs flask

# Restart containers
docker compose restart
```

**PGP key issues**
```bash
# Rebuild with fresh keys
docker compose down --rmi all -v
docker compose up -d --build
```

**Database connection errors**
```bash
# Check MongoDB status
docker compose logs mongodb

# Verify network connectivity
docker compose exec flask ping mongodb
```

**Port conflicts**
```bash
# Check if port 5000 is in use
sudo netstat -tulpn | grep :5000

# Stop conflicting services or change port in docker-compose.yml
```

## Security Best Practices

1. **Regular Updates**: Keep dependencies updated
2. **Key Rotation**: Periodically rotate PGP keys
3. **Access Control**: Limit dashboard access to authorized users
4. **Monitoring**: Monitor agent communications for anomalies
5. **Backup**: Regular backup of database and key materials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Cleanup

To completely remove the installation:

```bash
./uninstall.sh
```

This will stop containers, remove images, and clean up volumes.

## Monitoring Agents

For setting up the monitoring agents that communicate with this server, see: [Pyring Agent Repository](https://github.com/placeholder/pyring-agent)

## License

[Add your license information here]

## Support

[Add support contact information here]
