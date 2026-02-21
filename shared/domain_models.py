"""Shared domain models and base classes for manufacturing platform."""

from datetime import datetime
from enum import Enum
from typing import Optional, Generic, TypeVar, Any, Dict, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class AuditMixin(BaseModel):
    """Mixin for audit fields."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class BaseEntity(BaseModel):
    """Base entity with ID."""

    id: UUID = Field(default_factory=uuid4)


class BaseAuditedEntity(BaseEntity, AuditMixin):
    """Base entity with ID and audit fields."""

    pass


class PaginationParams(BaseModel):
    """Pagination parameters."""

    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(
        10, ge=1, le=100, description="Maximum records to return")


class PagedResponse(BaseModel, Generic[TypeVar("T")]):
    """Paginated response wrapper."""

    items: list
    total: int
    skip: int
    limit: int

    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        return (self.total + self.limit - 1) // self.limit


class ServiceError(Exception):
    """Base service error."""

    def __init__(self, code: str, message: str, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationError(ServiceError):
    """Validation error."""

    def __init__(self, field: str, message: str):
        super().__init__("VALIDATION_ERROR",
                         f"{field}: {message}", {"field": field})


class NotFoundError(ServiceError):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            "NOT_FOUND",
            f"{resource} not found: {identifier}",
            {"resource": resource, "identifier": identifier}
        )


class DuplicateError(ServiceError):
    """Duplicate resource error."""

    def __init__(self, resource: str, field: str, value: str):
        super().__init__(
            "DUPLICATE",
            f"{resource} with {field}='{value}' already exists",
            {"resource": resource, "field": field, "value": value}
        )


# ============================================================================
# MANUFACTURING DOMAIN ENUMS
# ============================================================================

class DataSourceType(str, Enum):
    """Types of data sources."""
    ERP = "erp"
    ACCOUNTING = "accounting"
    INVENTORY_SYSTEM = "inventory_system"
    QUALITY_CONTROL = "quality_control"
    PRODUCTION = "production"
    EXTERNAL_API = "external_api"
    TALLY = "tally"


class IngestionStatus(str, Enum):
    """Status of data ingestion."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_FAILED = "partially_failed"


class InventoryStatus(str, Enum):
    """Inventory level status."""
    CRITICAL = "critical"
    LOW = "low"
    OPTIMAL = "optimal"
    EXCESS = "excess"


class WorkOrderStatus(str, Enum):
    """Manufacturing work order status."""
    CREATED = "created"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class SalesOrderStatus(str, Enum):
    """Sales order status."""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============================================================================
# MANUFACTURING DOMAIN MODELS
# ============================================================================

class SKU(BaseAuditedEntity):
    """Stock Keeping Unit - represents a physical product."""

    sku_code: str = Field(..., description="Unique SKU identifier")
    product_name: str = Field(..., description="Product name")
    description: Optional[str] = None
    uom: str = Field("EA", description="Unit of Measure (EA, KG, etc.)")
    category: str = Field(..., description="Product category")
    supplier_id: Optional[UUID] = None
    unit_cost: float = Field(..., ge=0, description="Cost per unit")
    lead_time_days: int = Field(0, ge=0, description="Lead time in days")
    is_active: bool = Field(True, description="Is SKU active")

    class Config:
        use_enum_values = True


class BOM(BaseAuditedEntity):
    """Bill of Materials - recipe for manufacturing."""

    bom_number: str = Field(..., description="Unique BOM identifier")
    product_sku_id: UUID = Field(..., description="SKU being manufactured")
    version: int = Field(1, ge=1, description="BOM version number")
    components: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of component SKUs and quantities"
    )
    # Example: [{"sku_id": "...", "quantity": 5, "waste_percent": 2}]
    is_active: bool = Field(True)

    class Config:
        use_enum_values = True


class WorkOrder(BaseAuditedEntity):
    """Manufacturing work order."""

    work_order_number: str = Field(..., description="Unique WO identifier")
    sku_id: UUID = Field(..., description="SKU to manufacture")
    bom_id: UUID = Field(..., description="BOM to use")
    quantity_ordered: float = Field(..., gt=0,
                                    description="Quantity to produce")
    quantity_produced: float = Field(0, ge=0, description="Quantity produced")
    status: WorkOrderStatus = Field(WorkOrderStatus.CREATED)
    scheduled_start: datetime = Field(..., description="Scheduled start date")
    scheduled_end: datetime = Field(..., description="Scheduled end date")
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    priority: int = Field(5, ge=1, le=10, description="Priority 1-10")
    notes: Optional[str] = None

    class Config:
        use_enum_values = True


class Supplier(BaseAuditedEntity):
    """Supplier master data."""

    supplier_code: str = Field(..., description="Unique supplier identifier")
    supplier_name: str = Field(..., description="Legal supplier name")
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    payment_terms: str = Field("NET30", description="Payment terms")
    is_active: bool = Field(True)
    rating: float = Field(5.0, ge=1, le=5, description="Supplier rating")

    class Config:
        use_enum_values = True


class InventorySnapshot(BaseAuditedEntity):
    """Point-in-time inventory snapshot."""

    sku_id: UUID = Field(..., description="SKU in inventory")
    warehouse_location: str = Field(..., description="Warehouse/location code")
    quantity_on_hand: float = Field(..., ge=0,
                                    description="Qty currently in stock")
    quantity_reserved: float = Field(
        0, ge=0, description="Qty reserved for orders")
    quantity_available: float = Field(..., ge=0,
                                      description="Qty available for sale")
    reorder_point: float = Field(..., ge=0,
                                 description="Min qty before reorder")
    reorder_quantity: float = Field(..., gt=0,
                                    description="Standard reorder qty")
    status: InventoryStatus = Field(InventoryStatus.OPTIMAL)
    last_stock_count: datetime = Field(...,
                                       description="Last physical inventory count")

    class Config:
        use_enum_values = True


class SalesOrder(BaseAuditedEntity):
    """Sales order from customer."""

    sales_order_number: str = Field(..., description="Unique SO identifier")
    customer_id: str = Field(..., description="Customer identifier")
    customer_name: str = Field(..., description="Customer name")
    order_date: datetime = Field(..., description="Order date")
    required_date: datetime = Field(..., description="Required by date")
    status: SalesOrderStatus = Field(SalesOrderStatus.DRAFT)
    total_amount: float = Field(..., ge=0, description="Total order amount")
    line_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of order line items"
    )
    # Example: [{"sku_id": "...", "quantity": 10, "unit_price": 50}]
    notes: Optional[str] = None

    class Config:
        use_enum_values = True
