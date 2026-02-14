# Docker Deployment Guide

Manufacturing AI Copilot services are fully containerized and deployed using Docker Compose.

## Architecture

The Docker deployment includes:

- **PostgreSQL 15**: Persistent database (port 5432)
- **Redis 7**: Cache layer (port 6379)
- **5 Microservices**: Each running in its own container
  - Data Ingest Service (port 8001)
  - Unified Data Service (port 8002)
  - AI Runtime Service (port 8003)
  - Forecast Service (port 8004)
  - Notification Service (port 8005)

## Quick Start

### Prerequisites

- Docker Desktop installed and running
- 4GB+ available RAM
- Ports 5432, 6379, 8001-8005 available

### Start All Services

```bash
# Navigate to project root
cd d:\Programming\Python\OpsCopilot

# Build and start all containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Verify Services

Check that all containers are healthy:

```bash
# List all containers
docker ps

# Test individual service health endpoints
curl http://localhost:8001/api/v1/health  # Data Ingest
curl http://localhost:8002/api/v1/health  # Unified Data
curl http://localhost:8003/api/v1/health  # AI Runtime
curl http://localhost:8004/api/v1/health  # Forecast
curl http://localhost:8005/api/v1/health  # Notification
```

All endpoints should return HTTP 200 status.

## Environment Configuration

Services use the following environment variables (configured in `docker-compose.yml`):

```env
# Database
DB_USER=copilot_user
DB_PASSWORD=copilot_password
DB_HOST=postgres
DB_PORT=5432
DB_NAME=copilot_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO
```

## Database Setup

PostgreSQL automatically initializes with:
- User: `copilot_user`
- Database: `copilot_db`
- Schemas: `staging`, `manufacturing`, `forecast`, `notifications`, `ai_runtime`

On first startup, services will:
1. Connect to PostgreSQL
2. Create required tables and schemas
3. Initialize Redis connection

## Managing Containers

### View logs for a specific service

```bash
docker-compose logs -f data-ingest
docker-compose logs -f forecast
# etc.
```

### Restart a service

```bash
docker-compose restart data-ingest
```

### Remove all containers and volumes

```bash
docker-compose down -v
```

### Build images without starting

```bash
docker-compose build
```

## Performance & Production

### Recommended Settings for Production

Update `docker-compose.yml`:

```yaml
services:
  postgres:
    # Add persistent backup volume
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    # Add resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  # Similar limits for each service
  data-ingest:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

### Enable Docker Log Rotation

Update service in `docker-compose.yml`:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Monitoring

Check resource usage:

```bash
docker stats copilot_postgres copilot_redis copilot_data_ingest
```

## Troubleshooting

### Services fail to start

Check logs:
```bash
docker-compose logs data-ingest
```

Common issues:
- Port already in use: Change port mappings in `docker-compose.yml`
- Database connection error: Ensure PostgreSQL container is healthy (`docker ps`)
- Out of memory: Reduce replica count or increase system resources

### Database connection errors

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check database connectivity
docker exec copilot_postgres psql -U copilot_user -d copilot_db -c "SELECT 1"
```

### Clear all data and restart fresh

```bash
docker-compose down -v
docker-compose up -d
```

## Images Built

The following Docker images are built and deployed:

- `opscopilot-data-ingest:latest`
- `opscopilot-unified-data:latest`
- `opscopilot-ai-runtime:latest`
- `opscopilot-forecast:latest`
- `opscopilot-notification:latest`

Images are built from Dockerfiles in each service directory:
- `services/data-ingest-service/Dockerfile`
- `services/unified-data-service/Dockerfile`
- `services/ai-runtime-service/Dockerfile`
- `services/forecast-service/Dockerfile`
- `services/notification-service/Dockerfile`

## Network

All services communicate on a Docker network named `copilot_network`. Inter-service communication uses container names as hostnames (e.g., `postgres`, `redis`).

## Data Persistence

Data is persisted in Docker volumes:
- `postgres_data`: PostgreSQL data directory
- `redis_data`: Redis persistence files

These volumes survive container restarts but are deleted with `docker-compose down -v`.
