# Manufacturing AI Copilot - Local Development Setup Guide

## Prerequisites

- Python 3.11+ (Python 3.14 recommended)
- Windows PowerShell 5.1+ or similar shell
- PostgreSQL 15 (optional for local testing)
- Redis (optional for caching)

## Virtual Environment Setup ✓ COMPLETE

The virtual environment has been created and all dependencies installed:

```
✓ venv/                              - Python virtual environment
✓ fastapi==0.129.0                   - Web framework
✓ uvicorn==0.40.0                    - ASGI server
✓ pydantic==2.12.5                   - Data validation
✓ sqlalchemy==2.0.46                 - ORM
✓ asyncpg==0.31.0                    - PostgreSQL driver
✓ redis==7.1.1                       - Redis client
✓ pytest==9.0.2                      - Testing framework
✓ black, flake8, mypy, isort         - Development tools
```

## Starting the Services

### Option 1: Python Multi-Service Runner (RECOMMENDED)

This runs all services in one terminal with proper logging:

```bash
# Activate venv first (if not already activated)
.\venv\Scripts\Activate.ps1

# Run all services
python run_services.py
```

**Output**: All services will start on ports 8001-8005 with live logs in one window.

### Option 2: Start Individual Services Manually

If you prefer to run services individually:

```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# In Terminal 1
cd services/data-ingest-service
uvicorn main:app --reload --port 8001

# In Terminal 2
cd services/unified-data-service
uvicorn main:app --reload --port 8002

# In Terminal 3
cd services/ai-runtime-service
uvicorn main:app --reload --port 8003

# In Terminal 4
cd services/forecast-service
uvicorn main:app --reload --port 8004

# In Terminal 5
cd services/notification-service
uvicorn main:app --reload --port 8005
```

## Service Endpoints

Once services are running, access them at:

| Service | Port | Swagger UI | Health Check |
|---------|------|-----------|--------------|
| Data Ingest | 8001 | http://localhost:8001/docs | http://localhost:8001/api/v1/health |
| Unified Data | 8002 | http://localhost:8002/docs | http://localhost:8002/api/v1/health |
| AI Runtime | 8003 | http://localhost:8003/docs | http://localhost:8003/api/v1/health |
| Forecast | 8004 | http://localhost:8004/docs | http://localhost:8004/api/v1/health |
| Notification | 8005 | http://localhost:8005/docs | http://localhost:8005/api/v1/health |

## Testing Services

### Health Check All Services

```bash
# Check all services are running
for ($i = 8001; $i -le 8005; $i++) {
    Write-Host "Checking port $i..."
    Invoke-RestMethod -Uri "http://localhost:$i/api/v1/health"
}
```

### Example: Copilot Query

```bash
# POST /copilot/query endpoint
$query = @{
    query = "What's the current inventory level for SKU ABC123?"
    session_id = "user-123-session"
    context_hints = @{
        entity_type = "sku"
        entity_id = "ABC123"
    }
    max_tools = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8003/api/v1/copilot/query" `
    -Method Post -Body $query -ContentType "application/json"
```

### Example: Demand Forecast

```bash
# POST /forecast/demand endpoint
$forecast = @{
    entity_id = "SKU-ABC-123"
    entity_type = "sku"
    period = "weekly"
    horizon_days = 30
    lookback_days = 365
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8004/api/v1/forecast/demand" `
    -Method Post -Body $forecast -ContentType "application/json"
```

### Example: Send Email Alert

```bash
# POST /notify/email endpoint
$email = @{
    recipient_email = "user@example.com"
    subject = "Inventory Alert"
    body = "SKU ABC-123 is below reorder point"
    priority = "high"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8005/api/v1/notify/email" `
    -Method Post -Body $email -ContentType "application/json"
```

## Code Organization

```
OpsCopilot/
├── shared/                           # Shared infrastructure
│   ├── domain_models.py              # Manufacturing domain models
│   ├── database.py                   # Database setup
│   ├── config.py                     # Configuration management
│   └── requirements.txt              # Shared dependencies
│
├── services/
│   ├── data-ingest-service/          # Data ingestion
│   │   ├── app/
│   │   │   ├── api/routes.py
│   │   │   ├── domain/models.py
│   │   │   ├── infrastructure/
│   │   │   └── main.py
│   │   └── main.py                   # Entry point
│   │
│   ├── unified-data-service/         # Master data
│   │   ├── app/
│   │   │   ├── api/routes.py
│   │   │   ├── domain/models.py
│   │   │   └── main.py
│   │   └── main.py
│   │
│   ├── ai-runtime-service/           # Copilot engine
│   │   ├── app/
│   │   │   ├── api/routes.py         # ✓ /copilot/* endpoints
│   │   │   ├── copilot/
│   │   │   │   └── orchestrator.py   # CopilotOrchestrator
│   │   │   ├── memory/
│   │   │   │   └── conversation.py   # ConversationMemory
│   │   │   ├── tools/
│   │   │   │   └── base.py           # Tool implementations
│   │   │   ├── context/
│   │   │   │   └── builder.py        # ContextBuilder
│   │   │   └── main.py
│   │   └── main.py
│   │
│   ├── forecast-service/             # Forecasting
│   │   ├── app/
│   │   │   ├── api/routes.py         # ✓ /forecast/* endpoints
│   │   │   ├── domain/models.py
│   │   │   └── main.py
│   │   └── main.py
│   │
│   └── notification-service/         # Notifications
│       ├── app/
│       │   ├── api/routes.py         # ✓ /notify/* endpoints
│       │   ├── domain/models.py
│       │   └── main.py
│       └── main.py
│
├── run_services.py                   # Multi-service runner
├── start_services.ps1                # PowerShell startup script
├── .env                              # Environment variables (local)
└── README.md
```

## Development Workflow

### Adding a New Route

1. Create endpoint in `app/api/routes.py`:
   ```python
   @router.post("/path", response_model=ResponseModel)
   async def handler(request: RequestModel):
       # Implementation
       pass
   ```

2. Define request/response schemas in `app/domain/schemas.py`:
   ```python
   class RequestModel(BaseModel):
       field: str = Field(...)
   
   class ResponseModel(BaseModel):
       result: str
   ```

3. Access at: `http://localhost:{port}/api/v1/path`

4. Auto-reload will pick up changes (--reload flag)

### Running Tests

```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Run all tests
pytest

# Run specific service tests
pytest services/ai-runtime-service/tests

# Run with coverage
pytest --cov=services
```

### Code Quality

```bash
# Format code
black .

# Check imports
isort .

# Lint
flake8 .

# Type check
mypy services/
```

## Troubleshooting

### Port Already in Use

If a port is already in use:

```bash
# Find process using port (e.g., 8001)
Get-Process -Id (Get-NetTCPConnection -LocalPort 8001).OwningProcess

# Kill it
Get-Process -Id (Get-NetTCPConnection -LocalPort 8001).OwningProcess | Stop-Process -Force
```

### Module Not Found

Ensure PYTHONPATH is set correctly:

```bash
$env:PYTHONPATH = "."
```

### Database Connection Errors

Services will start even without a database. They'll fail at runtime if you try to use database operations. To use the database:

1. Start PostgreSQL
2. Create database: `CREATE DATABASE copilot_db`
3. Services will auto-migrate schemas on first run (if Alembic is set up)

### Service Won't Start

1. Check the service still has main.py:
   ```bash
   ls services/*/main.py
   ```

2. Check app/main.py exists:
   ```bash
   ls services/*/app/main.py
   ```

3. Check for syntax errors:
   ```bash
   python -m py_compile services/*/app/main.py
   ```

## Next Steps

1. **Try a copilot query**: Use the /copilot/query endpoint
2. **Generate forecast**: Use /forecast/demand endpoint
3. **Send notification**: Use /notify/email endpoint
4. **Read API docs**: Visit http://localhost:8003/docs (Swagger UI)
5. **Check logs**: Monitor service output in terminal

## Environment Variables

Key environment variables in `.env`:

```env
# Database
DB_HOST=localhost          # PostgreSQL host
DB_PORT=5432              # PostgreSQL port
DB_NAME=copilot_db        # Database name

# Redis
REDIS_HOST=localhost      # Redis host
REDIS_PORT=6379          # Redis port

# Development
DEBUG=true                # Enable debug mode
LOG_LEVEL=INFO            # Logging level
```

---

**Created**: February 2026  
**Status**: Services ready to run  
**Next milestone**: Setup Alembic migrations + Docker Compose
