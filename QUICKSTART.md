# Manufacturing AI Copilot Platform - Quick Start Guide

## Status ✅

- **Virtual Environment**: Ready (Python 3.14)
- **All Dependencies**: Installed
- **5 Microservices**: Ready to run
- **Database**: Optional (works without it for testing)

---

## Getting Started

### Option 1: Fast Start (No Database) ⚡

Perfect for testing APIs and exploring endpoints:

```bash
# This opens all 5 services in separate windows
python quick_start.py
```

Then access Swagger UI:
- **AI Runtime (Copilot)**: http://localhost:8003/docs
- **Forecast Service**: http://localhost:8004/docs
- **Notification Service**: http://localhost:8005/docs

### Option 2: Full Stack (With Database & Cache) 🐳

Complete setup with PostgreSQL and Redis:

```bash
# Start database and cache
docker-compose up -d

# Start all services (they auto-connect to Docker containers)
.\venv\Scripts\Activate.ps1
python run_services.py
```

---

## Verify Services Are Running

```bash
# Quick health check
for ($i = 8001; $i -le 8005; $i++) {
    Write-Host "Port $i: $(Invoke-RestMethod http://localhost:$i/api/v1/health | ConvertTo-Json)" -ForegroundColor Green
}
```

---

## Test the APIs

### AI Copilot Query

```bash
$query = @{
    query = "What's the current inventory?"
    session_id = "user-1"
    max_tools = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8003/api/v1/copilot/query" `
    -Method Post -Body $query -ContentType "application/json"
```

### Forecast Demand

```bash
$forecast = @{
    entity_id = "SKU-123"
    period = "weekly"
    horizon_days = 30
    lookback_days = 365
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8004/api/v1/forecast/demand" `
    -Method Post -Body $forecast -ContentType "application/json"
```

### Send Alert

```bash
$alert = @{
    user_id = "user-123"
    alert_title = "Inventory Alert"
    alert_message = "SKU below reorder point"
    severity = "high"
    channels = @("email")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8005/api/v1/notify/alert" `
    -Method Post -Body $alert -ContentType "application/json"
```

---

## Service Ports & Endpoints

| Service | Port | Swagger UI | Health |
|---------|------|-----------|--------|
| Data Ingest | 8001 | http://localhost:8001/docs | /api/v1/health |
| Unified Data | 8002 | http://localhost:8002/docs | /api/v1/health |
| **AI Runtime** | 8003 | http://localhost:8003/docs | /api/v1/health |
| **Forecast** | 8004 | http://localhost:8004/docs | /api/v1/health |
| **Notification** | 8005 | http://localhost:8005/docs | /api/v1/health |

---

## Project Structure

```
OpsCopilot/
├── venv/                          # Python virtual environment ✓
├── services/                      # 5 microservices
│   ├── data-ingest-service/       # Data ingestion module
│   ├── unified-data-service/      # Master data management
│   ├── ai-runtime-service/        # Copilot/AI engine
│   ├── forecast-service/          # Demand/risk forecasting
│   └── notification-service/      # Multi-channel alerts
├── shared/                        # Shared models & utilities
├── docker-compose.yml             # Database & cache setup
├── run_services.py                # Multi-service runner
├── quick_start.py                 # Quick start (no DB)
├── SETUP_GUIDE.md                 # Detailed setup
├── API_REFERENCE_PHASE_3.md       # API documentation
└── ARCHITECTURE_PATTERNS.md       # Design patterns
```

---

## What's Been Built

### Phase 1-2: Core Services ✅
- Data Ingest Service (connectors, transformers, jobs)
- Unified Data Service (6 models, 6 repositories)
- Shared domain models (manufacturing terminology)

### Phase 3: Advanced Features ✅
- **AI Runtime**: Copilot with isolated tools, context building, conversation memory
- **Forecast Service**: Demand forecasting + inventory risk assessment
- **Notification Service**: Multi-channel alerts (email, Slack, SMS, webhooks)

### Phase 4: Ready for Next
- Alembic migrations (database schema versioning)
- Full Docker deployment configuration
- Integration tests

---

## Environment Configuration

The `.env` file is configured for local development:

```env
DB_HOST=localhost          # Database (use Docker or local PostgreSQL)
DB_PORT=5432
DB_USER=copilot_user
DB_PASSWORD=copilot_password
DB_NAME=copilot_db
REDIS_HOST=localhost
REDIS_PORT=6379
DEBUG=true
LOG_LEVEL=INFO
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find and kill process
Get-NetTCPConnection -LocalPort 8003 | Select-Object OwningProcess
Get-Process -Id <PID> | Stop-Process -Force
```

### Database Connection Error

Use `quick_start.py` instead (doesn't require database):
```bash
python quick_start.py
```

### Virtual Environment Issues

```bash
# Reactivate venv
.\venv\Scripts\Activate.ps1

# Verify dependencies
.\venv\Scripts\python.exe -m pip list
```

---

## Next Steps

1. **Open Swagger UI**: Visit http://localhost:8003/docs
2. **Try copilot endpoint**: POST `/api/v1/copilot/query`
3. **Generate forecasts**: POST `/api/v1/forecast/demand`
4. **Send notifications**: POST `/api/v1/notify/alert`
5. **Read full docs**: See [API_REFERENCE_PHASE_3.md](API_REFERENCE_PHASE_3.md)

---

## Documentation

- **Setup Details**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **API Reference**: [API_REFERENCE_PHASE_3.md](API_REFERENCE_PHASE_3.md)
- **Architecture**: [ARCHITECTURE_PATTERNS.md](ARCHITECTURE_PATTERNS.md)
- **Completion Report**: [PHASE_3_COMPLETION_REPORT.md](PHASE_3_COMPLETION_REPORT.md)

---

**Last Updated**: February 13, 2026  
**Status**: All services ready ✅  
**Next**: Run `python quick_start.py` or `python run_services.py`


```bash
# Ingest data
curl -X POST http://localhost:8001/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "erp",
    "source_id": "erp_001",
    "batch_reference": "batch_001",
    "data": {"items": []}
  }'

# Check health
curl http://localhost:8001/api/v1/health
```

### 4. Access API Documentation

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Project Structure

```
OpsCopilot/
├── shared/                    # Shared code (config, db, logging)
├── services/
│   ├── data-ingest-service/   # Data ingestion
│   ├── unified-data-service/  # Data normalization
│   ├── ai-runtime-service/    # AI inference
│   ├── forecast-service/      # Forecasting
│   └── notification-service/  # Notifications
├── docker-compose.yml         # Service orchestration
├── README.md                  # Full documentation
├── ARCHITECTURE.md            # Architecture details
├── API_REFERENCE.md          # API documentation
└── DEVELOPMENT.md            # Development guide
```

## Key Features

### Clean Architecture
- **Domain Layer**: Business logic
- **Application Layer**: Use cases/services
- **Infrastructure Layer**: Database, logging
- **API Layer**: HTTP routes

### Design Patterns
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic encapsulation
- **Dependency Injection**: Loose coupling
- **Error Handling**: Custom exceptions

### Async/Await Throughout
- FastAPI + Uvicorn
- SQLAlchemy async
- asyncpg for PostgreSQL
- Non-blocking I/O

### Type Safety
- Pydantic v2 for validation
- Type hints everywhere
- mypy compatible

### Testing Ready
- pytest with async support
- In-memory SQLite for tests
- Mocking support
- Unit tests for each service

## Architecture Diagram

```
External Data Sources (ERP, Accounting)
            ↓
    [Data Ingest Service] → Validates & Queues
            ↓
PostgreSQL (raw_data_batches)
            ↓
    [Unified Data Service] → Normalizes
            ↓
PostgreSQL (manufacturing_items, inventory)
            ↓
    [AI Runtime Service] → Inference
            ↓
    [Forecast Service] → Predictions
            ↓
    [Notification Service] → Alerts
            ↓
    End Users (Email, Slack, SMS)
```

## Development

### Run Single Service Locally

```bash
# Setup Python environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r shared/requirements.txt
pip install -r services/data-ingest-service/requirements.txt

# Configure environment
cp .env.example .env

# Start PostgreSQL and Redis with Docker
docker-compose up -d postgres redis

# Run service
python services/data-ingest-service/main.py
```

### Run Tests

```bash
pytest services/data-ingest-service/tests/ -v
```

## API Examples

### Ingest Manufacturing Data

```bash
curl -X POST http://localhost:8001/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "erp",
    "source_id": "sap_001",
    "batch_reference": "SAP_20240115_001",
    "data": {
      "items": [
        {"sku": "COMP-001", "name": "Bearing", "qty": 1000}
      ]
    }
  }'
```

### Create Manufacturing Item

```bash
curl -X POST http://localhost:8002/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "COMP-001",
    "name": "Bearing",
    "uom": "EA",
    "standard_cost": 25.50,
    "supplier_name": "TechParts Inc"
  }'
```

### Generate Forecast

```bash
curl -X POST http://localhost:8004/api/v1/forecasts \
  -H "Content-Type: application/json" \
  -d '{
    "forecast_type": "demand",
    "period": "monthly",
    "entity_id": "COMP-001",
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
    "title": "Critical Inventory Alert",
    "message": "Stock level below reorder point",
    "notification_type": "alert",
    "severity": "critical",
    "channel": "email"
  }'
```

## Database Schema

### Key Tables

```
raw_data_batches          → Ingested data from external systems
manufacturing_items       → Normalized item master
inventory_snapshots       → Current inventory levels
ai_models                 → Registered ML models
inference_jobs            → Model execution records
forecasts                 → Generated predictions
forecast_alerts           → Auto-generated alerts
notifications             → Sent notifications
notification_preferences  → User notification settings
```

## Configuration

### Environment Variables

```env
# Database
DB_USER=copilot_user
DB_PASSWORD=copilot_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=copilot_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO
DEBUG=true
```

## Scaling & Deployment

### Horizontal Scaling
- Each service in separate container
- Load balancer in front (nginx/traefik)
- Database connection pooling
- Redis for distributed caching

### Kubernetes Ready
- Health check endpoints
- Resource requests/limits defined
- Graceful shutdown
- Environment-based configuration

### Production Checklist
- ✅ Clean architecture
- ✅ Error handling
- ✅ Database abstraction
- ✅ Logging
- ✅ Health checks
- ⚠️ Authentication (todo)
- ⚠️ Monitoring (todo)
- ⚠️ Load testing (todo)

## Documentation Files

| File | Purpose |
|------|---------|
| [README.md](README.md) | Platform overview and setup |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Detailed architecture & design patterns |
| [API_REFERENCE.md](API_REFERENCE.md) | Complete API documentation |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Development guide & best practices |
| [CHECKLIST.md](CHECKLIST.md) | Implementation checklist |

## Support

### Troubleshooting

**Services won't start:**
```bash
# Check database is running
docker-compose logs postgres

# Check Redis is running  
docker-compose logs redis

# Restart all services
docker-compose restart
```

**Database errors:**
```bash
# Connect to database
psql -U copilot_user -d copilot_db

# Check tables
\dt
```

**Port conflicts:**
```bash
# Change port in docker-compose.yml
# or kill process on port
lsof -i :8001
kill -9 <PID>
```

## Next Steps

1. **Start platform**: `docker-compose up -d`
2. **Explore APIs**: http://localhost:8001/docs
3. **Read architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
4. **Develop locally**: See [DEVELOPMENT.md](DEVELOPMENT.md)
5. **Extend services**: Add new features following patterns

## Tech Stack Summary

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy async
- **Database**: PostgreSQL
- **Cache**: Redis
- **Container**: Docker
- **Orchestration**: Docker Compose → Kubernetes (future)
- **Testing**: pytest
- **Validation**: Pydantic v2

## Production Deployment (Future)

```bash
# Build images
docker build -t manufacturing-ai/data-ingest:1.0 services/data-ingest-service/

# Push to registry
docker push manufacturing-ai/data-ingest:1.0

# Deploy to Kubernetes
kubectl apply -f k8s/
```

## License

Proprietary - Manufacturing AI Copilot Platform

---

**Ready to start? Run:** `docker-compose up -d`
