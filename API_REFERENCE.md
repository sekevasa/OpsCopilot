# API Reference

## Overview

All services follow REST conventions with consistent response formats.

## Response Format

### Success Response
```json
{
  "id": "uuid",
  "status": "success",
  "data": { /* response body */ },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { /* error details */ }
  }
}
```

## Common Error Codes

| Code | Status | Meaning |
|------|--------|---------|
| VALIDATION_ERROR | 400 | Invalid input data |
| NOT_FOUND | 404 | Resource not found |
| DUPLICATE | 400 | Resource already exists |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Permission denied |
| INTERNAL_ERROR | 500 | Server error |

## Data Ingest Service

### POST /api/v1/ingest

Ingest data batch from external system.

**Request**:
```json
{
  "source_type": "erp|accounting|inventory|sales",
  "source_id": "external_system_id",
  "batch_reference": "unique_batch_id",
  "data": {
    "items": [
      {"sku": "ITEM-001", "name": "Component A"}
    ]
  }
}
```

**Response** (202 Accepted):
```json
{
  "batch_id": "uuid",
  "status": "pending",
  "message": "Batch queued for processing"
}
```

### GET /api/v1/batch/{batch_id}

Get batch status and details.

**Response** (200 OK):
```json
{
  "id": "uuid",
  "source_type": "erp",
  "batch_reference": "batch_001",
  "status": "success|pending|in_progress|failed",
  "record_count": 100,
  "ingested_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:35:00Z",
  "error_message": null
}
```

### GET /api/v1/health

Health check.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "data-ingest-service",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Unified Data Service

### POST /api/v1/items

Create or update manufacturing item.

**Request**:
```json
{
  "sku": "ITEM-001",
  "name": "Component A",
  "description": "Industrial component",
  "uom": "EA",
  "standard_cost": 50.00,
  "supplier_id": "SUPP-001",
  "supplier_name": "Supplier X"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "sku": "ITEM-001",
  "name": "Component A",
  "uom": "EA",
  "status": "active",
  "standard_cost": 50.00,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### GET /api/v1/items/{sku}

Get manufacturing item by SKU.

**Response** (200 OK):
```json
{
  "id": "uuid",
  "sku": "ITEM-001",
  "name": "Component A",
  "uom": "EA",
  "status": "active",
  "standard_cost": 50.00,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /api/v1/inventory/{item_id}

Get latest inventory snapshot for item.

**Response** (200 OK):
```json
{
  "id": "uuid",
  "item_id": "uuid",
  "warehouse_id": "WH001",
  "quantity_on_hand": 1000,
  "quantity_reserved": 100,
  "quantity_available": 900,
  "reorder_point": 500,
  "snapshot_date": "2024-01-15T10:30:00Z"
}
```

## AI Runtime Service

### POST /api/v1/infer

Run inference on AI model.

**Request**:
```json
{
  "model_name": "demand-predictor",
  "input_data": {
    "historical_demand": 1000,
    "seasonality": 1.2,
    "promotion_flag": true
  },
  "timeout_seconds": 30
}
```

**Response** (200 OK):
```json
{
  "job_id": "uuid",
  "model_name": "demand-predictor",
  "status": "completed|pending|running|failed",
  "output_data": {
    "prediction": 1200,
    "confidence": 0.95
  },
  "execution_time_ms": 150,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:01Z"
}
```

## Forecast Service

### POST /api/v1/forecasts

Generate forecast for entity.

**Request**:
```json
{
  "forecast_type": "demand|inventory|supply|quality",
  "period": "daily|weekly|monthly|quarterly",
  "entity_id": "ITEM-001",
  "entity_type": "item|warehouse|process",
  "lookback_days": 365
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "forecast_type": "demand",
  "period": "monthly",
  "entity_id": "ITEM-001",
  "forecast_value": 5000,
  "forecast_lower_bound": 4000,
  "forecast_upper_bound": 6000,
  "confidence_level": 0.85,
  "model_name": "exponential_smoothing",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /api/v1/forecasts/{entity_id}/{forecast_type}

Get latest forecast.

**Response** (200 OK):
```json
{
  "id": "uuid",
  "forecast_type": "demand",
  "entity_id": "ITEM-001",
  "forecast_value": 5000,
  "forecast_lower_bound": 4000,
  "forecast_upper_bound": 6000,
  "confidence_level": 0.85,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /api/v1/alerts/active

Get active forecast alerts.

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "forecast_id": "uuid",
    "alert_type": "stockout_risk",
    "severity": "critical",
    "description": "Projected inventory below reorder point",
    "recommended_action": "Increase purchase order",
    "acknowledged": "pending",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

## Notification Service

### POST /api/v1/send

Send notification to user.

**Request**:
```json
{
  "user_id": "user123",
  "title": "Inventory Alert",
  "message": "Critical stock level for ITEM-001",
  "notification_type": "alert",
  "severity": "critical",
  "channel": "email|sms|slack|webhook|push",
  "metadata": {
    "item_id": "ITEM-001",
    "current_qty": 50
  }
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "user_id": "user123",
  "title": "Inventory Alert",
  "message": "Critical stock level for ITEM-001",
  "channel": "email",
  "status": "sent|pending|failed",
  "severity": "critical",
  "sent_at": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### POST /api/v1/preferences

Set notification preferences.

**Request**:
```json
{
  "user_id": "user123",
  "email": "user@example.com",
  "phone": "+1234567890",
  "email_enabled": true,
  "sms_enabled": false,
  "notify_on_critical": true,
  "notify_on_high": true,
  "notify_on_medium": false
}
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "user_id": "user123",
  "email": "user@example.com",
  "phone": "+1234567890",
  "email_enabled": true,
  "sms_enabled": false,
  "notify_on_critical": true,
  "notify_on_high": true
}
```

## Rate Limiting (Future)

Rate limits per service:
- Ingest: 1000 req/min
- Data queries: 5000 req/min
- Inference: 100 req/min
- Notifications: 10000 req/min

## Pagination

List endpoints support pagination:

**Query Parameters**:
- `skip`: Offset (default: 0)
- `limit`: Maximum results (default: 10, max: 100)

**Response**:
```json
{
  "items": [ /* results */ ],
  "total": 1000,
  "skip": 0,
  "limit": 10,
  "total_pages": 100
}
```

## Webhooks (Future)

Services can be configured to send webhook events:

```json
{
  "event_type": "batch.completed|forecast.generated|alert.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": { /* event data */ }
}
```
