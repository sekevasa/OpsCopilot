"""API routes for unified data service."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import db
from shared.domain_models import ServiceError
from datetime import datetime

from ..domain.schemas import (
    InventoryCurrentResponse,
    InventoryItemResponse,
    OpenOrdersResponse,
    SalesOrderResponse,
    SuppliersResponse,
    SupplierResponse,
    ProductionStatusResponse,
    DataQualityResponse,
    HealthResponse,
)
from ..services import ManufacturingDataService


router = APIRouter(prefix="/api/v1", tags=["unified-data"])


async def get_session() -> AsyncSession:
    """Get database session."""
    return db.get_session()


async def get_data_service(
    session: AsyncSession = Depends(get_session),
) -> ManufacturingDataService:
    """Dependency for data service."""
    return ManufacturingDataService(session)


# ============================================================================
# INVENTORY ENDPOINTS
# ============================================================================

@router.get(
    "/inventory/current",
    response_model=InventoryCurrentResponse,
)
async def get_inventory_current(
    warehouse: str = Query(None, description="Filter by warehouse location"),
    service: ManufacturingDataService = Depends(get_data_service),
) -> InventoryCurrentResponse:
    """
    Get current inventory snapshot.

    Returns latest inventory levels across all locations or specific warehouse.
    Includes reorder status and quantity available.
    """
    try:
        items = await service.get_inventory_current(warehouse=warehouse)

        return InventoryCurrentResponse(
            total_items=len(items),
            items=[InventoryItemResponse(**item) for item in items],
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )


# ============================================================================
# SALES ORDER ENDPOINTS
# ============================================================================

@router.get(
    "/orders/open",
    response_model=OpenOrdersResponse,
)
async def get_open_orders(
    service: ManufacturingDataService = Depends(get_data_service),
) -> OpenOrdersResponse:
    """
    Get all open sales orders.

    Returns confirmed and partial orders that require fulfillment.
    """
    try:
        orders = await service.get_orders_open()
        total_value = sum(o["total_amount"] for o in orders)

        return OpenOrdersResponse(
            total_orders=len(orders),
            orders=[SalesOrderResponse(**order) for order in orders],
            total_value=total_value,
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )


# ============================================================================
# SUPPLIER ENDPOINTS
# ============================================================================

@router.get(
    "/suppliers",
    response_model=SuppliersResponse,
)
async def get_suppliers(
    active_only: bool = Query(
        True, description="Only return active suppliers"),
    service: ManufacturingDataService = Depends(get_data_service),
) -> SuppliersResponse:
    """
    Get supplier master data.

    Returns list of suppliers with contact and rating information.
    """
    try:
        suppliers = await service.get_suppliers(active_only=active_only)

        return SuppliersResponse(
            total_suppliers=len(suppliers),
            suppliers=[SupplierResponse(**supplier) for supplier in suppliers],
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )


# ============================================================================
# PRODUCTION STATUS ENDPOINTS
# ============================================================================

@router.get(
    "/production/status",
    response_model=ProductionStatusResponse,
)
async def get_production_status(
    service: ManufacturingDataService = Depends(get_data_service),
) -> ProductionStatusResponse:
    """
    Get overall production status.

    Returns summary of work orders and production metrics.
    """
    try:
        status_data = await service.get_production_status()
        return ProductionStatusResponse(**status_data)
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )


# ============================================================================
# DATA QUALITY ENDPOINTS
# ============================================================================

@router.get(
    "/quality/inventory-check",
    response_model=DataQualityResponse,
)
async def check_inventory_quality(
    service: ManufacturingDataService = Depends(get_data_service),
) -> DataQualityResponse:
    """
    Check inventory data for quality issues.

    Validates consistency (on-hand vs. available) and business rules.
    """
    try:
        report = await service.validate_inventory_consistency()
        return DataQualityResponse(**report)
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )


# ============================================================================
# HEALTH ENDPOINTS
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check(
    session: AsyncSession = Depends(get_session),
) -> HealthResponse:
    """Health check endpoint."""
    db_status = "connected"
    try:
        await session.execute("SELECT 1")
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service="unified-data-service",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        database=db_status,
    )


@router.get("/health/ready")
async def readiness_check():
    """Readiness probe for Kubernetes."""
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}
