"""Unit tests for the Tally Prime 7 connector module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from xml.etree import ElementTree as ET

from app.connectors.tally.models import (
    TallyConnectionConfig,
    TallyConnectorConfig,
    TallyDataType,
    TallySyncMode,
)
from app.connectors.tally.tally_connection import (
    TallyConnection,
    TallyConnectionError,
    TallyRequestError,
)
from app.connectors.tally.tally_connector import TallyConnector
from app.connectors.tally.extractors.base_extractor import BaseExtractor
from app.connectors.tally.extractors.master_extractor import MasterExtractor
from app.connectors.tally.extractors.ledger_extractor import LedgerExtractor
from app.connectors.tally.extractors.voucher_extractor import VoucherExtractor
from app.connectors.tally.extractors.inventory_extractor import InventoryExtractor
from app.connectors.tally.transformers.master_transformer import MasterTransformer
from app.connectors.tally.transformers.transaction_transformer import TransactionTransformer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def connection_config():
    return TallyConnectionConfig(host="localhost", port=9000, timeout_seconds=5)


@pytest.fixture
def connector_config(connection_config):
    return TallyConnectorConfig(
        connector_name="test-tally",
        connection=connection_config,
        enabled_data_types=[TallyDataType.MASTERS],
        sync_mode=TallySyncMode.FULL,
        batch_size=100,
    )


@pytest.fixture
def tally_connection(connection_config):
    return TallyConnection(connection_config)


@pytest.fixture
def tally_connector(connector_config):
    return TallyConnector(connector_config)


# XML snippets that simulate Tally responses
STOCK_ITEMS_XML = """<ENVELOPE>
  <BODY>
    <DATA>
      <COLLECTION>
        <STOCKITEM NAME="Widget A">
          <NAME>Widget A</NAME>
          <PARENT>Finished Goods</PARENT>
          <BASEUNITS>Nos</BASEUNITS>
          <OPENINGBALANCE>10</OPENINGBALANCE>
          <OPENINGRATE>25.50</OPENINGRATE>
          <OPENINGVALUE>255.00</OPENINGVALUE>
          <ISBATCHWISEON>No</ISBATCHWISEON>
          <ISGSTAPPLICABLE>Yes</ISGSTAPPLICABLE>
          <HSNDETAILS.LIST><HSNCODE>8471</HSNCODE></HSNDETAILS.LIST>
          <DESCRIPTION>A standard widget</DESCRIPTION>
        </STOCKITEM>
        <STOCKITEM NAME="Gadget B">
          <NAME>Gadget B</NAME>
          <PARENT>Raw Materials</PARENT>
          <BASEUNITS>KG</BASEUNITS>
          <OPENINGBALANCE>50</OPENINGBALANCE>
          <OPENINGRATE>5.00</OPENINGRATE>
          <OPENINGVALUE>250.00</OPENINGVALUE>
        </STOCKITEM>
      </COLLECTION>
    </DATA>
  </BODY>
</ENVELOPE>"""

LEDGER_XML = """<ENVELOPE>
  <BODY>
    <DATA>
      <COLLECTION>
        <LEDGER NAME="Cash">
          <NAME>Cash</NAME>
          <PARENT>Cash-in-Hand</PARENT>
          <OPENINGBALANCE>5000</OPENINGBALANCE>
          <CLOSINGBALANCE>4500</CLOSINGBALANCE>
          <ISREVENUE>No</ISREVENUE>
        </LEDGER>
        <LEDGER NAME="Sales Account">
          <NAME>Sales Account</NAME>
          <PARENT>Sales Accounts</PARENT>
          <OPENINGBALANCE>0</OPENINGBALANCE>
          <CLOSINGBALANCE>150000</CLOSINGBALANCE>
          <ISREVENUE>Yes</ISREVENUE>
        </LEDGER>
      </COLLECTION>
    </DATA>
  </BODY>
</ENVELOPE>"""

VOUCHER_XML = """<ENVELOPE>
  <BODY>
    <DATA>
      <COLLECTION>
        <VOUCHER GUID="abc123">
          <VOUCHERNUMBER>SAL/001</VOUCHERNUMBER>
          <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
          <DATE>20240115</DATE>
          <PARTYLEDGERNAME>Customer X</PARTYLEDGERNAME>
          <NARRATION>Sale of widgets</NARRATION>
          <AMOUNT>1020.00</AMOUNT>
          <ISCANCELLED>No</ISCANCELLED>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>Customer X</LEDGERNAME>
            <AMOUNT>1020.00</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <INVENTORYENTRIES.LIST>
            <STOCKITEMNAME>Widget A</STOCKITEMNAME>
            <ACTUALQTY>10 Nos</ACTUALQTY>
            <RATE>102.00</RATE>
            <AMOUNT>1020.00</AMOUNT>
          </INVENTORYENTRIES.LIST>
        </VOUCHER>
      </COLLECTION>
    </DATA>
  </BODY>
</ENVELOPE>"""

INVENTORY_XML = """<ENVELOPE>
  <BODY>
    <DATA>
      <COLLECTION>
        <STOCKITEM NAME="Widget A">
          <NAME>Widget A</NAME>
          <GODOWNNAME>Main Godown</GODOWNNAME>
          <CLOSINGBALANCE>42</CLOSINGBALANCE>
          <CLOSINGRATE>25.50</CLOSINGRATE>
          <CLOSINGVALUE>1071.00</CLOSINGVALUE>
          <BASEUNITS>Nos</BASEUNITS>
        </STOCKITEM>
      </COLLECTION>
    </DATA>
  </BODY>
</ENVELOPE>"""


# ---------------------------------------------------------------------------
# TallyConnectionConfig tests
# ---------------------------------------------------------------------------

class TestTallyConnectionConfig:
    def test_base_url_http(self, connection_config):
        assert connection_config.base_url == "http://localhost:9000"

    def test_base_url_https(self):
        cfg = TallyConnectionConfig(host="myserver", port=443, use_ssl=True)
        assert cfg.base_url == "https://myserver:443"

    def test_host_validation_strips_whitespace(self):
        cfg = TallyConnectionConfig(host="  tally.local  ")
        assert cfg.host == "tally.local"

    def test_host_validation_rejects_empty(self):
        with pytest.raises(Exception):
            TallyConnectionConfig(host="   ")

    def test_default_port(self):
        cfg = TallyConnectionConfig(host="localhost")
        assert cfg.port == 9000


# ---------------------------------------------------------------------------
# TallyConnection tests
# ---------------------------------------------------------------------------

class TestTallyConnection:
    @pytest.mark.asyncio
    async def test_connect_success(self, tally_connection):
        """Connect should set is_connected=True when server responds."""
        with patch.object(tally_connection, "ping", new=AsyncMock(return_value=True)):
            import httpx
            mock_client = AsyncMock(spec=httpx.AsyncClient)
            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await tally_connection.connect()
        assert result is True
        assert tally_connection.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_failure_raises(self, tally_connection):
        """Connect should raise TallyConnectionError when server is unreachable."""
        import httpx
        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value = MagicMock()
            with patch.object(
                tally_connection, "ping", new=AsyncMock(return_value=False)
            ):
                with pytest.raises(TallyConnectionError):
                    await tally_connection.connect()

    @pytest.mark.asyncio
    async def test_disconnect_clears_state(self, tally_connection):
        """Disconnect should clear the client and mark disconnected."""
        mock_client = AsyncMock()
        tally_connection._client = mock_client
        tally_connection._is_connected = True
        await tally_connection.disconnect()
        assert tally_connection.is_connected is False
        assert tally_connection._client is None
        mock_client.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ping_returns_false_when_no_client(self, tally_connection):
        assert await tally_connection.ping() is False

    @pytest.mark.asyncio
    async def test_post_xml_raises_when_not_connected(self, tally_connection):
        with pytest.raises(TallyConnectionError):
            await tally_connection.post_xml("<ENVELOPE/>")

    def test_build_envelope(self):
        envelope = TallyConnection._build_envelope("Export", "<BODY/>")
        assert "<TALLYREQUEST>Export</TALLYREQUEST>" in envelope
        assert "<BODY/>" in envelope


# ---------------------------------------------------------------------------
# Base extractor helpers
# ---------------------------------------------------------------------------

class _ConcreteExtractor(BaseExtractor):
    """Minimal concrete extractor for testing base helpers."""

    async def extract(self, from_date=None, to_date=None, **kwargs):
        return []


class TestBaseExtractor:
    @pytest.fixture
    def extractor(self, tally_connection):
        return _ConcreteExtractor(tally_connection, batch_size=10)

    def test_text_found(self, extractor):
        root = ET.fromstring("<ROOT><NAME>Test</NAME></ROOT>")
        assert extractor._text(root, "NAME") == "Test"

    def test_text_missing_returns_default(self, extractor):
        root = ET.fromstring("<ROOT/>")
        assert extractor._text(root, "NAME", "fallback") == "fallback"

    def test_float_parsed(self, extractor):
        root = ET.fromstring("<ROOT><AMOUNT>1,234.56</AMOUNT></ROOT>")
        assert extractor._float(root, "AMOUNT") == pytest.approx(1234.56)

    def test_bool_yes(self, extractor):
        root = ET.fromstring("<ROOT><FLAG>Yes</FLAG></ROOT>")
        assert extractor._bool(root, "FLAG") is True

    def test_bool_no(self, extractor):
        root = ET.fromstring("<ROOT><FLAG>No</FLAG></ROOT>")
        assert extractor._bool(root, "FLAG") is False

    def test_iter_collection(self, extractor):
        root = ET.fromstring(
            "<ROOT><ITEM><NAME>A</NAME></ITEM><ITEM><NAME>B</NAME></ITEM></ROOT>"
        )
        items = extractor._iter_collection(root, "ITEM")
        assert len(items) == 2


# ---------------------------------------------------------------------------
# MasterExtractor tests
# ---------------------------------------------------------------------------

class TestMasterExtractor:
    @pytest.fixture
    def extractor(self, tally_connection):
        return MasterExtractor(tally_connection, batch_size=500)

    @pytest.mark.asyncio
    async def test_extract_stock_items(self, extractor):
        root = ET.fromstring(STOCK_ITEMS_XML)
        with patch.object(
            extractor.connection,
            "export_collection",
            new=AsyncMock(return_value=root),
        ):
            records = await extractor.extract_stock_items()

        assert len(records) == 2
        widget = records[0]
        assert widget["record_type"] == "stock_item"
        assert widget["name"] == "Widget A"
        assert widget["parent"] == "Finished Goods"
        assert widget["uom"] == "Nos"
        assert widget["opening_balance"] == pytest.approx(10.0)
        assert widget["gst_applicable"] is True
        assert widget["hsn_code"] == "8471"

    @pytest.mark.asyncio
    async def test_extract_parties(self, extractor):
        party_xml = """<ENVELOPE>
          <BODY><DATA><COLLECTION>
            <LEDGER NAME="Customer X">
              <NAME>Customer X</NAME>
              <PARENT>Sundry Debtors</PARENT>
              <EMAIL>cx@example.com</EMAIL>
              <PARTYGSTIN>29ABCDE1234F1Z5</PARTYGSTIN>
              <OPENINGBALANCE>10000</OPENINGBALANCE>
            </LEDGER>
          </COLLECTION></DATA></BODY>
        </ENVELOPE>"""
        root = ET.fromstring(party_xml)
        with patch.object(
            extractor.connection,
            "export_collection",
            new=AsyncMock(return_value=root),
        ):
            records = await extractor.extract_parties()

        assert len(records) == 1
        party = records[0]
        assert party["record_type"] == "party"
        assert party["is_customer"] is True
        assert party["is_supplier"] is False
        assert party["gstin"] == "29ABCDE1234F1Z5"


# ---------------------------------------------------------------------------
# LedgerExtractor tests
# ---------------------------------------------------------------------------

class TestLedgerExtractor:
    @pytest.fixture
    def extractor(self, tally_connection):
        return LedgerExtractor(tally_connection, batch_size=500)

    @pytest.mark.asyncio
    async def test_extract_ledgers(self, extractor):
        root = ET.fromstring(LEDGER_XML)
        with patch.object(
            extractor.connection,
            "export_collection",
            new=AsyncMock(return_value=root),
        ):
            records = await extractor.extract()

        assert len(records) == 2
        cash = records[0]
        assert cash["record_type"] == "ledger"
        assert cash["name"] == "Cash"
        assert cash["closing_balance"] == pytest.approx(4500.0)
        assert cash["is_revenue"] is False

        sales = records[1]
        assert sales["is_revenue"] is True


# ---------------------------------------------------------------------------
# VoucherExtractor tests
# ---------------------------------------------------------------------------

class TestVoucherExtractor:
    @pytest.fixture
    def extractor(self, tally_connection):
        return VoucherExtractor(tally_connection, batch_size=500)

    @pytest.mark.asyncio
    async def test_extract_vouchers(self, extractor):
        root = ET.fromstring(VOUCHER_XML)
        with patch.object(
            extractor.connection,
            "export_collection",
            new=AsyncMock(return_value=root),
        ):
            records = await extractor.extract()

        assert len(records) == 1
        voucher = records[0]
        assert voucher["record_type"] == "voucher"
        assert voucher["voucher_number"] == "SAL/001"
        assert voucher["voucher_type"] == "Sales"
        assert voucher["date"] == "20240115"
        assert voucher["party_name"] == "Customer X"
        assert len(voucher["ledger_entries"]) == 1
        assert len(voucher["inventory_entries"]) == 1


# ---------------------------------------------------------------------------
# InventoryExtractor tests
# ---------------------------------------------------------------------------

class TestInventoryExtractor:
    @pytest.fixture
    def extractor(self, tally_connection):
        return InventoryExtractor(tally_connection, batch_size=500)

    @pytest.mark.asyncio
    async def test_extract_stock_balances(self, extractor):
        root = ET.fromstring(INVENTORY_XML)
        with patch.object(
            extractor.connection,
            "export_collection",
            new=AsyncMock(return_value=root),
        ):
            records = await extractor.extract_stock_balances()

        assert len(records) == 1
        balance = records[0]
        assert balance["record_type"] == "stock_balance"
        assert balance["item_name"] == "Widget A"
        assert balance["quantity"] == pytest.approx(42.0)
        assert balance["value"] == pytest.approx(1071.0)


# ---------------------------------------------------------------------------
# MasterTransformer tests
# ---------------------------------------------------------------------------

class TestMasterTransformer:
    @pytest.fixture
    def transformer(self):
        return MasterTransformer()

    def test_transform_stock_item(self, transformer):
        raw = {
            "record_type": "stock_item",
            "name": "Widget A",
            "parent": "Finished Goods",
            "uom": "Nos",
            "opening_rate": 25.50,
            "hsn_code": "8471",
            "description": "A widget",
        }
        result = transformer.transform([raw])
        assert len(result) == 1
        item = result[0]
        assert item["unified_type"] == "item"
        assert item["sku_code"] == "WIDGET_A"
        assert item["uom"] == "Nos"
        assert item["unit_cost"] == pytest.approx(25.50)
        assert item["hsn_code"] == "8471"

    def test_transform_party(self, transformer):
        raw = {
            "record_type": "party",
            "name": "Customer X",
            "is_customer": True,
            "is_supplier": False,
            "email": "cx@example.com",
            "gstin": "29ABCDE1234F1Z5",
        }
        result = transformer.transform([raw])
        assert len(result) == 1
        party = result[0]
        assert party["unified_type"] == "party"
        assert party["party_type"] == "customer"
        assert party["gstin"] == "29ABCDE1234F1Z5"

    def test_skips_unknown_record_type(self, transformer):
        raw = {"record_type": "unknown", "name": "X"}
        result = transformer.transform([raw])
        assert result == []

    def test_skips_record_with_no_name(self, transformer):
        raw = {"record_type": "stock_item", "name": ""}
        result = transformer.transform([raw])
        assert result == []


# ---------------------------------------------------------------------------
# TransactionTransformer tests
# ---------------------------------------------------------------------------

class TestTransactionTransformer:
    @pytest.fixture
    def transformer(self):
        return TransactionTransformer()

    def test_transform_voucher(self, transformer):
        raw = {
            "record_type": "voucher",
            "voucher_number": "SAL/001",
            "voucher_type": "Sales",
            "date": "20240115",
            "party_name": "Customer X",
            "amount": 1020.0,
            "ledger_entries": [{"ledger_name": "Customer X", "amount": 1020.0}],
            "inventory_entries": [],
            "is_cancelled": False,
        }
        result = transformer.transform([raw])
        assert len(result) == 1
        tx = result[0]
        assert tx["unified_type"] == "transaction"
        assert tx["source_id"] == "SAL/001"
        assert tx["transaction_date"] == "2024-01-15"
        assert tx["currency"] == "INR"

    def test_transform_inventory_movement(self, transformer):
        raw = {
            "record_type": "inventory_movement",
            "item_name": "Widget A",
            "voucher_number": "SAL/001",
            "voucher_type": "Sales",
            "date": "20240115",
            "quantity": 10.0,
            "rate": 102.0,
            "uom": "Nos",
            "is_inward": False,
            "net_value": 1020.0,
        }
        result = transformer.transform([raw])
        assert len(result) == 1
        mv = result[0]
        assert mv["unified_type"] == "inventory_movement"
        assert mv["quantity"] == pytest.approx(10.0)
        assert mv["is_inward"] is False

    def test_transform_stock_balance(self, transformer):
        raw = {
            "record_type": "stock_balance",
            "item_name": "Widget A",
            "quantity": 42.0,
            "rate": 25.50,
            "value": 1071.0,
            "uom": "Nos",
        }
        result = transformer.transform([raw])
        assert len(result) == 1
        bal = result[0]
        assert bal["unified_type"] == "stock_balance"
        assert bal["value"] == pytest.approx(1071.0)

    def test_transform_ledger(self, transformer):
        raw = {
            "record_type": "ledger",
            "name": "Cash",
            "parent": "Cash-in-Hand",
            "opening_balance": 5000.0,
            "closing_balance": 4500.0,
            "is_revenue": False,
        }
        result = transformer.transform([raw])
        assert len(result) == 1
        ledger = result[0]
        assert ledger["unified_type"] == "ledger"
        assert ledger["closing_balance"] == pytest.approx(4500.0)

    def test_normalise_date_yyyymmdd(self, transformer):
        assert transformer._normalise_date("20240115") == "2024-01-15"

    def test_normalise_date_dd_mm_yyyy(self, transformer):
        assert transformer._normalise_date("15-01-2024") == "2024-01-15"

    def test_normalise_date_empty(self, transformer):
        assert transformer._normalise_date("") == ""


# ---------------------------------------------------------------------------
# TallyConnector tests
# ---------------------------------------------------------------------------

class TestTallyConnector:
    @pytest.mark.asyncio
    async def test_connect_delegates_to_tally_connection(self, tally_connector):
        with patch.object(
            tally_connector._tally_conn, "connect", new=AsyncMock(return_value=True)
        ):
            result = await tally_connector.connect()
        assert result is True
        assert tally_connector.is_connected is True

    @pytest.mark.asyncio
    async def test_disconnect_clears_state(self, tally_connector):
        tally_connector._is_connected = True
        with patch.object(
            tally_connector._tally_conn, "disconnect", new=AsyncMock()
        ):
            await tally_connector.disconnect()
        assert tally_connector.is_connected is False

    @pytest.mark.asyncio
    async def test_fetch_data_raises_when_not_connected(self, tally_connector):
        with pytest.raises(ConnectionError):
            await tally_connector.fetch_data("masters")

    @pytest.mark.asyncio
    async def test_validate_connection_delegates_to_ping(self, tally_connector):
        with patch.object(
            tally_connector._tally_conn, "ping", new=AsyncMock(return_value=True)
        ):
            result = await tally_connector.validate_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_fetch_all_returns_transformed_records(self, tally_connector):
        """fetch_all should extract and transform records for each data type."""
        tally_connector._is_connected = True
        mock_records = [
            {"record_type": "stock_item", "name": "Widget A", "parent": "FG", "uom": "Nos",
             "opening_rate": 10.0, "hsn_code": "", "description": ""}
        ]
        with patch.object(
            tally_connector, "_extract_by_type", new=AsyncMock(return_value=mock_records)
        ):
            results = await tally_connector.fetch_all(
                data_types=[TallyDataType.MASTERS]
            )
        assert len(results) == 1
        assert results[0]["unified_type"] == "item"

    @pytest.mark.asyncio
    async def test_compute_stats(self, tally_connector):
        records = [
            {"unified_type": "item"},
            {"unified_type": "item"},
            {"unified_type": "transaction"},
        ]
        stats = tally_connector._compute_stats(records, 1.5)
        assert stats["total_records"] == 3
        assert stats["by_type"]["item"] == 2
        assert stats["by_type"]["transaction"] == 1
        assert stats["duration_seconds"] == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# DataSourceType enum
# ---------------------------------------------------------------------------

def test_tally_data_source_type():
    """DataSourceType should include TALLY."""
    from shared.domain_models import DataSourceType
    assert DataSourceType.TALLY == "tally"
    assert DataSourceType.TALLY in list(DataSourceType)
