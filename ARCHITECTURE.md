# Architecture Documentation

## System Design

### Microservices Architecture

Each service is independently deployable and scalable:

1. **Data Ingest Service** - Entry point for data
   - Validates and queues raw data
   - Tracks ingestion status
   - Enables replay capability

2. **Unified Data Service** - Data normalization
   - Transforms ERP/accounting data
   - Maps external IDs to unified schema
   - Maintains historical snapshots

3. **AI Runtime Service** - ML model execution
   - Manages model lifecycle
   - Executes async inference
   - Tracks execution metrics

4. **Forecast Service** - Predictive analytics
   - Generates forecasts from historical data
   - Creates automatic alerts
   - Tracks forecast accuracy

5. **Notification Service** - Alert delivery
   - Multi-channel notification
   - User preferences management
   - Delivery tracking and retry logic

### Data Flow

```
External System
    ↓
[Data Ingest Service]
    ↓ (raw_data_batches)
PostgreSQL
    ↓
[Unified Data Service] (normalizes)
    ↓
[manufacturing_items, inventory_snapshots]
    ↓
[AI Runtime Service] (inference)
    ↓
[Forecast Service] (predictions)
    ↓
[Notification Service] (alerts)
    ↓
End User
```

### Communication Patterns

#### Synchronous (HTTP/REST)
- Service-to-service API calls
- Direct latency-sensitive operations
- Health checks, status queries

#### Asynchronous (Future)
- Message queue for bulk operations
- Event streaming for data updates
- Batch processing jobs

### Database Design

#### Shared Database Approach
- Single PostgreSQL instance per environment
- Schema isolation per service (future)
- Shared infrastructure layer

#### Schema Organization
```
-- Raw data from external systems
public.raw_data_batches
public.prim_master_audits

-- Normalized manufacturing data
public.manufacturing_items
public.manufacturing_processes
public.inventory_snapshots

-- AI/ML models and execution
public.ai_models
public.inference_jobs

-- Forecasts and alerts
public.forecasts
public.forecast_alerts

-- Notifications
public.notifications
public.notification_preferences
public.notification_templates
```

### Caching Strategy

Redis caching for:
- Frequently accessed items (manufacturing_items)
- User preferences
- Model metadata
- Recent forecasts

TTL-based expiration for data freshness.

## Clean Architecture Layers

### Domain Layer (app/domain/)

**Purpose**: Core business logic independent of technology

**Components**:
- `models.py` - SQLAlchemy ORM models (database schema)
- `schemas.py` - Pydantic models for API contracts
- `repositories.py` - Data access interfaces
- Business rules, validations, calculations

**Key Principles**:
- No external dependencies (framework, DB drivers)
- Pure business logic
- Testable without infrastructure

### Application Layer (app/application/)

**Purpose**: Orchestrates domain objects to fulfill use cases

**Components**:
- `services.py` - Application services
- High-level business workflows
- Orchestration of repositories

**Responsibilities**:
- Transaction management
- Cross-domain coordination
- Use case implementation

### Infrastructure Layer (app/infrastructure/)

**Purpose**: Technical implementation details

**Components**:
- Configuration management
- Logger initialization
- External service clients
- Dependency injection setup

### API Layer (app/api/)

**Purpose**: HTTP interface

**Components**:
- `routes.py` - Endpoint definitions
- Request/response handling
- Error formatting
- Input validation (Pydantic)

## Design Patterns

### Repository Pattern
```python
class Repository(Generic[T]):
    async def create(obj: T) -> T
    async def get_by_id(id: UUID) -> Optional[T]
    async def update(id: UUID, data: dict) -> Optional[T]
    async def delete(id: UUID) -> bool
```

Provides data access abstraction, enables testing with mock repositories.

### Service Layer Pattern
```python
class Service:
    def __init__(self, session: AsyncSession):
        self.repository = Repository(session)
    
    async def business_operation(self):
        # Orchestrate repository calls
        # Apply business logic
        # Return domain results
```

Encapsulates business logic and use cases.

### Dependency Injection via FastAPI
```python
async def get_service(
    session: AsyncSession = Depends(db.get_session)
) -> Service:
    return Service(session)

@router.post("/endpoint")
async def endpoint(service: Service = Depends(get_service)):
    # Use injected service
```

Provides loose coupling, testability, and singleton management.

## Async/Await Strategy

All I/O operations are async:
- Database queries (asyncpg)
- External service calls (httpx)
- File operations

Benefits:
- Better resource utilization
- Handles concurrent requests efficiently
- Scalable with limited resources

## Error Handling

### Exception Hierarchy
```
Exception
├── ServiceError (custom)
│   ├── ValidationError
│   ├── NotFoundError
│   ├── DuplicateError
│   └── OperationError
```

### HTTP Error Responses
```json
{
  "detail": {
    "code": "VALIDATION_ERROR",
    "message": "Field 'sku' must be unique",
    "details": {
      "field": "sku",
      "value": "ITEM-001"
    }
  }
}
```

## Configuration Management

### Layered Configuration
1. Environment variables (highest priority)
2. .env file
3. Default values in config.py

### Pydantic Settings
- Type-safe configuration
- Automatic validation
- Environment variable mapping
- Nested configuration objects

## Testing Strategy

### Unit Tests
- Test services in isolation
- Mock repositories
- Mock external dependencies

### Integration Tests
- Use in-memory SQLite
- Test full service layer
- Include repository logic

### End-to-End Tests (Future)
- Docker Compose setup
- Real database
- Multi-service workflows

## Deployment Considerations

### Containerization
- Each service in separate container
- Shared base image
- Minimal image size

### Environment Separation
- Development (local, verbose logging)
- Staging (production-like)
- Production (optimized, secure)

### Scaling
- Horizontal scaling: Multiple service instances
- Load balancing: Nginx/Traefik
- Database: Connection pooling
- Cache: Distributed Redis

### Health & Monitoring
- Health check endpoints
- Structured logging
- Prometheus metrics (future)
- Distributed tracing (future)

## Security (Future)

- API authentication (JWT/OAuth)
- Rate limiting
- CORS configuration
- Data encryption at rest
- Secrets management (HashiCorp Vault)
- SQL injection prevention (SQLAlchemy parameterization)
