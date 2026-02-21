"""Pydantic models and schemas for the Tally Prime 7 connector."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# ENUMS
# ============================================================================

class TallyDataType(str, Enum):
    """Supported Tally data types for extraction."""
    MASTERS = "masters"
    LEDGERS = "ledgers"
    VOUCHERS = "vouchers"
    INVENTORY = "inventory"
    ALL = "all"


class TallyVoucherType(str, Enum):
    """Common Tally voucher types."""
    SALES = "Sales"
    PURCHASE = "Purchase"
    RECEIPT = "Receipt"
    PAYMENT = "Payment"
    JOURNAL = "Journal"
    CONTRA = "Contra"
    CREDIT_NOTE = "Credit Note"
    DEBIT_NOTE = "Debit Note"
    DELIVERY_NOTE = "Delivery Note"
    RECEIPT_NOTE = "Receipt Note"


class TallySyncMode(str, Enum):
    """Sync mode for Tally data extraction."""
    FULL = "full"
    INCREMENTAL = "incremental"


# ============================================================================
# TALLY CONNECTION CONFIG
# ============================================================================

class TallyConnectionConfig(BaseModel):
    """Configuration for connecting to Tally Prime 7."""

    host: str = Field("localhost", description="Tally server hostname or IP")
    port: int = Field(9000, ge=1, le=65535, description="Tally HTTP port")
    company_name: Optional[str] = Field(
        None, description="Tally company name to connect to"
    )
    username: Optional[str] = Field(None, description="Tally username (if auth enabled)")
    password: Optional[str] = Field(None, description="Tally password (if auth enabled)")
    timeout_seconds: int = Field(30, ge=1, le=300, description="Request timeout")
    use_ssl: bool = Field(False, description="Use HTTPS for Tally connection")

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Host cannot be empty")
        return v.strip()

    @property
    def base_url(self) -> str:
        """Build base URL for Tally HTTP API."""
        scheme = "https" if self.use_ssl else "http"
        return f"{scheme}://{self.host}:{self.port}"


# ============================================================================
# TALLY CONNECTOR CONFIGURATION (stored model)
# ============================================================================

class TallyConnectorConfig(BaseModel):
    """Full connector configuration stored for a Tally integration."""

    model_config = {"from_attributes": True}

    id: UUID = Field(default_factory=uuid4)
    connector_name: str = Field(..., description="Unique name for this connector")
    connection: TallyConnectionConfig
    enabled_data_types: List[TallyDataType] = Field(
        default=[TallyDataType.ALL],
        description="Data types to extract",
    )
    sync_mode: TallySyncMode = Field(
        TallySyncMode.INCREMENTAL, description="Sync mode"
    )
    batch_size: int = Field(
        500, ge=1, le=5000, description="Records per batch"
    )
    last_sync_at: Optional[datetime] = Field(None, description="Last successful sync")
    is_active: bool = Field(True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# TALLY API REQUEST / RESPONSE SCHEMAS
# ============================================================================

class TallyXMLRequest(BaseModel):
    """Represents a raw XML request payload for Tally."""

    request_type: str = Field(..., description="Tally request type (e.g. 'Export')")
    report_name: str = Field(..., description="Tally report or collection name")
    from_date: Optional[str] = Field(None, description="From date (YYYYMMDD)")
    to_date: Optional[str] = Field(None, description="To date (YYYYMMDD)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


# ============================================================================
# TALLY MASTER DATA SCHEMAS
# ============================================================================

class TallyStockItem(BaseModel):
    """Represents a stock item (SKU) from Tally masters."""

    name: str = Field(..., description="Stock item name")
    alias: Optional[str] = None
    parent: Optional[str] = Field(None, description="Parent stock group")
    uom: Optional[str] = Field(None, description="Unit of measure")
    base_units: Optional[str] = None
    opening_balance: float = Field(0.0, description="Opening balance quantity")
    opening_rate: float = Field(0.0, description="Opening rate per unit")
    opening_value: float = Field(0.0, description="Opening value")
    is_batch_enabled: bool = False
    gst_applicable: bool = False
    hsn_code: Optional[str] = None
    description: Optional[str] = None


class TallyParty(BaseModel):
    """Represents a party (customer/supplier) from Tally masters."""

    name: str = Field(..., description="Party name")
    alias: Optional[str] = None
    parent: Optional[str] = Field(None, description="Parent ledger group")
    address: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = Field(None, description="GST Identification Number")
    pan: Optional[str] = None
    credit_limit: float = Field(0.0)
    credit_days: int = Field(0)
    is_customer: bool = False
    is_supplier: bool = False
    opening_balance: float = Field(0.0)


class TallyLedger(BaseModel):
    """Represents a ledger account from Tally."""

    name: str = Field(..., description="Ledger name")
    alias: Optional[str] = None
    parent: str = Field(..., description="Parent ledger group")
    opening_balance: float = Field(0.0)
    closing_balance: float = Field(0.0)
    is_revenue: bool = False
    gst_duty_head: Optional[str] = None
    tax_classification: Optional[str] = None


# ============================================================================
# TALLY VOUCHER / TRANSACTION SCHEMAS
# ============================================================================

class TallyVoucherLine(BaseModel):
    """Single line item in a Tally voucher."""

    ledger_name: str = Field(..., description="Ledger account")
    amount: float = Field(..., description="Amount (positive for debit, negative for credit)")
    item_name: Optional[str] = None
    quantity: Optional[float] = None
    rate: Optional[float] = None
    uom: Optional[str] = None
    batch_name: Optional[str] = None
    cost_centre: Optional[str] = None
    narration: Optional[str] = None


class TallyVoucher(BaseModel):
    """Represents a voucher (transaction) from Tally."""

    voucher_number: str = Field(..., description="Unique voucher number")
    voucher_type: str = Field(..., description="Type of voucher")
    date: str = Field(..., description="Voucher date (YYYYMMDD or DD-MM-YYYY)")
    party_name: Optional[str] = None
    narration: Optional[str] = None
    reference: Optional[str] = None
    amount: float = Field(0.0, description="Total voucher amount")
    ledger_entries: List[TallyVoucherLine] = Field(default_factory=list)
    inventory_entries: List[TallyVoucherLine] = Field(default_factory=list)
    is_cancelled: bool = False
    guid: Optional[str] = None


# ============================================================================
# TALLY INVENTORY SCHEMA
# ============================================================================

class TallyInventoryMovement(BaseModel):
    """Represents an inventory movement from Tally."""

    item_name: str = Field(..., description="Stock item name")
    voucher_number: str
    voucher_type: str
    date: str
    quantity: float
    rate: float
    uom: Optional[str] = None
    batch_name: Optional[str] = None
    godown: Optional[str] = None
    is_inward: bool = Field(..., description="True if inward (purchase/receipt)")
    net_value: float = 0.0


class TallyStockBalance(BaseModel):
    """Represents current stock balance for an item."""

    item_name: str
    godown: Optional[str] = None
    quantity: float = 0.0
    rate: float = 0.0
    value: float = 0.0
    uom: Optional[str] = None


# ============================================================================
# SYNC REQUEST / RESPONSE SCHEMAS
# ============================================================================

class TallySyncRequest(BaseModel):
    """Request to trigger a Tally sync operation."""

    connector_name: str = Field(..., description="Name of Tally connector to use")
    data_types: Optional[List[TallyDataType]] = Field(
        None, description="Data types to sync (defaults to connector config)"
    )
    sync_mode: Optional[TallySyncMode] = Field(
        None, description="Override sync mode"
    )
    from_date: Optional[str] = Field(
        None, description="Start date for incremental sync (YYYYMMDD)"
    )
    to_date: Optional[str] = Field(
        None, description="End date for sync (YYYYMMDD)"
    )


class TallySyncStats(BaseModel):
    """Statistics for a completed Tally sync operation."""

    total_masters: int = 0
    total_ledgers: int = 0
    total_vouchers: int = 0
    total_inventory_records: int = 0
    failed_records: int = 0
    duration_seconds: float = 0.0


class TallySyncResponse(BaseModel):
    """Response for a triggered Tally sync job."""

    job_id: UUID
    connector_name: str
    status: str
    message: str
    sync_mode: TallySyncMode
    started_at: datetime = Field(default_factory=datetime.utcnow)
    stats: Optional[TallySyncStats] = None


# ============================================================================
# UNIFIED SCHEMA MAPPINGS
# ============================================================================

class UnifiedItem(BaseModel):
    """Tally stock item mapped to the unified platform schema."""

    source_id: str = Field(..., description="Original Tally item name")
    sku_code: str
    product_name: str
    description: Optional[str] = None
    uom: str = "EA"
    category: Optional[str] = None
    unit_cost: float = 0.0
    hsn_code: Optional[str] = None
    is_active: bool = True


class UnifiedParty(BaseModel):
    """Tally party mapped to the unified platform schema."""

    source_id: str = Field(..., description="Original Tally party name")
    party_code: str
    party_name: str
    party_type: str = Field(..., description="'customer' or 'supplier'")
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    is_active: bool = True


class UnifiedTransaction(BaseModel):
    """Tally voucher mapped to the unified transaction schema."""

    source_id: str = Field(..., description="Original Tally voucher number")
    transaction_type: str
    transaction_date: str
    party_name: Optional[str] = None
    amount: float
    currency: str = "INR"
    reference: Optional[str] = None
    narration: Optional[str] = None
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
