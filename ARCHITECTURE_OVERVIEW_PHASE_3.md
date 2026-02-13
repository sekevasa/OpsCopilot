# Architecture Overview - Manufacturing AI Copilot

Complete architecture documentation for the Manufacturing AI Copilot microservices platform.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATIONS                       │
│         (Web UI, Mobile App, Desktop Client, API Clients)       │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ├────────────────────────────────────────────────────────┐
           │                                                        │
           ▼                                                        ▼
      ┌─────────────────┐   ┌──────────────────────────────────────┐
      │  API GATEWAY    │   │  KUBERNETES / DOCKER-COMPOSE         │
      │  (Optional)     │   │  (Service Orchestration)             │
      └────────┬────────┘   └──────────────────────────────────────┘
               │
    ┌──────────┼──────────┬───────────┬──────────────┬──────────────┐
    │          │          │           │              │              │
    ▼          ▼          ▼           ▼              ▼              ▼
┌─────────┐ ┌─────────┐ ┌────────┐ ┌──────────┐ ┌──────────────┐
│ Data    │ │Unified  │ │Forecast│ │AI Runtime│ │Notification │
│Ingest   │ │ Data    │ │Service │ │ Service  │ │ Service     │
│Service  │ │Service  │ │        │ │          │ │             │
└────┬────┘ └────┬────┘ └───┬────┘ └────┬─────┘ └─────┬────────┘
     │           │           │           │             │
     │    ┌──────┴───────┐   │           │             │
     │    │              │   │           │             │
     └────┼──────────────┼───┼───────────┼─────────────┘
          │              │   │           │
          └──────────────┼───┼───────────┘
                         │   │
                    ┌────▼───▼────────────────────┐
                    │  SHARED INFRASTRUCTURE      │
                    │  ├─ PostgreSQL (Multiple   │
                    │  │  Schemas)               │
                    │  ├─ Base Repository        │
                    │  ├─ Domain Models          │
                    │  ├─ Configuration          │
                    │  └─ Logging                │
                    └─────────────────────────────┘
```

---

## Microservices Architecture

### 1. Data Ingest Service

**Purpose**: Entry point for data from external systems (ERP, Accounting, Inventory)

**Architecture**:
```
┌─────────────────────────────────────────┐
│           API Layer (FastAPI)           │
│  POST /api/v1/ingest                   │
│  GET  /api/v1/jobs                     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Service Layer (Orchestration)      │
│  - IngestionOrchestrator                │
│  - Job management                       │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌──────────────┐      ┌───────────────┐
│  Connectors  │      │  Transformers │
├──────────────┤      ├───────────────┤
│ - ERP        │      │ - SKU         │
│ - Accounting │      │ - Inventory   │
│ - Inventory  │      │ - WorkOrder   │
└──────┬───────┘      └────────┬──────┘
       │                       │
       └───────────┬───────────┘
                   │
┌──────────────────▼──────────────────────┐
│   Repository Layer (Data Access)        │
│  - IngestionJobRepository               │
│  - StagingDataRepository                │
│  - DataConnectorConfigRepository        │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│   Infrastructure (Database)             │
│   PostgreSQL - staging schema           │
└─────────────────────────────────────────┘
```

**Key Patterns**:
- Factory Pattern: ConnectorFactory, TransformerFactory
- Strategy Pattern: Pluggable connectors and transformers
- Async Orchestration: Non-blocking job processing

**Database Schema**:
```sql
-- staging schema
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY,
    job_type VARCHAR,
    status VARCHAR,  -- pending, running, completed, failed
    source_connector VARCHAR,
    record_count INT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE staging_data (
    id UUID PRIMARY KEY,
    ingestion_job_id UUID REFERENCES ingestion_jobs,
    entity_type VARCHAR,  -- SKU, Inventory, WorkOrder
    raw_data JSONB,
    validation_status VARCHAR,
    transformed_data JSONB
);

CREATE TABLE data_connector_configs (
    id UUID PRIMARY KEY,
    connector_type VARCHAR,  -- ERP, Accounting, Inventory
    config_json JSONB,
    is_active BOOLEAN
);
```

---

### 2. Unified Data Service

**Purpose**: Single source of truth for manufacturing data (canonical schema)

**Architecture**:
```
┌─────────────────────────────────────────┐
│           API Layer (FastAPI)           │
│  GET  /api/v1/inventory/current         │
│  GET  /api/v1/orders/open               │
│  GET  /api/v1/suppliers                 │
│  GET  /api/v1/production/status         │
│  GET  /api/v1/quality/inventory-check   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│    Service Layer (Business Logic)       │
│  - ManufacturingDataService             │
│    ├─ get_inventory_current()           │
│    ├─ get_orders_open()                 │
│    ├─ get_suppliers()                   │
│    ├─ get_production_status()           │
│    └─ validate_inventory_consistency()  │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
    ┌───▼────┐       ┌────▼────┐
    │ Domain │       │Repository│
    │ Models │       │ Layer    │
    ├────────┤       ├──────────┤
    │- SKU   │       │- SKU     │
    │- BOM   │       │- BOM     │
    │- WO    │       │- WorkO.  │
    │- Suppl │       │- Supplier│
    │- Inv.  │       │- Invent. │
    │- Sales │       │- Sales   │
    └────────┘       └────┬─────┘
                          │
┌─────────────────────────▼──────────────┐
│   Infrastructure (Database)            │
│   PostgreSQL - manufacturing schema    │
└────────────────────────────────────────┘
```

**Data Models** (Manufacturing Domain):
```python
class SKU:
    sku_code: str
    description: str
    category: str
    unit_cost: float
    is_active: bool

class BOM:  # Bill of Materials
    bom_id: str
    sku_id: str
    component_sku_id: str
    quantity_per_unit: float

class WorkOrder:
    work_order_id: str
    sku_id: str
    quantity: float
    status: str  # planned, in_progress, completed, cancelled
    scheduled_start: datetime

class Supplier:
    supplier_id: str
    name: str
    rating: float
    lead_time_days: int

class InventorySnapshot:
    inventory_id: str
    sku_id: str
    warehouse_id: str
    quantity_on_hand: float
    quantity_reserved: float

class SalesOrder:
    sales_order_id: str
    customer_id: str
    sku_id: str
    quantity: float
    status: str  # open, partial, complete
```

**Key Patterns**:
- Repository Pattern: 6 specialized repositories
- Custom Query Methods: get_by_*, get_latest_*, get_active_*
- Domain-Driven Design: Manufacturing terminology

---

### 3. AI Runtime Service (Copilot)

**Purpose**: Intelligent query processing with tool orchestration

**Architecture**:
```
┌────────────────────────────────────────────┐
│          API Layer (FastAPI)               │
│  POST /api/v1/copilot/query               │
│  GET  /api/v1/copilot/session/{id}/history│
│  DELETE /api/v1/copilot/session/{id}      │
│  GET  /api/v1/copilot/tools               │
└────────────────┬─────────────────────────┘
                 │
    ┌────────────▼────────────┐
    │  CopilotOrchestrator    │
    │  ├─ process_query()     │
    │  ├─ _build_context()    │
    │  ├─ _determine_tools()  │
    │  ├─ _execute_tools()    │
    │  └─ _generate_response()│
    └────────┬────────────────┘
             │
    ┌────────┴───────────────┐
    │                        │
┌───▼─────────┐       ┌──────▼───────┐
│  Tools      │       │  Context     │
│  Module     │       │  Building    │
├─────────────┤       ├──────────────┤
│ BaseTool    │       │ContextBuilder│
│ -Inventory  │       │ _get_*()     │
│ -Orders     │       │ _calculate_  │
│ -Production │       │   insights() │
│ -Forecast   │       │              │
│ -Alerts     │       │              │
│             │       │              │
│ ToolRegistry│       │              │
└─────┬───────┘       └──────┬───────┘
      │                      │
      └──────────┬───────────┘
                 │
    ┌────────────▼────────────┐
    │  Memory Module          │
    │  ├─ ConversationMemory  │
    │  ├─ Message Storage     │
    │  └─ Context Variables   │
    │                         │
    │  ConversationStore      │
    │  ├─ Multi-session mgmt  │
    │  └─ Session Cleanup     │
    └────────┬────────────────┘
             │
┌────────────▼──────────────────────┐
│  External Service Integration     │
│  ├─ Unified Data Service          │
│  ├─ Forecast Service              │
│  ├─ Notification Service          │
│  └─ Database (Session Cache)      │
└───────────────────────────────────┘
```

**Query Processing Pipeline**:
```
User Query
    │
    ▼
1. Add to Memory
    │
    ▼
2. Build Context
    ├─ Fetch Inventory (Unified Data)
    ├─ Fetch Orders (Unified Data)
    ├─ Fetch Production (Unified Data)
    └─ Calculate Insights
    │
    ▼
3. Determine Tools
    ├─ Keyword analysis
    ├─ Context inspection
    └─ Tool selection (max N tools)
    │
    ▼
4. Execute Tools
    ├─ Tool 1: query_inventory
    ├─ Tool 2: lookup_orders
    └─ Tool 3: get_forecast
    │
    ▼
5. Generate Response
    ├─ Summarize tool results
    ├─ Add business insights
    ├─ Include failure notes
    └─ Calculate confidence
    │
    ▼
6. Save Response to Memory
    │
    ▼
Response to User
```

**Tool Isolation Pattern**:
```python
class BaseTool(ABC):
    """Abstract base class for isolated tools."""
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool with arguments."""
        pass

class InventoryQueryTool(BaseTool):
    async def execute(self, sku_code: str, warehouse=None):
        # Isolated: no dependencies on other tools
        # Calls Unified Data Service
        return {"qty_available": 250}

class ToolRegistry:
    """Factory for tool discovery and execution."""
    
    def get_tool(self, name: str) -> BaseTool:
        return self._tools.get(name)
    
    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())
```

---

### 4. Forecast Service

**Purpose**: Demand and inventory risk forecasting

**Architecture**:
```
┌─────────────────────────────────────┐
│        API Layer (FastAPI)          │
│  POST /api/v1/forecast/demand       │
│  POST /api/v1/forecast/inventory-risk│
│  POST /api/v1/forecasts (legacy)    │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│     Service Layer (Business Logic)  │
│  - ForecastingService               │
│    ├─ generate_forecast()           │
│    ├─ get_latest_forecast()         │
│    └─ get_active_alerts()           │
└────────────────┬────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼──────┐          ┌──────▼────┐
│  Domain  │          │Repository  │
│  Models  │          │  Layer     │
├──────────┤          ├────────────┤
│Forecast  │          │ForecastRepo│
│Forecast  │          │ForecastAlrt│
│Alert     │          │Repository  │
└──────────┘          └─────┬──────┘
                            │
┌────────────────────────────▼──────────────┐
│    Infrastructure (Database)              │
│    PostgreSQL - forecast schema           │
└───────────────────────────────────────────┘
```

**Forecast Models**:
```python
class Forecast:
    forecast_id: str
    forecast_type: str  # demand, inventory, supply, quality
    period: str  # daily, weekly, monthly, quarterly
    entity_id: str  # SKU, warehouse, etc.
    forecast_value: float
    confidence_level: float  # 0-100
    model_name: str

class ForecastAlert:
    alert_id: str
    forecast_id: str
    alert_type: str  # threshold_breach, anomaly, etc.
    severity: str  # critical, high, medium, low
    message: str
```

**Demand Forecast Response**:
```json
{
  "entity_id": "SKU-ABC-123",
  "period": "weekly",
  "forecast_values": [100, 105, 98, 110, 102],
  "forecast_dates": ["2024-12-26", "2025-01-02", ...],
  "confidence_intervals": {
    "upper": [110, 115.5, ...],
    "lower": [90, 94.5, ...]
  },
  "confidence_level": 85.0
}
```

**Inventory Risk Response**:
```json
{
  "entity_id": "SKU-ABC-123",
  "risk_level": "medium",  // critical, high, medium, low
  "stockout_probability": 0.35,
  "days_until_critical": 7,
  "recommended_reorder_qty": 250,
  "risk_factors": ["Inventory below reorder point", "High consumption rate"]
}
```

---

### 5. Notification Service

**Purpose**: Multi-channel alert distribution

**Architecture**:
```
┌──────────────────────────────────────┐
│       API Layer (FastAPI)            │
│  POST /api/v1/notify/email           │
│  POST /api/v1/notify/alert           │
│  POST /notify/alert/{id}/acknowledge │
│  POST /api/v1/notify/preferences     │
│  GET  /api/v1/notify/channels        │
└────────────────┬─────────────────────┘
                 │
┌────────────────▼─────────────────────┐
│   Service Layer (Business Logic)     │
│  - NotificationService               │
│    ├─ send_notification()            │
│    ├─ send_via_channel()             │
│    └─ set_preferences()              │
└────────────────┬─────────────────────┘
                 │
┌────────────────▼─────────────────────┐
│      Channel Adapters                │
│  ├─ Email (SMTP)                     │
│  ├─ Slack (Webhook)                  │
│  ├─ SMS (Twilio/Nexmo)               │
│  └─ Generic Webhook                  │
└────────────────┬─────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼──────┐          ┌──────▼────┐
│  Domain  │          │Repository  │
│  Models  │          │  Layer     │
├──────────┤          ├────────────┤
│Notif.    │          │NotifRepo   │
│Notif.Pref│          │NotifPref   │
│          │          │Repository  │
└──────────┘          └─────┬──────┘
                            │
┌────────────────────────────▼──────────────┐
│    Infrastructure (Database)              │
│    PostgreSQL - notification schema       │
└───────────────────────────────────────────┘
```

**Notification Flow**:
```
Alert Request
    │
    ▼
1. Create Alert Record
    │
    ▼
2. Get User Preferences
    ├─ Enabled channels
    ├─ Quiet hours check
    └─ Severity filters
    │
    ▼
3. Dispatch to Channels
    ├─ Email → SMTP
    ├─ Slack → Webhook
    ├─ SMS → Twilio API
    └─ Webhook → HTTP POST
    │
    ▼
4. Track Delivery
    ├─ Success/Failure per channel
    └─ Retry logic
    │
    ▼
5. Return Status
```

**Notification Models**:
```python
class Notification:
    notification_id: str
    user_id: str
    title: str
    message: str
    notification_type: str  # alert, info, warning
    severity: str  # critical, high, medium, low, info
    channel: str  # email, slack, sms, webhook
    status: str  # pending, sent, failed
    created_at: datetime

class NotificationPreference:
    preference_id: str
    user_id: str
    email: str
    phone: str
    slack_webhook: str
    enabled_channels: List[str]
    notify_on_critical: bool
    notify_on_high: bool
    quiet_hours_enabled: bool
    quiet_hours_start: str  # HH:MM
    quiet_hours_end: str    # HH:MM
```

---

## Shared Infrastructure

### Base Repository Pattern

```python
class BaseRepository(Generic[T]):
    """Generic repository for all entities."""
    
    async def create(self, entity: T) -> T:
        """Create new entity."""
        
    async def get_by_id(self, id: UUID) -> T:
        """Get entity by ID."""
        
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get paginated list."""
        
    async def update(self, id: UUID, update_data: dict) -> T:
        """Update entity."""
        
    async def delete(self, id: UUID) -> bool:
        """Delete entity."""
```

### Domain Models (Shared)

```python
# Enums
class DataSourceType(str, Enum):
    ERP = "erp"
    ACCOUNTING = "accounting"
    INVENTORY = "inventory"

class IngestionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class InventoryStatus(str, Enum):
    CRITICAL = "critical"
    LOW = "low"
    NORMAL = "normal"
    EXCESS = "excess"

# Domain Classes (Pydantic)
class SKU(BaseModel):
    sku_code: str
    description: str
    category: str
    unit_cost: float

class BOM(BaseModel):
    bom_id: str
    sku_id: str
    component_sku_id: str
    quantity_per_unit: float

class WorkOrder(BaseModel):
    work_order_id: str
    sku_id: str
    quantity: float
    status: str

class Supplier(BaseModel):
    supplier_id: str
    name: str
    rating: float
    lead_time_days: int

class InventorySnapshot(BaseModel):
    inventory_id: str
    sku_id: str
    quantity_on_hand: float
    quantity_reserved: float

class SalesOrder(BaseModel):
    sales_order_id: str
    customer_id: str
    sku_id: str
    quantity: float
    status: str
```

### Configuration Management

```python
class Settings:
    # Database
    DATABASE_URL: str
    
    # Services
    DATA_INGEST_SERVICE_URL: str
    UNIFIED_DATA_SERVICE_URL: str
    FORECAST_SERVICE_URL: str
    NOTIFICATION_SERVICE_URL: str
    
    # Feature flags
    ENABLE_FORECAST_CACHING: bool
    ENABLE_NOTIFICATION_RETRY: bool
    
    # Logging
    LOG_LEVEL: str  # DEBUG, INFO, WARNING, ERROR
    JSON_LOGS: bool
```

---

## Data Flow Diagrams

### Data Ingestion Flow

```
External Systems
├─ ERP
├─ Accounting
└─ Inventory Systems
    │
    ▼
Data Ingest Service (Connectors)
    ├─ ERPConnector
    ├─ AccountingConnector
    └─ InventoryConnector
    │
    ▼
Data Ingest Service (Transformers)
    ├─ Transform to SKU
    ├─ Transform to Inventory
    └─ Transform to WorkOrder
    │
    ▼
Data Ingest Service (Repositories)
    ├─ Store in staging schema
    └─ Update ingestion_jobs status
    │
    ▼
Unified Data Service
    ├─ Read from staging
    ├─ Validate & clean
    └─ Store in manufacturing schema
    │
    ▼
Available to:
├─ AI Runtime (via queries)
├─ Forecast Service (for training)
└─ Reports & Dashboards
```

### Copilot Query Flow

```
Client
    │
    ▼
POST /copilot/query
    │
    ▼
CopilotOrchestrator.process_query()
    │
    ├─ 1. Add to ConversationMemory
    │
    ├─ 2. Build Context
    │    ├─ Call Unified Data Service
    │    ├─ Fetch inventory context
    │    ├─ Fetch orders context
    │    └─ Calculate insights
    │
    ├─ 3. Determine Tools
    │    └─ Keyword analysis → [tool1, tool2, tool3]
    │
    ├─ 4. Execute Tools (in parallel)
    │    ├─ query_inventory → Unified Data
    │    ├─ lookup_orders → Unified Data
    │    └─ get_forecast → Forecast Service
    │
    ├─ 5. Generate Response
    │    ├─ Summarize results
    │    ├─ Add insights
    │    └─ Calculate confidence
    │
    └─ 6. Return Response
        ├─ Message
        ├─ Tool calls
        ├─ Context
        └─ Confidence score
```

### Alert Distribution Flow

```
System Event
    │
    ▼
POST /notify/alert
    │
    ▼
NotificationService
    │
    ├─ Create Alert record
    │
    ├─ Get User Preferences
    │    ├─ Enabled channels
    │    ├─ Severity filters
    │    └─ Quiet hours check
    │
    ├─ Dispatch per Channel
    │    ├─ Email → SMTP Server
    │    ├─ Slack → Webhook
    │    ├─ SMS → Twilio API
    │    └─ Webhook → HTTP POST
    │
    ├─ Track Delivery
    │    ├─ Update channel status
    │    └─ Retry if failed
    │
    └─ Return Response
        ├─ channels_notified
        ├─ channels_failed
        └─ alert status
```

---

## Integration Points

### Service-to-Service Communication

```
AI Runtime Service
    │
    ├─→ Unified Data Service (/inventory/current, /orders/open, /production/status)
    ├─→ Forecast Service (/forecasts, /forecast/demand)
    └─→ Notification Service (/notify/alert)

Forecast Service
    └─→ Unified Data Service (/orders/open for historical demand)

Data Ingest Service
    └─→ Unified Data Service (indirect via database)
```

### External System Integration

```
Data Ingest Service
    ├─→ ERP System (extract data)
    ├─→ Accounting System (extract data)
    └─→ Inventory System (extract data)

Notification Service
    ├─→ SMTP Server (Email)
    ├─→ Slack API (Messages)
    ├─→ Twilio/Nexmo (SMS)
    └─→ Custom Webhooks (Generic)
```

---

## Database Schema Overview

### Staging Schema (Data Ingest)
```
ingestion_jobs
ingestion_log_entries
staging_data
data_connector_configs
```

### Manufacturing Schema (Unified Data)
```
skus
boms
work_orders
suppliers
inventory_snapshots
sales_orders
inventory_history
```

### Forecast Schema
```
forecasts
forecast_alerts
forecast_models
forecast_accuracy_metrics
```

### Notification Schema
```
notifications
notification_preferences
notification_channel_configs
alert_acknowledgments
```

---

## Deployment Topology

### Development Environment
```
Docker Compose
├─ 5 Microservices (containers)
├─ PostgreSQL (single instance, multiple schemas)
├─ Redis (optional, for session caching)
└─ Network: service-to-service via container names
```

### Production Environment
```
Kubernetes Cluster
├─ 5 Microservices (deployments)
├─ PostgreSQL (managed service)
├─ Redis Cluster (distributed cache)
├─ API Gateway (Nginx/Kong)
├─ Message Queue (RabbitMQ/Kafka)
├─ Monitoring (Prometheus/Grafana)
└─ Logging (ELK Stack)
```

---

**Last Updated**: December 2024  
**Architecture Version**: 3.0  
**Services**: 5 Microservices + Shared Infrastructure
