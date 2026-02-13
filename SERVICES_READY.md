# ✅ Manufacturing AI Copilot - Services Ready!

**Date**: February 13, 2026

---

## 🎉 Setup Complete

All 5 microservices are now ready to run in your local environment!

### ✓ What Was Set Up

1. **Virtual Environment** (Python 3.14)
   - Located: `./venv/`
   - All dependencies installed

2. **All Services Ready**
   - ✅ Data Ingest Service (port 8001)
   - ✅ Unified Data Service (port 8002)  
   - ✅ AI Runtime Service (port 8003) - **Copilot with tools, context, memory**
   - ✅ Forecast Service (port 8004) - **Demand forecasting + risk assessment**
   - ✅ Notification Service (port 8005) - **Multi-channel alerts**

3. **Startup Scripts Created**
   - `run_services.py` - Multi-service runner with database
   - `quick_start.py` - Quick start without database
   - `start_services.ps1` - PowerShell startup script

4. **Bugs Fixed** 🔧
   - ✅ Fixed unified-data-service import paths
   - ✅ Fixed data-ingest-service SQLAlchemy metadata conflict
   - ✅ Fixed notification-service syntax errors
   - ✅ Added missing RawDataBatch model
   - ✅ Installed email-validator dependency

---

## 🚀 Quick Start (Choose One)

### Option A: Test APIs Without Database (Recommended First Step)

```bash
python quick_start.py
```

✓ Services start in separate windows  
✓ No database required  
✓ Perfect for testing endpoints

Then visit: **http://localhost:8003/docs** (Swagger UI)

### Option B: Full Setup With Database & Cache

```bash
# Start PostgreSQL + Redis (requires Docker)
docker-compose up -d

# Start services
.\venv\Scripts\Activate.ps1
python run_services.py
```

✓ Full database connectivity  
✓ Redis caching  
✓ Complete integration testing

---

## 📡 Access the Services

Once services are running, access them at:

| Service | Swagger UI | Purpose |
|---------|-----------|---------|
| **AI Runtime** | http://localhost:8003/docs | Copilot with tools & conversation memory |
| **Forecast** | http://localhost:8004/docs | Demand forecasting & risk assessment |
| **Notification** | http://localhost:8005/docs | Multi-channel alerts & preferences |
| **Unified Data** | http://localhost:8002/docs | Master data management |
| **Data Ingest** | http://localhost:8001/docs | Data ingestion |

---

## 🧪 Try These Endpoints

### 1. Copilot Query (AI Runtime)

```bash
$query = @{
    query = "What's the current inventory for SKU ABC123?"
    session_id = "user-1"
    max_tools = 3
} | ConvertTo-Json

Invoke-RestMethod http://localhost:8003/api/v1/copilot/query `
    -Method Post -Body $query -ContentType "application/json" | ConvertTo-Json
```

### 2. Demand Forecast

```bash
$forecast = @{
    entity_id = "SKU-123"
    period = "weekly"
    horizon_days = 30
    lookback_days = 365
} | ConvertTo-Json

Invoke-RestMethod http://localhost:8004/api/v1/forecast/demand `
    -Method Post -Body $forecast -ContentType "application/json" | ConvertTo-Json
```

### 3. Send Alert

```bash
$alert = @{
    user_id = "user-1"
    alert_title = "Critical Alert"
    alert_message = "Inventory below threshold"
    severity = "critical"
    channels = @("email", "slack")
} | ConvertTo-Json

Invoke-RestMethod http://localhost:8005/api/v1/notify/alert `
    -Method Post -Body $alert -ContentType "application/json" | ConvertTo-Json
```

---

## 📋 What's Included

### Phase 3 Features (Just Completed)

**AI Runtime Service** (Port 8003)
- ✅ Copilot orchestrator with tool isolation
- ✅ 5 specialized tools (inventory, orders, production, forecast, alerts)
- ✅ Multi-source context building
- ✅ Conversation memory with multi-turn support
- ✅ 4 new endpoints: `/copilot/query`, `/copilot/session/{id}/history`, etc.

**Forecast Service** (Port 8004)
- ✅ Demand forecasting with confidence intervals
- ✅ Inventory risk assessment with stockout probability
- ✅ Reorder quantity recommendations
- ✅ 2 new endpoints: `/forecast/demand`, `/forecast/inventory-risk`

**Notification Service** (Port 8005)
- ✅ Email notifications with HTML support
- ✅ Multi-channel alert dispatch (email, Slack, SMS, webhooks)
- ✅ Alert acknowledgment & TTL expiration
- ✅ User preference management with quiet hours
- ✅ 5 new endpoints: `/notify/email`, `/notify/alert`, `/notify/preferences`, etc.

### Earlier Phases

**Data Ingest** - ERP/accounting data ingestion  
**Unified Data** - Manufacturing master data with 6 models  
**Shared** - Domain models (SKU, BOM, WorkOrder, etc.)

---

## 🔧 Environment

### Current Configuration (.env)

```env
DB_HOST=localhost
DB_USER=copilot_user
DB_PASSWORD=copilot_password
DB_NAME=copilot_db
REDIS_HOST=localhost
DEBUG=true
```

For Docker: Services will auto-connect to docker-compose containers  
For PostgreSQL: Install locally and update DB_HOST  
For Testing: Use `quick_start.py` (no DB required)

---

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** ← Start here!
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed setup instructions
- **[API_REFERENCE_PHASE_3.md](API_REFERENCE_PHASE_3.md)** - Complete API reference with examples
- **[PHASE_3_COMPLETION_REPORT.md](PHASE_3_COMPLETION_REPORT.md)** - Detailed work summary
- **[ARCHITECTURE_PATTERNS.md](ARCHITECTURE_PATTERNS.md)** - Design patterns used

---

## ⚡ Common Commands

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start all services (quick, no DB)
python quick_start.py

# Start all services (with Docker)
docker-compose up -d
python run_services.py

# Start one service manually
cd services/ai-runtime-service
uvicorn main:app --reload --port 8003

# Check health of all services
for ($i = 8001; $i -le 8005; $i++) {
    Invoke-RestMethod http://localhost:$i/api/v1/health
}

# Run tests
pytest

# Format code
black .

# Type check
mypy services/
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
Get-NetTCPConnection -LocalPort 8003 | Select-Object OwningProcess
Get-Process -Id <PID> | Stop-Process -Force
```

### Database Connection Error
→ Use `python quick_start.py` instead (no DB required)

### Module Import Errors
```bash
$env:PYTHONPATH = "."
.\venv\Scripts\python.exe -c "from shared.domain_models import SKU; print('OK')"
```

### Service Won't Start
```bash
# Check venv is activated
.\venv\Scripts\python.exe --version

# Check app can be imported
cd services/ai-runtime-service
..\..\venv\Scripts\python.exe -c "from app.main import app; print('OK')"
```

---

## 🎯 Next Steps

1. **Run services**: `python quick_start.py`
2. **Open Swagger**: http://localhost:8003/docs
3. **Try a query**: Use the `/copilot/query` endpoint
4. **Read the docs**: See [API_REFERENCE_PHASE_3.md](API_REFERENCE_PHASE_3.md)
5. **Explore features**: Test forecast and notification endpoints

---

## 📊 Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| Virtual Environment | ✅ | Python 3.14, all dependencies installed |
| Data Ingest Service | ✅ | Complete with connectors & orchestration |
| Unified Data Service | ✅ | 6 models, 6 repositories |
| AI Runtime Service | ✅ | Copilot with tools & context building |
| Forecast Service | ✅ | Demand forecasting + risk assessment |
| Notification Service | ✅ | Multi-channel alerts & preferences |
| Startup Scripts | ✅ | `quick_start.py`, `run_services.py` |
| Docker Compose | ✅ | PostgreSQL + Redis configured |
| Alembic Migrations | ⏳ | Next milestone |
| Kubernetes Deploy | ⏳ | Future phase |

---

## 💡 Architecture Highlights

- **Clean Architecture**: API → Service → Domain → Repository → DB
- **Domain-Driven Design**: Manufacturing terminology (SKU, BOM, WorkOrder)
- **Async/Await**: 100% non-blocking with FastAPI + asyncpg
- **Tool Isolation**: Each tool is independent, extensible
- **Context Building**: Multi-source data aggregation for copilot
- **Type Safety**: Full Pydantic + mypy type hints

---

**Status**: ✅ All services ready to run!  
**Command**: `python quick_start.py`  
**Docs**: http://localhost:8003/docs

Good luck! 🚀
