# Docker Setup for Hetzner Auction Matrix Bot

This guide explains how to run the Hetzner Auction Matrix Bot using Docker and Docker Compose.

## Prerequisites

- Docker and Docker Compose installed on your system
- A Matrix account for your bot
- A Matrix room where notifications will be sent

## Quick Start

1. **Clone the repository and navigate to the project directory:**
   ```bash
   git clone <repository-url>
   cd hetzner-auction-matrix-bot
   ```

2. **Create environment configuration:**
   ```bash
   cp .env.example .env
   ```

3. **Edit the `.env` file with your configuration:**
   ```env
   # Matrix Bot Configuration
   MATRIX_HOMESERVER=https://matrix.org
   MATRIX_USERNAME=@your_bot:matrix.org
   MATRIX_PASSWORD=your_matrix_bot_password
   HETZNER_NOTIFICATIONS_ROOM_ID=!your_room_id:matrix.org
   
   # MongoDB Configuration
   MONGO_ROOT_PASSWORD=your_secure_password
   ```

4. **Start the services:**
   ```bash
   docker-compose up -d
   ```

5. **Check the logs:**
   ```bash
   docker-compose logs -f hetzner-bot
   ```

## Configuration Details

### Matrix Configuration

1. **Create a Matrix account for your bot:**
   - Register a new account on your Matrix homeserver
   - Note the username and password

2. **Get the room ID:**
   - Create or join a Matrix room where you want notifications
   - The room ID looks like `!room_id:matrix.org`
   - You can find it in the room settings or by using a Matrix client

3. **Invite your bot to the room:**
   - Invite your bot account to the notification room
   - Make sure the bot has permission to send messages

### MongoDB Configuration

The MongoDB service is automatically configured with:
- A root user with admin privileges
- A dedicated `hetzner` database
- A `hetzner_bot` user with read/write access to the database
- Proper indexes for optimal performance

## Docker Services

### hetzner-bot
- **Image:** Built from the local Dockerfile
- **Purpose:** Runs the Matrix bot application
- **Dependencies:** Waits for MongoDB to be healthy before starting
- **Health Check:** Basic Python import test

### mongodb
- **Image:** mongo:7.0
- **Purpose:** Stores user configurations and monitoring data
- **Data Persistence:** Uses Docker volume `mongodb_data`
- **Health Check:** MongoDB ping command

## Management Commands

### Start the services:
```bash
docker-compose up -d
```

### Stop the services:
```bash
docker-compose down
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f hetzner-bot
docker-compose logs -f mongodb
```

### Restart a service:
```bash
docker-compose restart hetzner-bot
```

### Update the bot:
```bash
docker-compose down
docker-compose build --no-cache hetzner-bot
docker-compose up -d
```

### Access MongoDB directly:
```bash
docker-compose exec mongodb mongosh -u admin -p
```

## Data Persistence

- **MongoDB data:** Stored in the `mongodb_data` Docker volume
- **Bot logs:** Optional volume mount at `./logs` (create the directory first)

## Security Considerations

1. **Change default passwords:** Update `MONGO_ROOT_PASSWORD` in your `.env` file
2. **Network isolation:** Services communicate through a dedicated Docker network
3. **Non-root user:** The bot runs as a non-root user inside the container
4. **Environment variables:** Sensitive data is passed via environment variables, not hardcoded

## Troubleshooting

### Bot won't start:
1. Check the logs: `docker-compose logs hetzner-bot`
2. Verify your Matrix credentials in the `.env` file
3. Ensure the bot account is invited to the notification room

### MongoDB connection issues:
1. Check MongoDB logs: `docker-compose logs mongodb`
2. Verify the MongoDB URI in the bot logs
3. Ensure MongoDB is healthy: `docker-compose ps`

### Permission issues:
1. Make sure the `logs` directory exists and is writable
2. Check file permissions in the project directory

## Production Deployment

For production deployment, consider:

1. **Use Docker secrets** for sensitive data instead of environment variables
2. **Set up proper logging** with log rotation
3. **Configure monitoring** and alerting
4. **Use a reverse proxy** if exposing services externally
5. **Regular backups** of the MongoDB data volume
6. **Resource limits** in the docker-compose.yml file

## Backup and Restore

### Backup MongoDB data:
```bash
docker-compose exec mongodb mongodump --db hetzner --out /data/backup
docker cp hetzner-bot-mongodb:/data/backup ./mongodb-backup
```

### Restore MongoDB data:
```bash
docker cp ./mongodb-backup hetzner-bot-mongodb:/data/backup
docker-compose exec mongodb mongorestore --db hetzner /data/backup/hetzner
```