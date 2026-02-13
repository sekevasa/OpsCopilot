"""API routes for AI runtime."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from shared.database import db
from shared.domain_models import ServiceError
from ..domain.schemas import (
    InferenceRequest,
    InferenceResponse,
    AIModelResponse,
)
from ..application.services import AIRuntimeService
from ..copilot.orchestrator import CopilotOrchestrator, CopilotResponse
from ..memory.conversation import ConversationStore
from datetime import datetime
from typing import Optional, Dict, Any


router = APIRouter(prefix="/api/v1", tags=["ai-runtime"])

# Global conversation store
_conversation_store = ConversationStore()


# Pydantic schemas for copilot endpoints
class CopilotQueryRequest(BaseModel):
    """Copilot query request."""
    query: str = Field(..., description="User query for the copilot")
    session_id: Optional[str] = Field(
        None, description="Conversation session ID")
    context_hints: Optional[Dict[str, Any]] = Field(
        None, description="Optional hints about context")
    max_tools: int = Field(3, description="Maximum number of tools to use")


class ToolCallResponse(BaseModel):
    """Tool call response."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str


class CopilotQueryResponse(BaseModel):
    """Copilot query response."""
    message: str = Field(..., description="AI response message")
    tool_calls: list[ToolCallResponse] = Field(
        default_factory=list, description="Tools executed")
    context_used: Dict[str, Any] = Field(
        default_factory=dict, description="Context data used")
    confidence: float = Field(..., description="Confidence score 0-1")
    timestamp: str


class ConversationHistoryResponse(BaseModel):
    """Conversation history response."""
    session_id: str
    messages: list[Dict[str, Any]] = Field(
        default_factory=list, description="Message history")
    summary: Dict[str, Any] = Field(
        default_factory=dict, description="Conversation summary")


async def get_service(session: AsyncSession = Depends(db.get_session)) -> AIRuntimeService:
    """Dependency for AI runtime service."""
    return AIRuntimeService(session)


@router.post("/infer", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest,
    service: AIRuntimeService = Depends(get_service),
) -> InferenceResponse:
    """Run inference on AI model."""
    try:
        job = await service.run_inference(
            model_name=request.model_name,
            input_data=request.input_data,
            timeout_seconds=request.timeout_seconds,
        )
        return InferenceResponse.from_orm(job)
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-runtime-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow(),
    }

# Copilot endpoints


@router.post("/copilot/query", response_model=CopilotQueryResponse)
async def process_copilot_query(request: CopilotQueryRequest) -> CopilotQueryResponse:
    """Process a copilot query end-to-end.

    This endpoint:
    1. Creates or retrieves a conversation session
    2. Builds rich context from multiple services
    3. Determines which tools to use
    4. Executes tools in optimal order
    5. Generates an AI response

    Args:
        request: Query request with session_id, query, and optional context hints

    Returns:
        CopilotQueryResponse with AI message, tool calls, context, and confidence

    Example:
        POST /api/v1/copilot/query
        {
            "query": "What's the current inventory level for SKU ABC123?",
            "session_id": "user-123-session-456",
            "context_hints": {
                "entity_type": "sku",
                "entity_id": "ABC123"
            }
        }
    """
    try:
        # Get or create conversation
        session_id = request.session_id or str(datetime.utcnow().timestamp())
        memory = _conversation_store.get_conversation(session_id)
        if not memory:
            memory = _conversation_store.create_conversation(session_id)

        # Create orchestrator with existing memory
        orchestrator = CopilotOrchestrator(memory=memory)

        # Process query
        response = await orchestrator.process_query(
            query=request.query,
            context_hints=request.context_hints,
            max_tools=request.max_tools,
        )

        # Convert to response model
        return CopilotQueryResponse(
            message=response.message,
            tool_calls=[
                ToolCallResponse(
                    tool_name=tc.tool_name,
                    arguments=tc.arguments,
                    result=tc.result,
                    error=tc.error,
                    timestamp=tc.timestamp.isoformat(),
                )
                for tc in response.tool_calls
            ],
            context_used=response.context_used,
            confidence=response.confidence,
            timestamp=response.timestamp.isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "query": request.query},
        )


@router.get("/copilot/session/{session_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(session_id: str) -> ConversationHistoryResponse:
    """Get conversation history for a session.

    Args:
        session_id: Conversation session ID

    Returns:
        Conversation history and summary
    """
    try:
        memory = _conversation_store.get_conversation(session_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        return ConversationHistoryResponse(
            session_id=session_id,
            messages=memory.get_history(),
            summary=memory.get_summary(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/copilot/session/{session_id}")
async def delete_session(session_id: str) -> Dict[str, Any]:
    """Delete a conversation session.

    Args:
        session_id: Conversation session ID

    Returns:
        Success message
    """
    try:
        deleted = _conversation_store.delete_conversation(session_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )

        return {"message": f"Session deleted: {session_id}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/copilot/tools")
async def list_available_tools() -> Dict[str, Any]:
    """List all available tools in the copilot.

    Returns:
        Dictionary with tool information
    """
    try:
        from app.tools.base import ToolRegistry

        registry = ToolRegistry()
        tools = registry.list_tools()

        return {
            "available_tools": len(tools),
            "tools": [
                {
                    "name": tool.name(),
                    "description": tool.description(),
                    "input_schema": tool.input_schema(),
                }
                for tool in tools
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
