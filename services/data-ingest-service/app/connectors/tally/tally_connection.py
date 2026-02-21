"""Tally Prime 7 connection manager.

Handles HTTP connections to the Tally XML/HTTP gateway (port 9000 by default).
Tally Prime 7 exposes an HTTP server that accepts XML payloads and returns
XML responses.
"""

import logging
from typing import Any, Dict, Optional
from xml.etree import ElementTree as ET

import httpx

from .models import TallyConnectionConfig

logger = logging.getLogger(__name__)

# XML envelope template for Tally XML HTTP gateway
_TALLY_ENVELOPE_TEMPLATE = """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>{request_type}</TALLYREQUEST>
  </HEADER>
  <BODY>
    {body}
  </BODY>
</ENVELOPE>"""


class TallyConnectionError(Exception):
    """Raised when a Tally connection cannot be established or maintained."""


class TallyRequestError(Exception):
    """Raised when a Tally API request fails."""


class TallyConnection:
    """Manages an HTTP connection to Tally Prime 7's XML gateway.

    Tally Prime 7 exposes an HTTP server (default port 9000) that accepts
    XML-formatted requests and returns XML responses.  This class wraps an
    ``httpx.AsyncClient`` and provides helpers to build and parse those
    XML payloads.
    """

    def __init__(self, config: TallyConnectionConfig):
        """Initialise the connection manager.

        Args:
            config: Connection configuration (host, port, timeout, …).
        """
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._is_connected: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> bool:
        """Open the underlying HTTP client and verify reachability.

        Returns:
            ``True`` on success.

        Raises:
            TallyConnectionError: If the Tally server cannot be reached.
        """
        try:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout_seconds),
            )
            # Perform a lightweight ping to verify the server is up
            is_alive = await self.ping()
            if not is_alive:
                raise TallyConnectionError(
                    f"Tally server at {self.config.base_url} did not respond to ping"
                )
            self._is_connected = True
            logger.info("Connected to Tally at %s", self.config.base_url)
            return True
        except httpx.ConnectError as exc:
            self._is_connected = False
            raise TallyConnectionError(
                f"Cannot connect to Tally at {self.config.base_url}: {exc}"
            ) from exc

    async def disconnect(self) -> None:
        """Close the underlying HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._is_connected = False
        logger.info("Disconnected from Tally")

    async def ping(self) -> bool:
        """Send a minimal XML request to check if Tally is alive.

        Returns:
            ``True`` if Tally responds with a valid XML envelope.
        """
        if self._client is None:
            return False
        try:
            xml_body = self._build_envelope(
                request_type="Export",
                body="<EXPORT><EXPORTDATA><REQUESTDESC><REPORTNAME>List of Companies</REPORTNAME></REQUESTDESC></EXPORTDATA></EXPORT>",
            )
            response = await self._client.post(
                "/",
                content=xml_body.encode("utf-8"),
                headers={"Content-Type": "text/xml"},
            )
            return response.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    @property
    def is_connected(self) -> bool:
        """Whether the connection is currently open."""
        return self._is_connected

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------

    async def post_xml(self, xml_payload: str) -> str:
        """Send a raw XML payload to Tally and return the raw XML response.

        Args:
            xml_payload: Complete XML envelope to send.

        Returns:
            Raw XML string response from Tally.

        Raises:
            TallyConnectionError: If not connected.
            TallyRequestError: If the HTTP request fails.
        """
        if not self._is_connected or self._client is None:
            raise TallyConnectionError("Not connected to Tally. Call connect() first.")
        try:
            response = await self._client.post(
                "/",
                content=xml_payload.encode("utf-8"),
                headers={"Content-Type": "text/xml"},
            )
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as exc:
            raise TallyRequestError(
                f"Tally HTTP error {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc
        except httpx.RequestError as exc:
            raise TallyRequestError(f"Tally request failed: {exc}") from exc

    async def export_collection(
        self,
        collection_name: str,
        report_name: str,
        filters: Optional[Dict[str, Any]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> ET.Element:
        """Export a named Tally collection as a parsed XML element tree.

        Args:
            collection_name: Name of the TDL collection (e.g. "Stock Items").
            report_name: Tally report/export name.
            filters: Optional key/value filter pairs.
            from_date: Optional from date in YYYYMMDD format.
            to_date: Optional to date in YYYYMMDD format.

        Returns:
            Parsed root XML element of the Tally response.
        """
        desc_parts = [f"<REPORTNAME>{report_name}</REPORTNAME>"]
        if from_date:
            desc_parts.append(f"<STATICVARIABLES><SVFROMDATE>{from_date}</SVFROMDATE></STATICVARIABLES>")
        if to_date:
            desc_parts.append(f"<STATICVARIABLES><SVTODATE>{to_date}</SVTODATE></STATICVARIABLES>")

        if filters:
            for key, value in filters.items():
                desc_parts.append(f"<{key.upper()}>{value}</{key.upper()}>")

        if self.config.company_name:
            desc_parts.append(
                f"<STATICVARIABLES><SVCURRENTCOMPANY>{self.config.company_name}</SVCURRENTCOMPANY></STATICVARIABLES>"
            )

        request_desc = "".join(desc_parts)
        body = f"<EXPORT><EXPORTDATA><REQUESTDESC>{request_desc}</REQUESTDESC></EXPORTDATA></EXPORT>"
        xml_payload = self._build_envelope(request_type="Export", body=body)

        raw_xml = await self.post_xml(xml_payload)
        try:
            return ET.fromstring(raw_xml)
        except ET.ParseError as exc:
            raise TallyRequestError(f"Failed to parse Tally XML response: {exc}") from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_envelope(request_type: str, body: str) -> str:
        """Wrap a body fragment in a Tally XML envelope.

        Args:
            request_type: Tally request type (e.g. "Export").
            body: Inner XML body content.

        Returns:
            Full XML envelope string.
        """
        return _TALLY_ENVELOPE_TEMPLATE.format(
            request_type=request_type,
            body=body,
        )
