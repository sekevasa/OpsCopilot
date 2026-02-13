"""Domain models for unified data service - canonical manufacturing schema."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from shared.database import Base
from shared.domain_models import (
    InventoryStatus,
    WorkOrderStatus,
    SalesOrderStatus,
)


class SKUModel(Base):
    """Stock Keeping Unit - canonical product master."""

    __tablename__ = "skus"
    __table_args__ = {"schema": "manufacturing"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    sku_code = Column(String(50), unique=True, nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    uom = Column(String(10), default="EA", nullable=False)
    category = Column(String(100), nullable=False, index=True)

    supplier_id = Column(PG_UUID(as_uuid=True), nullable=True)
    unit_cost = Column(Float, nullable=False)
    list_price = Column(Float, nullable=True)
    lead_time_days = Column(Integer, default=0)

    is_active = Column(Boolean, default=True, index=True)
    is_serialized = Column(Boolean, default=False)

    attributes = Column(JSON, nullable=True)  # Custom attributes

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class BOMModel(Base):
    """Bill of Materials - manufacturing recipe."""

    __tablename__ = "boms"
    __table_args__ = {"schema": "manufacturing"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    bom_number = Column(String(50), unique=True, nullable=False, index=True)
    sku_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)

    version = Column(Integer, default=1, nullable=False)
    # [{sku_id, quantity, waste_percent}, ...]
    components = Column(JSON, nullable=False)

    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class WorkOrderModel(Base):
    """Manufacturing work order - production plan."""

    __tablename__ = "work_orders"
    __table_args__ = {"schema": "manufacturing"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    work_order_number = Column(
        String(50), unique=True, nullable=False, index=True)
    sku_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    bom_id = Column(PG_UUID(as_uuid=True), nullable=True)

    quantity_ordered = Column(Float, nullable=False)
    quantity_produced = Column(Float, default=0)
    quantity_scrapped = Column(Float, default=0)

    status = Column(SQLEnum(WorkOrderStatus),
                    default=WorkOrderStatus.CREATED, nullable=False)
    priority = Column(Integer, default=5)

    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class SupplierModel(Base):
    """Supplier master data."""

    __tablename__ = "suppliers"
    __table_args__ = {"schema": "manufacturing"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)

    contact_person = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    payment_terms = Column(String(50), default="NET30")
    is_active = Column(Boolean, default=True)
    rating = Column(Float, default=5.0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class InventorySnapshotModel(Base):
    """Point-in-time inventory snapshot."""

    __tablename__ = "inventory_snapshots"
    __table_args__ = {"schema": "manufacturing"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    sku_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    warehouse_location = Column(String(100), nullable=False)

    quantity_on_hand = Column(Float, nullable=False)
    quantity_reserved = Column(Float, default=0)
    quantity_available = Column(Float, nullable=False)

    reorder_point = Column(Float, nullable=False)
    reorder_quantity = Column(Float, nullable=False)

    status = Column(SQLEnum(InventoryStatus), default=InventoryStatus.OPTIMAL)
    last_stock_count = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class SalesOrderModel(Base):
    """Sales order from customers."""

    __tablename__ = "sales_orders"
    __table_args__ = {"schema": "manufacturing"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    sales_order_number = Column(
        String(50), unique=True, nullable=False, index=True)
    customer_id = Column(String(100), nullable=False)
    customer_name = Column(String(255), nullable=False)

    order_date = Column(DateTime, nullable=False)
    required_date = Column(DateTime, nullable=False)

    status = Column(SQLEnum(SalesOrderStatus),
                    default=SalesOrderStatus.DRAFT, nullable=False)
    total_amount = Column(Float, nullable=False)

    # [{sku_id, quantity, unit_price}, ...]
    line_items = Column(JSON, nullable=False)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
