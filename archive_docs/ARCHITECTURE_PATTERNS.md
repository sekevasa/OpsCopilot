# Enterprise Architecture Patterns - Implementation Guide

## 🏛️ Clean Architecture Implementation

### Layered Design

```
┌────────────────────────────────────────┐
│     API Layer (FastAPI Routes)         │  ← HTTP interface
│   - Request validation (Pydantic)      │  ← OpenAPI documentation
│   - Error handling (HTTPException)     │  ← Status codes
├────────────────────────────────────────┤
│   Application Services Layer           │  ← Business orchestration
│   - Use case implementation            │  ← Transaction coordination
│   - Domain service methods             │  ← Error handling
├────────────────────────────────────────┤
│   Domain Model Layer                   │  ← Core business logic
│   - Entities (SKU, BOM, WorkOrder)     │  ← Value objects
│   - Enums (statuses, types)            │  ← Business rules
├────────────────────────────────────────┤
│   Data Access Layer (Repositories)     │  ← Query abstraction
│   - Generic CRUD (BaseRepository[T])   │  ← Custom queries
│   - Entity repositories                │  ← SQL generation
├────────────────────────────────────────┤
│   Infrastructure Layer                 │  ← Technical concerns
│   - Database connection                │  ← Session management
│   - Configuration                      │  ← Logging
└────────────────────────────────────────┘
```

### Dependencies Flow (Inbound)

```
HTTP Request
    ↓
(1) API Route Handler validates & deserializes request
    ↓ Depends on
(2) Service Layer executes business logic
    ↓ Depends on
(3) Repository executes queries
    ↓ Depends on
(4) Infrastructure (Database, Config)

✅ NO REVERSE DEPENDENCIES (lower layers don't know about higher layers)
```

---

## 🏭 Factory Pattern

### Problem
Different data sources (ERP, Accounting, Inventory) need different connectors, but API shouldn't need to know about all types.

### Solution: ConnectorFactory

```python
class ConnectorFactory:
    _connectors = {
        "erp": ERPConnector,
        "accounting": AccountingConnector,
        "inventory_system": InventoryConnector,
    }
    
    @classmethod
    def create_connector(cls, source_type: str, connection_str: str) -> BaseConnector:
        connector_class = cls._connectors.get(source_type)
        if not connector_class:
            raise ValueError(f"Unsupported type: {source_type}")
        return connector_class(connection_str)
```

### Benefits
- ✅ Easy to add new connector types
- ✅ No conditional logic in client code
- ✅ Type-safe with abstract base class
- ✅ Configuration-driven

### Usage
```python
# Instead of:
if source_type == "erp":
    connector = ERPConnector(...)
elif source_type == "accounting":
    connector = AccountingConnector(...)

# Do this:
connector = ConnectorFactory.create_connector(source_type, connection_str)
```

---

## 🏛️ Repository Pattern

### Generic Base Repository

```python
class BaseRepository(Generic[T]):
    """Generic CRUD for any entity."""
    
    async def create(self, entity: T) -> T: ...
    async def get_by_id(self, id: UUID) -> Optional[T]: ...
    async def get_all(self, skip=0, limit=100) -> List[T]: ...
    async def update(self, entity: T) -> T: ...
    async def delete(self, id: UUID) -> bool: ...
    async def exists(self, id: UUID) -> bool: ...
```

### Specialized Repository with Custom Queries

```python
class SKURepository(BaseRepository[SKUModel]):
    """Repository for SKU with domain-specific queries."""
    
    async def get_by_sku_code(self, sku_code: str) -> Optional[SKUModel]:
        """Query-optimized by code."""
        stmt = select(SKUModel).where(SKUModel.sku_code == sku_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_active_skus(self) -> List[SKUModel]:
        """Get only active products."""
        stmt = select(SKUModel).where(SKUModel.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_category(self, category: str) -> List[SKUModel]:
        """Group by product category."""
        stmt = select(SKUModel).where(SKUModel.category == category)
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

### Benefits
- ✅ **No database queries in services**: Queries isolated in repository
- ✅ **Easy to test**: Mock repository instead of real DB
- ✅ **Easy to optimize**: Change SQL without affecting business logic
- ✅ **Reusable**: Same repository for multiple services
- ✅ **Type-safe**: Generic[T] ensures compile-time type checking

### Testing
```python
# In tests: Mock the repository
mock_repo = AsyncMock(spec=SKURepository)
mock_repo.get_by_sku_code.return_value = SKUModel(sku_code="SKU-001", ...)

# Pass mock to service
service = ManufacturingDataService(session)
service.sku_repo = mock_repo

# Service logic tested without touching DB
await service.get_inventory_current()
```

---

## 🎯 Service Layer Pattern

### Problem
Business logic mixed with HTTP concerns → Hard to test, reuse, maintain.

### Solution: Dedicated Service Class

```python
class ManufacturingDataService:
    """Pure business logic - no HTTP knowledge."""
    
    def __init__(self, session: AsyncSession):
        self.sku_repo = SKURepository(session)
        self.inventory_repo = InventorySnapshotRepository(session)
    
    async def get_inventory_current(self, warehouse=None):
        """Get current inventory - pure business logic."""
        # 1. Fetch data
        snapshots = await self.inventory_repo.get_all()
        
        # 2. Filter
        if warehouse:
            snapshots = [s for s in snapshots if s.warehouse_location == warehouse]
        
        # 3. Transform
        result = []
        for snapshot in snapshots:
            sku = await self.sku_repo.get_by_id(snapshot.sku_id)
            result.append({
                "sku_code": sku.sku_code,
                "quantity_available": snapshot.quantity_available,
                "reorder_needed": snapshot.quantity_available <= snapshot.reorder_point,
            })
        
        return result
```

### API Layer Usage
```python
@router.get("/api/v1/inventory/current")
async def get_inventory_current(
    warehouse: str = Query(None),
    service: ManufacturingDataService = Depends(get_data_service),
) -> InventoryCurrentResponse:
    """HTTP wrapper around service."""
    # 1. Get business data
    items = await service.get_inventory_current(warehouse=warehouse)
    
    # 2. Convert to HTTP response
    return InventoryCurrentResponse(
        total_items=len(items),
        items=[InventoryItemResponse(**item) for item in items],
    )
```

### Benefits
- ✅ **Testable**: Test business logic without HTTP server
- ✅ **Reusable**: Use same service for CLI, batch jobs, webhooks
- ✅ **Clear separation**: HTTP ↔ Business Logic boundary obvious
- ✅ **Dependency injection**: Pass session, repositories as dependencies

---

## 📝 Domain-Driven Design (DDD)

### Ubiquitous Language

Manufacturing domain terms used consistently:

| Term | Definition | Use |
|------|-----------|-----|
| **SKU** | Stock Keeping Unit | Product master identifier |
| **BOM** | Bill of Materials | Manufacturing recipe |
| **WorkOrder** | Production plan | Make 1000 units of SKU-001 |
| **Supplier** | Vendor master | Purchase components from |
| **InventorySnapshot** | Point-in-time stock | Current qty on hand |
| **SalesOrder** | Customer order | Customer wants 500 units |

### Code Reflects Language

```python
# ✅ Good - Uses manufacturing terms
class WorkOrder:
    work_order_number: str  # Not "order_id"
    quantity_ordered: float  # Not "qty_req"
    quantity_produced: float  # Not "qty_made"
    scheduled_start: datetime  # Not "start"
    
# ❌ Bad - Generic terms
class Order:
    order_id: str
    qty: float
    completed_qty: float
    date: datetime
```

### Benefits
- ✅ **Communication**: Business talks about WorkOrders, code uses WorkOrders
- ✅ **Understanding**: Reading code feels like reading business logic
- ✅ **Accuracy**: Fewer misinterpretations between teams
- ✅ **Extensibility**: New features align with domain terms

---

## 🔗 Dependency Injection

### Pattern: Constructor Injection

```python
class ManufacturingDataService:
    def __init__(self, session: AsyncSession):
        self.sku_repo = SKURepository(session)
        self.inventory_repo = InventorySnapshotRepository(session)
```

### FastAPI Integration

```python
async def get_data_service(
    session: AsyncSession = Depends(get_session),
) -> ManufacturingDataService:
    return ManufacturingDataService(session)

@router.get("/api/v1/inventory/current")
async def get_inventory_current(
    service: ManufacturingDataService = Depends(get_data_service),
):
    return await service.get_inventory_current()
```

### Benefits
- ✅ **Testable**: Inject mock repositories
- ✅ **Flexible**: Swap implementations easily
- ✅ **Explicit**: Dependencies visible in constructor
- ✅ **Lifecycle**: FastAPI handles object creation/cleanup

---

## ⚡ Async/Await Throughout

### Why Async?

**Problem**: With sync I/O, threads block waiting for database:
```
Thread 1: [ I/O wait .... ] [ I/O wait .... ]
Thread 2: [ Working ] [ I/O wait ....... ] [ Working ]
Thread 3: [ I/O wait ...... ] [ Working ] [ I/O wait ]
```

**Solution**: With async, single thread handles multiple I/O:
```
Event Loop: [I/O] → [context switch] → [I/O] → [context switch] → [I/O]
            Task 1   Task 2           Task 3   Task 1            Task 2
```

### Implementation

```python
# ✅ Async repositories
class SKURepository(BaseRepository[SKUModel]):
    async def get_by_sku_code(self, sku_code: str):
        stmt = select(SKUModel).where(SKUModel.sku_code == sku_code)
        result = await self.session.execute(stmt)  # Don't block!
        return result.scalar_one_or_none()

# ✅ Async services
class ManufacturingDataService:
    async def get_inventory_current(self, warehouse=None):
        snapshots = await self.inventory_repo.get_all()  # Non-blocking
        for snapshot in snapshots:
            sku = await self.sku_repo.get_by_id(...)  # Non-blocking
        return result

# ✅ Async routes
@router.get("/inventory/current")
async def get_inventory_current(
    service: ManufacturingDataService = Depends(get_data_service),
):
    items = await service.get_inventory_current()  # Non-blocking
    return InventoryCurrentResponse(items=items)
```

### Benefits
- ✅ **Throughput**: Handle 10x more concurrent requests
- ✅ **Scalability**: Same hardware serves more users
- ✅ **Responsiveness**: No thread context switching overhead

---

## 🛡️ Error Handling Hierarchy

### Custom Exception Classes

```python
class ServiceError(Exception):
    """Base error for all service operations."""
    def __init__(self, code: str, message: str, details=None):
        self.code = code
        self.message = message
        self.details = details or {}

class ValidationError(ServiceError):
    """Specific field validation failed."""
    pass

class NotFoundError(ServiceError):
    """Resource not found."""
    pass

class DuplicateError(ServiceError):
    """Resource already exists."""
    pass
```

### Usage in Repository

```python
class SKURepository(BaseRepository[SKUModel]):
    async def get_by_sku_code(self, sku_code: str):
        sku = await self._find_by_code(sku_code)
        if not sku:
            raise NotFoundError("SKU", sku_code)
        return sku
```

### Handling in Route

```python
@router.get("/inventory/current")
async def get_inventory_current(service: ManufacturingDataService = Depends(...)):
    try:
        items = await service.get_inventory_current()
        return InventoryCurrentResponse(items=items)
    except NotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={"code": e.code, "message": e.message}
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": e.code, "message": e.message}
        )
```

### Benefits
- ✅ **Semantic**: Error codes tell us what happened
- ✅ **Consistent**: Same error format across all APIs
- ✅ **Debugging**: Details include context
- ✅ **Client-friendly**: Structured error responses

---

## 📊 Testing Strategy

### Unit Tests (Repository)

```python
@pytest.mark.asyncio
async def test_get_by_sku_code():
    session = AsyncSession(...)
    repo = SKURepository(session)
    
    sku = await repo.get_by_sku_code("SKU-001")
    
    assert sku.sku_code == "SKU-001"
    assert sku.product_name == "Widget A"
```

### Integration Tests (Service)

```python
@pytest.mark.asyncio
async def test_get_inventory_current():
    session = AsyncSession(...)
    service = ManufacturingDataService(session)
    
    inventory = await service.get_inventory_current(warehouse="WH_SOUTH")
    
    assert len(inventory) > 0
    assert all(i["warehouse"] == "WH_SOUTH" for i in inventory)
```

### API Tests (Route)

```python
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get("/api/v1/inventory/current?warehouse=WH_SOUTH")

assert response.status_code == 200
assert response.json()["total_items"] > 0
```

---

## 🚀 Best Practices Implemented

| Practice | Implementation | Benefit |
|----------|---|---|
| **Type Hints** | All functions typed | Catch errors early |
| **Async/Await** | Throughout stack | Better throughput |
| **Dependency Injection** | Via FastAPI Depends | Easy testing |
| **Repository Pattern** | Generic + custom | Testable queries |
| **Service Layer** | Business logic isolated | Reusable logic |
| **Domain Models** | Manufacturing terms | Clear intent |
| **Error Hierarchy** | ServiceError subclasses | Proper error handling |
| **Structured Logging** | JSON format | Machine-readable logs |
| **Health Checks** | Multiple probe types | K8s ready |
| **OpenAPI Docs** | Auto-generated | Self-documenting |
| **Pagination** | Ready to implement | Scalable lists |
| **Versioning** | /api/v1/ | API evolution |

---

## 📖 Learning Resources

- **Clean Architecture**: Robert C. Martin's "Clean Code"
- **Domain-Driven Design**: Eric Evans' "DDD"
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/asyncio/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://pydantic-ai.jina.ai/

---

**Last Updated**: February 13, 2025  
**Status**: ✅ Enterprise Architecture Ready
