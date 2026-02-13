# Manufacturing AI Copilot - Microservices Platform

Production-grade microservices platform for Manufacturing AI with clean architecture, domain-driven design, and async Python.

## Platform Overview

This platform provides a manufacturing AI copilot system with the following capabilities:

- **Data Ingestion**: Ingest ERP, accounting, and manufacturing data
- **Data Normalization**: Transform raw data into unified manufacturing schema
- **AI Runtime**: Execute ML models for insights and recommendations
- **Forecasting**: Generate demand, inventory, supply, and quality forecasts
- **Notifications**: Multi-channel alert delivery system

## Architecture

### Service Topology

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (Future)                      │
└─────────────────────────────────────────────────────────────┘
          │         │          │           │          │
          ↓         ↓          ↓           ↓          ↓
    ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
    │ Data    │ │Unified │ │   AI   │ │Forecast│ │Notif.   │
    │ Ingest  │ │ Data   │ │Runtime │ │Service │ │Service  │
    └─────────┘ └────────┘ └────────┘ └────────┘ └──────────┘
          │         │          │           │          │
          └─────────┴──────────┴───────────┴──────────┘
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
      PostgreSQL    Redis       Message Queue
```

### Each Service Architecture (Clean)

```
┌─────────────────────────────────────┐
│         API Layer (Routes)           │
├─────────────────────────────────────┤
│     Application Layer (Services)     │
├─────────────────────────────────────┤
│    Domain Layer (Models, Repos)      │
├─────────────────────────────────────┤
│   Infrastructure (DB, Logger, etc)   │
└─────────────────────────────────────┘
```

## Services

### 1. Data Ingest Service (Port 8001)

Ingests raw data from external systems.

**Key Features:**
- Support for ERP, accounting, inventory, and sales data
- Batch ingestion with reference tracking
- Automatic duplicate detection
- Status tracking (pending, processing, success, failed)
- Audit trail for data modifications

**API Endpoints:**
- `POST /api/v1/ingest` - Ingest data batch
- `GET /api/v1/batch/{batch_id}` - Get batch status
- `GET /api/v1/health` - Health check

**Database Models:**
- `RawDataBatches` - Raw data batches
- `PriMasterAudits` - Audit trail

### 2. Unified Data Service (Port 8002)

Normalizes and transforms data into unified schema.

**Key Features:**
- Manufacturing item normalization
- Process definition management
- Inventory snapshot tracking
- External system mapping
- Historical data preservation

**API Endpoints:**
- `POST /api/v1/items` - Create/update manufacturing item
- `GET /api/v1/items/{sku}` - Get item by SKU
- `GET /api/v1/inventory/{item_id}` - Get inventory snapshot
- `GET /api/v1/health` - Health check

**Database Models:**
- `ManufacturingItems` - Normalized items
- `ManufacturingProcesses` - Process definitions
- `InventorySnapshots` - Inventory tracking

### 3. AI Runtime Service (Port 8003)

Manages AI/ML model execution and inference.

**Key Features:**
- Model registration and versioning
- Async inference execution
- Execution tracking and metrics
- Mock inference for testing
- Extensible for real ML models

**API Endpoints:**
- `POST /api/v1/infer` - Run inference
- `GET /api/v1/health` - Health check

**Database Models:**
- `AIModels` - Model definitions
- `InferenceJobs` - Inference execution records

### 4. Forecast Service (Port 8004)

Generates forecasts for manufacturing entities.

**Key Features:**
- Multi-type forecasting (demand, inventory, supply, quality)
- Time-period based forecasting (daily, weekly, monthly, quarterly)
- Confidence intervals and bounds
- Alert generation from forecasts
- Mock forecasting for testing

**API Endpoints:**
- `POST /api/v1/forecasts` - Generate forecast
- `GET /api/v1/forecasts/{entity_id}/{forecast_type}` - Get forecast
- `GET /api/v1/alerts/active` - Get active alerts
- `GET /api/v1/health` - Health check

**Database Models:**
- `Forecasts` - Forecast predictions
- `ForecastAlerts` - Generated alerts

### 5. Notification Service (Port 8005)

Sends multi-channel notifications and alerts.

**Key Features:**
- Multi-channel delivery (email, SMS, Slack, webhook)
- User notification preferences
- Notification templates
- Delivery tracking
- Severity-based filtering

**API Endpoints:**
- `POST /api/v1/send` - Send notification
- `POST /api/v1/preferences` - Set user preferences
- `GET /api/v1/health` - Health check

**Database Models:**
- `Notifications` - Sent notifications
- `NotificationPreferences` - User preferences
- `NotificationTemplates` - Message templates

## Tech Stack

### Core Framework
- **Python 3.11+** - Language
- **FastAPI 0.104+** - Web framework
- **Uvicorn 0.24+** - ASGI server
- **Pydantic v2** - Data validation

### Database & ORM
- **PostgreSQL 15** - Relational database
- **SQLAlchemy 2.0+** - Async ORM
- **asyncpg 0.29+** - PostgreSQL async driver
- **Alembic** - Database migrations

### Infrastructure
- **Redis 7** - Caching and queues
- **Docker** - Containerization
- **Docker Compose** - Local orchestration
- **Kubernetes ready** - For production deployment

### Development & Testing
- **pytest 7.4+** - Testing framework
- **pytest-asyncio** - Async test support
- **httpx** - Async HTTP client
- **black** - Code formatting
- **mypy** - Type checking
- **flake8** - Linting

## Project Structure

```
OpsCopilot/
├── shared/                          # Shared modules
│   ├── __init__.py
│   ├── config.py                   # Configuration management
│   ├── domain_models.py            # Base domain classes
│   ├── database.py                 # Database manager
│   ├── logger.py                   # Structured logging
│   ├── repository.py               # Base repository pattern
│   └── requirements.txt            # Shared dependencies
│
├── services/
│   ├── data-ingest-service/
│   │   ├── app/
│   │   │   ├── domain/             # Domain layer
│   │   │   ├── application/        # Application/service layer
│   │   │   ├── infrastructure/     # Infrastructure code
│   │   │   ├── api/                # HTTP routes
│   │   │   ├── config.py
│   │   │   └── main.py             # FastAPI app
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── main.py
│   │
│   ├── unified-data-service/       # Similar structure
│   ├── ai-runtime-service/         # Similar structure
│   ├── forecast-service/           # Similar structure
│   └── notification-service/       # Similar structure
│
├── docker-compose.yml              # Local orchestration
├── .env.example                    # Environment template
└── README.md                       # This file
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (if running locally)
- Redis 7+ (if running locally)

### Quick Start with Docker Compose

```bash
# Clone the repository
git clone <repository>
cd OpsCopilot

# Start all services
docker-compose up -d

# Verify services are healthy
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install shared dependencies
pip install -r shared/requirements.txt

# Install service-specific dependencies
pip install -r services/data-ingest-service/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run service
python services/data-ingest-service/main.py

# Run tests
pytest services/data-ingest-service/tests/
```

## API Examples

### Ingest Data

```bash
curl -X POST http://localhost:8001/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "erp",
    "source_id": "erp_001",
    "batch_reference": "batch_20240101_001",
    "data": {
      "items": [
        {"sku": "ITEM-001", "name": "Component A", "qty": 100}
      ]
    }
  }'
```

### Create Manufacturing Item

```bash
curl -X POST http://localhost:8002/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "ITEM-001",
    "name": "Component A",
    "uom": "EA",
    "standard_cost": 50.00,
    "supplier_name": "Supplier X"
  }'
```

### Generate Forecast

```bash
curl -X POST http://localhost:8004/api/v1/forecasts \
  -H "Content-Type: application/json" \
  -d '{
    "forecast_type": "demand",
    "period": "monthly",
    "entity_id": "ITEM-001",
    "entity_type": "item",
    "lookback_days": 365
  }'
```

### Send Notification

```bash
curl -X POST http://localhost:8005/api/v1/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "title": "Inventory Alert",
    "message": "Stock level critical for ITEM-001",
    "notification_type": "alert",
    "severity": "critical",
    "channel": "email"
  }'
```

## Environment Configuration

Create `.env` file:

```env
# Database
DB_USER=copilot_user
DB_PASSWORD=copilot_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=copilot_db
DB_ECHO=false

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Service
SERVICE_NAME=data-ingest-service
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

## Clean Architecture Principles

### Domain Layer
- Pure business logic
- No external dependencies
- Entities, value objects, repositories
- Domain-driven design

### Application Layer
- Use cases and workflows
- Orchestrates domain objects
- Service classes
- No business logic

### Infrastructure Layer
- Database access
- External service calls
- Logging, configuration
- Technical details

### API Layer
- HTTP request/response handling
- Route definitions
- Request/response serialization
- Error handling

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific service tests
pytest services/data-ingest-service/tests/

# Run async tests
pytest -v -s services/data-ingest-service/tests/
```

## Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Kubernetes Deployment (Future)

Each service is designed for Kubernetes deployment:

```yaml
# Example Kubernetes manifest
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-ingest-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-ingest
  template:
    metadata:
      labels:
        app: data-ingest
    spec:
      containers:
      - name: data-ingest
        image: data-ingest-service:1.0.0
        ports:
        - containerPort: 8001
        env:
        - name: DB_HOST
          value: postgres-service
        - name: REDIS_HOST
          value: redis-service
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Monitoring & Observability

### Logging
- Structured JSON logging via `python-json-logger`
- Service name, timestamp, level included
- All endpoints return JSON responses

### Health Checks
- Each service exposes `GET /api/v1/health`
- Docker HEALTHCHECK included in Dockerfiles
- Kubernetes-ready liveness probes

### Metrics (Future)
- Prometheus metrics endpoint
- Service request latency
- Database connection pool stats
- Error rates by service

## Contributing

1. Follow clean architecture principles
2. Write tests for all new features
3. Use type hints throughout
4. Format with black
5. Pass mypy type checking
6. Update documentation

## License

Proprietary - Manufacturing AI Copilot Platform

## Support

For issues and questions, contact the development team.
