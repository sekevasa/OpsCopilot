"""Copilot orchestrator for query processing."""

from typing import Any, Dict, List, Optional
import logging
import json
from datetime import datetime

from app.tools.base import ToolRegistry, BaseTool
from app.context.builder import ContextBuilder
from app.memory.conversation import ConversationMemory, Message

logger = logging.getLogger(__name__)


class ToolCall:
    """Record of a tool execution."""

    def __init__(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any = None,
        error: Optional[str] = None,
    ):
        self.tool_name = tool_name
        self.arguments = arguments
        self.result = result
        self.error = error
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class CopilotResponse:
    """Copilot response with reasoning and tool calls."""

    def __init__(
        self,
        message: str,
        tool_calls: List[ToolCall],
        context_used: Dict[str, Any],
        confidence: float = 0.8,
    ):
        self.message = message
        self.tool_calls = tool_calls
        self.context_used = context_used
        self.confidence = confidence
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "context_used": self.context_used,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


class CopilotOrchestrator:
    """Orchestrator for copilot query processing.

    Responsibilities:
    - Accept user queries
    - Build context from multiple sources
    - Determine which tools to use
    - Execute tools in optimal order
    - Generate AI response
    - Manage conversation memory
    """

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        context_builder: Optional[ContextBuilder] = None,
        memory: Optional[ConversationMemory] = None,
    ):
        """Initialize orchestrator.

        Args:
            tool_registry: Tool registry (uses default singleton if None)
            context_builder: Context builder (creates new if None)
            memory: Conversation memory (creates new if None)
        """
        self.tool_registry = tool_registry or ToolRegistry()
        self.context_builder = context_builder or ContextBuilder()
        self.memory = memory or ConversationMemory()

    async def process_query(
        self,
        query: str,
        context_hints: Optional[Dict[str, Any]] = None,
        max_tools: int = 3,
    ) -> CopilotResponse:
        """Process a user query end-to-end.

        Args:
            query: User query string
            context_hints: Optional hints about context (e.g., {"entity_type": "sku", "entity_id": "ABC123"})
            max_tools: Maximum number of tools to use

        Returns:
            CopilotResponse with message, tool calls, and context
        """
        logger.info(f"Processing query: {query[:100]}...")

        # Add query to memory
        self.memory.add_message(role="user", content=query, metadata={
                                "context_hints": context_hints})

        # Step 1: Build context
        logger.info("Building context...")
        context = await self._build_context(context_hints)

        # Step 2: Determine which tools to use
        logger.info("Determining tools to use...")
        tools_to_use = self._determine_tools(query, context, max_tools)

        # Step 3: Execute tools
        logger.info(f"Executing {len(tools_to_use)} tools...")
        tool_calls = await self._execute_tools(tools_to_use, query, context)

        # Step 4: Generate response
        logger.info("Generating response...")
        response_message = self._generate_response(query, context, tool_calls)

        # Step 5: Create response
        response = CopilotResponse(
            message=response_message,
            tool_calls=tool_calls,
            context_used=context,
            confidence=self._calculate_confidence(tool_calls, context),
        )

        # Add response to memory
        self.memory.add_message(
            role="assistant",
            content=response_message,
            metadata={"tool_calls": len(
                tool_calls), "confidence": response.confidence},
        )

        logger.info(f"Query processed: {len(tool_calls)} tools executed")
        return response

    async def _build_context(
        self,
        context_hints: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build context for the query.

        Args:
            context_hints: Optional hints about what context to build

        Returns:
            Built context dictionary
        """
        entity_type = context_hints.get(
            "entity_type") if context_hints else None
        entity_id = context_hints.get("entity_id") if context_hints else None

        # Build rich context from multiple sources
        context = await self.context_builder.build_context(
            entity_type=entity_type,
            entity_id=entity_id,
            include_inventory=True,
            include_orders=True,
            include_production=True,
        )

        return context

    def _determine_tools(
        self,
        query: str,
        context: Dict[str, Any],
        max_tools: int = 3,
    ) -> List[str]:
        """Determine which tools to use for the query.

        Args:
            query: User query
            context: Built context
            max_tools: Maximum tools to use

        Returns:
            List of tool names to use
        """
        query_lower = query.lower()
        tools_to_use = []

        # Simple keyword-based tool selection
        # In production, this would be ML-based tool selection
        keyword_map = {
            "query_inventory": ["inventory", "stock", "quantity", "available"],
            "lookup_orders": ["order", "sales", "customer", "purchase"],
            "check_production": ["production", "schedule", "status", "manufacturing"],
            "get_forecast": ["forecast", "predict", "demand", "future"],
            "manage_alerts": ["alert", "warning", "issue", "problem"],
        }

        for tool_name, keywords in keyword_map.items():
            if any(kw in query_lower for kw in keywords):
                tools_to_use.append(tool_name)
                if len(tools_to_use) >= max_tools:
                    break

        # If no tools matched, use context insights to suggest tools
        if not tools_to_use:
            insights = context.get("insights", {})
            if insights.get("has_alerts"):
                tools_to_use.append("manage_alerts")
            if insights.get("has_critical_inventory"):
                tools_to_use.append("query_inventory")

        logger.info(f"Selected tools: {tools_to_use}")
        return tools_to_use

    async def _execute_tools(
        self,
        tool_names: List[str],
        query: str,
        context: Dict[str, Any],
    ) -> List[ToolCall]:
        """Execute tools and collect results.

        Args:
            tool_names: List of tool names to execute
            query: Original query
            context: Built context

        Returns:
            List of tool call records
        """
        tool_calls = []

        for tool_name in tool_names:
            try:
                logger.info(f"Executing tool: {tool_name}")

                # Get tool from registry
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    logger.warning(f"Tool not found: {tool_name}")
                    tool_calls.append(
                        ToolCall(
                            tool_name=tool_name,
                            arguments={},
                            error=f"Tool not found: {tool_name}",
                        )
                    )
                    continue

                # Extract arguments for the tool from context
                arguments = self._extract_tool_arguments(tool, query, context)

                # Execute tool
                result = await tool.execute(**arguments)

                tool_calls.append(
                    ToolCall(
                        tool_name=tool_name,
                        arguments=arguments,
                        result=result,
                    )
                )

                logger.info(f"Tool executed successfully: {tool_name}")

            except Exception as e:
                logger.error(
                    f"Tool execution failed: {tool_name}", exc_info=True)
                tool_calls.append(
                    ToolCall(
                        tool_name=tool_name,
                        arguments={},
                        error=str(e),
                    )
                )

        return tool_calls

    def _extract_tool_arguments(
        self,
        tool: BaseTool,
        query: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract arguments for a tool from query and context.

        Args:
            tool: Tool to get arguments for
            query: User query
            context: Built context

        Returns:
            Dictionary of arguments
        """
        # Get tool's input schema
        schema = tool.input_schema()

        arguments = {}

        # Simple extraction: for each field in schema, try to get from context
        # In production, this would be more sophisticated NLP-based extraction
        if "sku_code" in schema:
            # Try to extract SKU code from query or context
            if context.get("entity_id"):
                arguments["sku_code"] = context["entity_id"]

        if "customer_id" in schema:
            if context.get("entity_id"):
                arguments["customer_id"] = context["entity_id"]

        if "warehouse" in schema:
            arguments["warehouse"] = context.get(
                "current_warehouse", "default")

        return arguments

    def _generate_response(
        self,
        query: str,
        context: Dict[str, Any],
        tool_calls: List[ToolCall],
    ) -> str:
        """Generate response message.

        Args:
            query: Original query
            context: Built context
            tool_calls: Executed tool calls

        Returns:
            Response message
        """
        # Build response from tool results
        message_parts = []

        # Start with acknowledgment
        message_parts.append("Based on the available data: ")

        # Add tool results
        successful_calls = [tc for tc in tool_calls if not tc.error]
        if successful_calls:
            for tool_call in successful_calls:
                tool_name = tool_call.tool_name.replace("_", " ").title()
                if tool_call.result:
                    # Summarize result
                    result_summary = self._summarize_result(tool_call)
                    message_parts.append(f"\n• {tool_name}: {result_summary}")

        # Add insights
        insights = context.get("insights", {})
        if insights:
            message_parts.append("\n\nKey Insights:")
            if insights.get("has_alerts"):
                message_parts.append(
                    f"\n• {insights.get('alert_count', 0)} active alerts")
            if insights.get("has_critical_inventory"):
                message_parts.append(f"\n• Critical inventory items detected")
            if insights.get("has_high_volume_orders"):
                message_parts.append(f"\n• High-volume orders in progress")

        # Add failed tool calls
        failed_calls = [tc for tc in tool_calls if tc.error]
        if failed_calls:
            message_parts.append("\n\nNote: Some tools encountered issues:")
            for tool_call in failed_calls:
                message_parts.append(
                    f"\n• {tool_call.tool_name}: {tool_call.error}")

        return "".join(message_parts) or "I've analyzed the available data. How can I help you further?"

    def _summarize_result(self, tool_call: ToolCall) -> str:
        """Summarize tool result for response.

        Args:
            tool_call: Tool call with result

        Returns:
            Summary string
        """
        result = tool_call.result
        if isinstance(result, dict):
            # Extract key information
            if "qty_available" in result:
                return f"Available quantity: {result['qty_available']}"
            elif "order_count" in result:
                return f"Found {result['order_count']} orders"
            elif "status" in result:
                return f"Status: {result['status']}"
            else:
                # Generic summary
                return f"Retrieved {len(result)} items"
        elif isinstance(result, list):
            return f"Retrieved {len(result)} items"
        else:
            return str(result)[:100]

    def _calculate_confidence(
        self,
        tool_calls: List[ToolCall],
        context: Dict[str, Any],
    ) -> float:
        """Calculate confidence in the response.

        Args:
            tool_calls: Executed tool calls
            context: Built context

        Returns:
            Confidence score 0-1
        """
        # Start with base confidence
        confidence = 0.6

        # Increase for successful tool calls
        successful_tools = sum(1 for tc in tool_calls if not tc.error)
        confidence += (successful_tools * 0.1)

        # Increase for rich context
        if context.get("inventory"):
            confidence += 0.05
        if context.get("orders"):
            confidence += 0.05
        if context.get("production"):
            confidence += 0.05
        if context.get("insights"):
            confidence += 0.05

        # Cap at 0.99
        return min(confidence, 0.99)

    def get_memory(self) -> ConversationMemory:
        """Get the conversation memory."""
        return self.memory

    def clear_memory(self) -> None:
        """Clear conversation memory."""
        self.memory.clear()
