"""Pydantic schemas for unified data service."""

from datetime import datetime
from typing import Optional, Any, Dict, List
from uuid import UUID
from pydantic import BaseModel, Field
from shared.domain_models import InventoryStatus, WorkOrderStatus, SalesOrderStatus


# ============================================================================
# INVENTORY SCHEMAS
# ============================================================================

class InventoryItemResponse(BaseModel):
    """Response for an inventory item."""

    sku_code: str
    product_name: str
    warehouse: str
    quantity_on_hand: float
    quantity_reserved: float
    quantity_available: float
    status: InventoryStatus
    reorder_point: float
    reorder_needed: bool


class InventoryCurrentResponse(BaseModel):
    """Response for current inventory."""

    total_items: int
    items: List[InventoryItemResponse]
    as_of: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# SALES ORDER SCHEMAS
# ============================================================================

class SalesOrderLineItem(BaseModel):
    """Line item in sales order."""

    sku_code: str
    quantity: float
    unit_price: float


class SalesOrderResponse(BaseModel):
    """Response for sales order."""

    sales_order_number: str
    customer_name: str
    order_date: datetime
    required_date: datetime
    status: SalesOrderStatus
    total_amount: float
    line_count: int


class OpenOrdersResponse(BaseModel):
    """Response for open orders."""

    total_orders: int
    orders: List[SalesOrderResponse]
    total_value: float = Field(0, description="Total $ value of open orders")


# ============================================================================
# SUPPLIER SCHEMAS
# ============================================================================

class SupplierResponse(BaseModel):
    """Response for supplier."""

    supplier_code: str
    supplier_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    rating: float
    is_active: bool


class SuppliersResponse(BaseModel):
    """Response for supplier list."""

    total_suppliers: int
    suppliers: List[SupplierResponse]


# ============================================================================
# PRODUCTION STATUS SCHEMAS
# ============================================================================

class ProductionStatusResponse(BaseModel):
    """Response for production status."""

    total_work_orders: int
    open_work_orders: int
    total_quantity_ordered: float
    total_quantity_produced: float
    production_rate: float = Field(..., ge=0,
                                   le=100, description="Percentage complete")


# ============================================================================
# DATA QUALITY SCHEMAS
# ============================================================================

class ValidationIssue(BaseModel):
    """A data validation issue."""

    sku_id: str
    warehouse: str
    issue: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None


class DataQualityResponse(BaseModel):
    """Response for data quality check."""

    total_records_checked: int
    issues_found: int
    issues: List[ValidationIssue]


# ============================================================================
# HEALTH SCHEMAS
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime
    database: str = Field("unknown", description="Database connection status")
