# New API Endpoints Reference - Phase 3

Quick reference for all new and updated endpoints added in Phase 3.

---

## AI Runtime Service - Copilot API

### POST /api/v1/copilot/query
**Process a copilot query with tool orchestration**

```json
Request:
{
  "query": "What's the current inventory level for SKU ABC123?",
  "session_id": "user-123-session-456",
  "context_hints": {
    "entity_type": "sku",
    "entity_id": "ABC123"
  },
  "max_tools": 3
}

Response:
{
  "message": "Based on the available data: ... Current inventory: 250 units",
  "tool_calls": [
    {
      "tool_name": "query_inventory",
      "arguments": {"sku_code": "ABC123"},
      "result": {"qty_available": 250, "warehouse": "WH-01"},
      "error": null,
      "timestamp": "2024-12-19T10:30:00"
    }
  ],
  "context_used": {
    "inventory": {...},
    "insights": {...}
  },
  "confidence": 0.92,
  "timestamp": "2024-12-19T10:30:00"
}
```

**Status Code**: 200 OK | 500 Internal Server Error

---

### GET /api/v1/copilot/session/{session_id}/history
**Retrieve conversation history for a session**

```json
Request:
GET /api/v1/copilot/session/user-123-session-456/history

Response:
{
  "session_id": "user-123-session-456",
  "messages": [
    {
      "message_id": "msg-001",
      "role": "user",
      "content": "What's the current inventory?",
      "timestamp": "2024-12-19T10:25:00",
      "metadata": {}
    },
    {
      "message_id": "msg-002",
      "role": "assistant",
      "content": "Current inventory is 250 units...",
      "timestamp": "2024-12-19T10:25:30",
      "metadata": {"tool_calls": 1, "confidence": 0.92}
    }
  ],
  "summary": {
    "total_messages": 2,
    "user_messages": 1,
    "assistant_messages": 1,
    "duration_seconds": 30,
    "context_keys": ["entity_id", "warehouse"]
  }
}
```

**Status Code**: 200 OK | 404 Not Found (session not found)

---

### DELETE /api/v1/copilot/session/{session_id}
**Delete a conversation session**

```json
Request:
DELETE /api/v1/copilot/session/user-123-session-456

Response:
{
  "message": "Session deleted: user-123-session-456"
}
```

**Status Code**: 200 OK | 404 Not Found

---

### GET /api/v1/copilot/tools
**List all available tools in the copilot**

```json
Response:
{
  "available_tools": 5,
  "tools": [
    {
      "name": "query_inventory",
      "description": "Query current inventory levels",
      "input_schema": {
        "sku_code": "string",
        "warehouse": "string (optional)"
      }
    },
    {
      "name": "lookup_orders",
      "description": "Look up sales orders by customer",
      "input_schema": {
        "customer_id": "string",
        "date_from": "string (optional)"
      }
    },
    {
      "name": "check_production",
      "description": "Check production metrics and status",
      "input_schema": {
        "work_order_id": "string"
      }
    },
    {
      "name": "get_forecast",
      "description": "Get demand forecasts",
      "input_schema": {
        "sku_code": "string",
        "horizon_days": "integer (optional)"
      }
    },
    {
      "name": "manage_alerts",
      "description": "Create or manage alerts",
      "input_schema": {
        "action": "string (create|acknowledge|resolve)",
        "alert_id": "string (optional)"
      }
    }
  ]
}
```

**Status Code**: 200 OK | 500 Internal Server Error

---

## Forecast Service - Demand & Risk API

### POST /api/v1/forecast/demand
**Generate demand forecast with confidence intervals**

```json
Request:
{
  "entity_id": "SKU-ABC-123",
  "entity_type": "sku",
  "period": "weekly",
  "horizon_days": 30,
  "lookback_days": 365
}

Response:
{
  "entity_id": "SKU-ABC-123",
  "forecast_type": "demand",
  "period": "weekly",
  "forecast_values": [100, 105, 98, 110, 102],
  "forecast_dates": [
    "2024-12-26",
    "2025-01-02",
    "2025-01-09",
    "2025-01-16",
    "2025-01-23"
  ],
  "confidence_intervals": {
    "upper": [110, 115.5, 107.8, 121, 112.2],
    "lower": [90, 94.5, 88.2, 99, 91.8]
  },
  "confidence_level": 85.0,
  "model_name": "exponential_smoothing",
  "created_at": "2024-12-19T10:30:00"
}
```

**Status Code**: 201 Created | 400 Bad Request | 500 Internal Server Error

---

### POST /api/v1/forecast/inventory-risk
**Forecast inventory risk and stockout probability**

```json
Request:
{
  "entity_id": "SKU-ABC-123",
  "warehouse_id": "WH-01",
  "lookback_days": 365,
  "reorder_point": 100
}

Response:
{
  "entity_id": "SKU-ABC-123",
  "warehouse_id": "WH-01",
  "risk_level": "medium",
  "stockout_probability": 0.35,
  "days_until_critical": 7,
  "recommended_reorder_qty": 250,
  "current_velocity": 3.2,
  "forecast_demand": 96,
  "risk_factors": [
    "Inventory below reorder point",
    "High consumption rate"
  ],
  "timestamp": "2024-12-19T10:30:00"
}
```

**Risk Levels**: 
- `critical`: Stockout probability > 80%
- `high`: Stockout probability 50-80%
- `medium`: Stockout probability 20-50%
- `low`: Stockout probability < 20%

**Status Code**: 200 OK | 400 Bad Request | 500 Internal Server Error

---

## Notification Service - Alert & Channel API

### POST /api/v1/notify/email
**Send email notification**

```json
Request:
{
  "recipient_email": "user@example.com",
  "subject": "Inventory Alert - SKU ABC-123",
  "body": "SKU ABC-123 is below reorder point",
  "html_body": "<h1>Inventory Alert</h1><p>SKU ABC-123 is below reorder point</p>",
  "priority": "high",
  "tags": ["inventory", "alert", "urgent"],
  "metadata": {
    "sku": "ABC-123",
    "quantity": 50
  }
}

Response:
{
  "notification_id": "notif-6d7c4e3b",
  "recipient_email": "user@example.com",
  "subject": "Inventory Alert - SKU ABC-123",
  "status": "sent",
  "timestamp": "2024-12-19T10:30:00",
  "delivery_status": "pending",
  "send_attempts": 1
}
```

**Priority Levels**: critical, high, medium, low, info

**Status Code**: 201 Created | 400 Bad Request | 500 Internal Server Error

---

### POST /api/v1/notify/alert
**Send multi-channel alert**

```json
Request:
{
  "user_id": "user-123",
  "alert_title": "Critical Inventory Alert",
  "alert_message": "SKU ABC-123 stock critically low at 5 units",
  "severity": "critical",
  "channels": ["email", "slack"],
  "alert_type": "inventory",
  "source_entity": "SKU-ABC-123",
  "action_required": true,
  "ttl_hours": 24
}

Response:
{
  "alert_id": "alert-1734689400.123",
  "user_id": "user-123",
  "alert_title": "Critical Inventory Alert",
  "severity": "critical",
  "channels_notified": ["email", "slack"],
  "channels_failed": [],
  "status": "pending",
  "created_at": "2024-12-19T10:30:00",
  "expires_at": "2024-12-20T10:30:00"
}
```

**Alert Types**: system, inventory, production, quality  
**Severity Levels**: critical, high, medium, low, info

**Status Code**: 201 Created | 500 Internal Server Error

---

### POST /api/v1/notify/alert/{alert_id}/acknowledge
**Acknowledge an alert**

```json
Request:
POST /api/v1/notify/alert/alert-1734689400.123/acknowledge
{
  "acknowledged_by": "user-123",
  "acknowledgment_message": "Inventory reorder in progress"
}

Response:
{
  "alert_id": "alert-1734689400.123",
  "acknowledged_by": "user-123",
  "acknowledged_at": "2024-12-19T10:35:00",
  "status": "acknowledged"
}
```

**Status Code**: 200 OK | 500 Internal Server Error

---

### POST /api/v1/notify/preferences
**Update notification preferences**

```json
Request:
{
  "user_id": "user-123",
  "email": "user@example.com",
  "phone": "+1-555-0123",
  "slack_webhook": "https://hooks.slack.com/...",
  "enabled_channels": ["email", "slack", "sms"],
  "notify_on_critical": true,
  "notify_on_high": true,
  "notify_on_medium": false,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "18:00",
  "quiet_hours_end": "08:00"
}

Response:
{
  "user_id": "user-123",
  "enabled_channels": ["email", "slack", "sms"],
  "notify_on_critical": true,
  "notify_on_high": true,
  "notify_on_medium": false,
  "quiet_hours_enabled": true,
  "updated_at": "2024-12-19T10:30:00"
}
```

**Status Code**: 200 OK | 400 Bad Request | 500 Internal Server Error

---

### GET /api/v1/notify/channels
**List available notification channels**

```json
Response:
{
  "channels": [
    {
      "name": "email",
      "description": "Email notifications",
      "requires_config": ["recipient_email"]
    },
    {
      "name": "slack",
      "description": "Slack messages",
      "requires_config": ["slack_webhook_url"]
    },
    {
      "name": "sms",
      "description": "SMS text messages",
      "requires_config": ["phone_number"]
    },
    {
      "name": "webhook",
      "description": "HTTP webhook callbacks",
      "requires_config": ["webhook_url"]
    }
  ]
}
```

**Status Code**: 200 OK

---

## Common HTTP Status Codes

| Code | Meaning | Notes |
|------|---------|-------|
| 200 | OK | Successful GET/DELETE request |
| 201 | Created | Successful POST request (resource created) |
| 400 | Bad Request | Invalid input parameters or validation error |
| 404 | Not Found | Resource (session, alert) not found |
| 500 | Internal Server Error | Unexpected server error |

---

## Authentication & Rate Limiting

**Recommended** (not yet implemented):
- API key authentication on all endpoints
- Rate limiting: 100 requests/minute per user
- JWT token validation for multi-tenant support

---

## Example Usage Flows

### Flow 1: Copilot Inventory Query
```
1. POST /api/v1/copilot/query
   → "What's the stock level for SKU ABC-123?"
2. Copilot processes query → selects query_inventory tool
3. Calls Unified Data Service to fetch inventory
4. Returns response with 92% confidence
5. GET /api/v1/copilot/session/{id}/history
   → Retrieve conversation for context
```

### Flow 2: Inventory Risk & Alert
```
1. POST /api/v1/forecast/inventory-risk
   → SKU ABC-123 at medium risk
2. POST /api/v1/notify/alert
   → Send alert to operations team via email + Slack
3. POST /api/v1/notify/alert/{id}/acknowledge
   → Operations team acknowledges alert
```

### Flow 3: Demand Planning
```
1. POST /api/v1/forecast/demand
   → Get 30-day demand forecast with confidence intervals
2. POST /api/v1/notify/email
   → Send forecast report to procurement team
3. Procurement uses forecast to optimize orders
```

---

**Last Updated**: December 2024  
**API Version**: v1  
**All endpoints require**: Content-Type: application/json
