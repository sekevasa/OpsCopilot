# 🚀 OpsCopilot Services - Ready to Run!

## ✅ Status
All 5 microservices are **ready to start** and will run in **mock mode** (without requiring a database).

```
✓ data-ingest-service         (Port 8001)
✓ unified-data-service        (Port 8002)
✓ ai-runtime-service          (Port 8003)
✓ forecast-service            (Port 8004)
✓ notification-service        (Port 8005)
```

## 🚀 Quick Start - Choose One Option

### Option 1: Simple Quick Start (Recommended)
```powershell
python quick_start_safe.py
```
This will open each service in a separate PowerShell window. Services will run in mock mode.

### Option 2: Manual Start (Individual Services)
```powershell
# Terminal 1
cd d:\Programming\Python\OpsCopilot
$env:PYTHONPATH = "d:\Programming\Python\OpsCopilot"
.\venv\Scripts\python.exe -m uvicorn services.data-ingest-service.app.main:app --port 8001 --reload

# Terminal 2
$env:PYTHONPATH = "d:\Programming\Python\OpsCopilot"
.\venv\Scripts\python.exe -m uvicorn services.unified-data-service.app.main:app --port 8002 --reload

# Terminal 3
$env:PYTHONPATH = "d:\Programming\Python\OpsCopilot"
.\venv\Scripts\python.exe -m uvicorn services.ai-runtime-service.app.main:app --port 8003 --reload

# Terminal 4
$env:PYTHONPATH = "d:\Programming\Python\OpsCopilot"
.\venv\Scripts\python.exe -m uvicorn services.forecast-service.app.main:app --port 8004 --reload

# Terminal 5
$env:PYTHONPATH = "d:\Programming\Python\OpsCopilot"
.\venv\Scripts\python.exe -m uvicorn services.notification-service.app.main:app --port 8005 --reload
```

### Option 3: With Docker Database (Full Setup)
```powershell
# Terminal 1: Start Docker containers
docker-compose up -d

# Terminal 2: Run all services with database
python run_services.py
```

## 🌐 Access APIs

Once services are running, access them via Swagger UI:

| Service | Swagger UI | Health Check |
|---------|-----------|--------------|
| Data Ingest | http://localhost:8001/docs | http://localhost:8001/api/v1/health |
| Unified Data | http://localhost:8002/docs | http://localhost:8002/api/v1/health |
| AI Runtime | http://localhost:8003/docs | http://localhost:8003/api/v1/health |
| Forecast | http://localhost:8004/docs | http://localhost:8004/api/v1/health |
| Notification | http://localhost:8005/docs | http://localhost:8005/api/v1/health |

## 📝 Test API Calls

### Example 1: Query the Copilot
```bash
curl -X POST http://localhost:8003/copilot/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current demand forecast?",
    "context": {"timeframe": "7days"}
  }'
```

### Example 2: Get Demand Forecast
```bash
curl -X POST http://localhost:8004/forecast/demand \
  -H "Content-Type: application/json" \
  -d '{
    "sku_id": "SKU-001",
    "historical_data": [100, 110, 105, 120],
    "days_ahead": 7
  }'
```

### Example 3: Send Notification
```bash
curl -X POST http://localhost:8005/notify/alert \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "email",
    "recipient": "user@example.com",
    "subject": "Production Alert",
    "message": "Production capacity reached 80%"
  }'
```

## 📚 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│        Manufacturing AI Copilot Platform             │
├──────────────┬──────────────┬──────────────────────┤
│ Data Ingest  │ Unified Data │ AI Runtime Copilot  │
│ (8001)       │ Service      │ (8003)              │
│              │ (8002)       │                     │
├──────────────┴──────────────┴──────────────────────┤
│ Forecast Service (8004) │ Notification (8005)     │
├─────────────────────────┴──────────────────────────┤
│    Shared Infrastructure                           │
│  • SQLAlchemy ORM (Mock Mode)                      │
│  • PostgreSQL Connection (Optional)                │
│  • Redis Caching (Optional)                        │
│  • Domain Models & Repositories                    │
└─────────────────────────────────────────────────────┘
```

## 🔧 Service Details

### Data Ingest Service (8001)
- **Purpose**: Ingest manufacturing data from ERP systems
- **Key Endpoints**: 
  - POST `/ingest/batch` - Process data batch
  - GET `/ingest/jobs` - List ingest jobs
  - GET `/ingest/jobs/{id}/status` - Job status

### Unified Data Service (8002)
- **Purpose**: Master data management for manufacturing
- **Key Endpoints**:
  - GET `/sku` - List SKUs
  - POST `/bom` - Create Bill of Materials
  - GET `/work-order` - List work orders

### AI Runtime Service (8003) - Copilot
- **Purpose**: Conversational AI assistant for manufacturing
- **Key Endpoints**:
  - POST `/copilot/query` - Ask questions
  - POST `/copilot/session/{id}/history` - Get conversation history
  - GET `/copilot/tools` - List available tools

### Forecast Service (8004)
- **Purpose**: Demand forecasting and inventory management
- **Key Endpoints**:
  - POST `/forecast/demand` - Generate demand forecast
  - POST `/forecast/inventory-risk` - Assess inventory risk
  - GET `/forecast/models` - List ML models

### Notification Service (8005)
- **Purpose**: Multi-channel alerts and notifications
- **Key Endpoints**:
  - POST `/notify/alert` - Send alert
  - POST `/notify/subscribe` - Subscribe to alerts
  - GET `/notify/channels` - List channels

## 🛠️ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'shared'"
**Solution**: Ensure PYTHONPATH is set to workspace root:
```powershell
$env:PYTHONPATH = "d:\Programming\Python\OpsCopilot"
```

### Issue: "Password authentication failed"
**Solution**: This is expected in mock mode. Services will continue running. To use actual database:
1. Install PostgreSQL 15+
2. Create user: `createuser -P copilot_user` (password: `copilot_password`)
3. Create database: `createdb -U copilot_user copilot_db`
4. Run `python run_services.py`

### Issue: Port already in use
**Solution**: Change port in startup command:
```powershell
.\venv\Scripts\python.exe -m uvicorn services.forecast-service.app.main:app --port 9004 --reload
```

### Issue: Virtual environment not found
**Solution**: Recreate it:
```powershell
py -3.14 -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

## 📖 Documentation Files

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide with examples
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete setup instructions
- **[API_REFERENCE.md](API_REFERENCE_PHASE_3.md)** - API reference with all endpoints
- **.env** - Environment configuration (database, Redis, ports)
- **docker-compose.yml** - PostgreSQL + Redis containers for full setup

## 🎯 Next Steps

1. **Start Services**: Run `python quick_start_safe.py`
2. **Test API**: Open http://localhost:8003/docs in browser
3. **Try Examples**: Use Swagger UI or curl commands above
4. **Enable Database** (Optional):
   - Install PostgreSQL + Redis
   - Run `docker-compose up -d`
   - Run `python run_services.py`

## 💻 System Requirements

- Python 3.14+
- Virtual environment (already created)
- 2 GB RAM (4 GB recommended with database)
- PostgreSQL 15+ (optional, for persistence)
- Redis 7+ (optional, for caching)

## ✨ Key Features

✓ All 5 microservices ready to run  
✓ Mock mode (no database required initially)  
✓ Swagger UI on all endpoints (/docs)  
✓ Health checks on all services  
✓ Graceful error handling  
✓ Development ready with hot reload  
✓ Production-ready architecture  

---

**Status**: ✅ Ready for use  
**Last Updated**: 2024  
**Environment**: Python 3.14, FastAPI 0.129.0  
**Mode**: Mock (can upgrade to full database setup anytime)
