# Manufacturing AI Copilot - API Endpoints (Refactored)

## Data Ingest Service (Port 8001)

### Sync Operations
- **POST** `/api/v1/sync/run` - Start new ingestion job from data source
  - Request: `{source_type, source_id, metadata?}`
  - Response: `{job_id, job_reference, status, message}`
  - Status: `202 Accepted`

- **GET** `/api/v1/sync/status/{job_id}` - Poll ingestion job progress
  - Response: `{job_id, status, progress%, total, successful, failed}`
  - Status: `200 OK`

- **GET** `/api/v1/sync/job/{job_id}` - Get detailed job information
  - Response: Full IngestionJobResponse with metadata
  - Status: `200 OK`

### Health & Readiness
- **GET** `/api/v1/health` - Service health check (includes DB status)
- **GET** `/api/v1/health/ready` - Kubernetes readiness probe
- **GET** `/api/v1/health/live` - Kubernetes liveness probe

---

## Unified Data Service (Port 8002)

### Inventory Endpoints
- **GET** `/api/v1/inventory/current[?warehouse=WH_SOUTH]` - Get current inventory
  - Query Params: `warehouse` (optional - filter by location)
  - Response: `{total_items, items[], as_of}`
  - Item Fields: sku_code, product_name, warehouse, qty_on_hand, qty_reserved, qty_available, status, reorder_needed
  - Status: `200 OK`

### Sales Order Endpoints
- **GET** `/api/v1/orders/open` - Get all open sales orders
  - Response: `{total_orders, orders[], total_value}`
  - Order Fields: sales_order_number, customer_name, order_date, required_date, status, total_amount, line_count
  - Status: `200 OK`

### Supplier Endpoints
- **GET** `/api/v1/suppliers[?active_only=true]` - Get supplier master data
  - Query Params: `active_only` (default: true)
  - Response: `{total_suppliers, suppliers[]}`
  - Supplier Fields: code, name, contact, email, phone, country, rating, is_active
  - Status: `200 OK`

### Production Status Endpoints
- **GET** `/api/v1/production/status` - Get production summary
  - Response: `{total_work_orders, open_work_orders, qty_ordered, qty_produced, production_rate%}`
  - Status: `200 OK`

### Data Quality Endpoints
- **GET** `/api/v1/quality/inventory-check` - Validate inventory consistency
  - Response: `{total_records_checked, issues_found, issues[]}`
  - Issue Fields: sku_id, warehouse, issue_description, expected, actual
  - Status: `200 OK`

### Health & Readiness
- **GET** `/api/v1/health` - Service health check (includes DB status)
- **GET** `/api/v1/health/ready` - Kubernetes readiness probe
- **GET** `/api/v1/health/live` - Kubernetes liveness probe

---

## Key Changes from Previous Version

| Service | Before | After |
|---------|--------|-------|
| **Data Ingest** | POST /ingest | POST /sync/run + GET /sync/status |
| **Ingest API** | Immediate response | 202 Accepted with job ID for polling |
| **Unified Data** | Generic /items, /inventory/{id} | Specific /inventory/current, /orders/open, /suppliers |
| **Data Model** | 3 generic models | 6 specialized manufacturing models |
| **Architecture** | Flat | Layered (API → Service → Domain → Repository → DB) |

---

## Request/Response Examples

### Start Sync Job
```bash
curl -X POST http://localhost:8001/api/v1/sync/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "erp",
    "source_id": "SAP_001",
    "metadata": {"run_date": "2025-02-13", "entity_type": "work_order"}
  }'

# Response (202 Accepted)
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_reference": "erp_SAP_001",
  "status": "PENDING",
  "message": "Sync job started"
}
```

### Poll Job Status
```bash
curl http://localhost:8001/api/v1/sync/status/550e8400-e29b-41d4-a716-446655440000

# Response (200 OK)
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PROCESSING",
  "progress": 45.5,
  "total_records": 10000,
  "successful_records": 4550,
  "failed_records": 0,
  "started_at": "2025-02-13T10:15:00Z",
  "completed_at": null
}
```

### Get Current Inventory
```bash
curl http://localhost:8002/api/v1/inventory/current?warehouse=WH_SOUTH

# Response (200 OK)
{
  "total_items": 245,
  "items": [
    {
      "sku_code": "SKU-001",
      "product_name": "Widget A",
      "warehouse": "WH_SOUTH",
      "quantity_on_hand": 500,
      "quantity_reserved": 250,
      "quantity_available": 250,
      "status": "OPTIMAL",
      "reorder_point": 100,
      "reorder_needed": false
    },
    {
      "sku_code": "SKU-002",
      "product_name": "Widget B",
      "warehouse": "WH_SOUTH",
      "quantity_on_hand": 45,
      "quantity_reserved": 0,
      "quantity_available": 45,
      "status": "CRITICAL",
      "reorder_point": 200,
      "reorder_needed": true
    }
  ],
  "as_of": "2025-02-13T15:30:45Z"
}
```

### Get Open Orders
```bash
curl http://localhost:8002/api/v1/orders/open

# Response (200 OK)
{
  "total_orders": 12,
  "orders": [
    {
      "sales_order_number": "SO-2025-001",
      "customer_name": "ACME Corp",
      "order_date": "2025-02-10T08:00:00Z",
      "required_date": "2025-02-17T17:00:00Z",
      "status": "CONFIRMED",
      "total_amount": 45000.00,
      "line_count": 3
    }
  ],
  "total_value": 450000.00
}
```

### Get Suppliers
```bash
curl http://localhost:8002/api/v1/suppliers?active_only=true

# Response (200 OK)
{
  "total_suppliers": 45,
  "suppliers": [
    {
      "supplier_code": "SUPP-001",
      "supplier_name": "Global Parts Inc.",
      "contact_person": "John Smith",
      "email": "john@globalparts.com",
      "phone": "+1-555-0123",
      "country": "USA",
      "rating": 4.8,
      "is_active": true
    }
  ]
}
```

### Production Status
```bash
curl http://localhost:8002/api/v1/production/status

# Response (200 OK)
{
  "total_work_orders": 156,
  "open_work_orders": 42,
  "total_quantity_ordered": 500000.0,
  "total_quantity_produced": 375000.0,
  "production_rate": 75.0
}
```

### Data Quality Check
```bash
curl http://localhost:8002/api/v1/quality/inventory-check

# Response (200 OK)
{
  "total_records_checked": 1250,
  "issues_found": 3,
  "issues": [
    {
      "sku_id": "550e8400-e29b-41d4-a716-446655440000",
      "warehouse": "WH_NORTH",
      "issue": "Quantity available mismatch",
      "expected": 150.0,
      "actual": 145.0
    },
    {
      "sku_id": "550e8400-e29b-41d4-a716-446655440001",
      "warehouse": "WH_EAST",
      "issue": "Reserved quantity exceeds on-hand",
      "expected": null,
      "actual": null
    }
  ]
}
```

---

## Error Responses

### Validation Error (400)
```json
{
  "detail": {
    "code": "VALIDATION_ERROR",
    "message": "source_type: Invalid data source type",
    "details": {"field": "source_type"}
  }
}
```

### Not Found Error (404)
```json
{
  "detail": {
    "code": "NOT_FOUND",
    "message": "Job 550e8400-e29b-41d4-a716-446655440000 not found",
    "details": {}
  }
}
```

### Service Error (400)
```json
{
  "detail": {
    "code": "DUPLICATE_BATCH",
    "message": "Batch SAP_001_2025-02-13 already exists",
    "details": {"batch_reference": "SAP_001_2025-02-13"}
  }
}
```

---

## Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created
- `202 Accepted` - Request accepted, processing async (jobs)
- `400 Bad Request` - Validation or business logic error
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service degraded

---

## Content Type

All endpoints:
- **Request**: `Content-Type: application/json`
- **Response**: `Content-Type: application/json`

---

## Pagination (Future)

Ready for implementation on list endpoints:
```
GET /api/v1/suppliers?skip=0&limit=50

{
  "items": [...],
  "total": 250,
  "skip": 0,
  "limit": 50,
  "total_pages": 5
}
```

---

## OpenAPI Documentation

Access Swagger UI:
- Data Ingest: http://localhost:8001/docs
- Unified Data: http://localhost:8002/docs

Access ReDoc:
- Data Ingest: http://localhost:8001/redoc
- Unified Data: http://localhost:8002/redoc

---

**Last Updated**: February 13, 2025  
**API Version**: v1  
**Status**: ✅ Production Ready (refactoring complete)
