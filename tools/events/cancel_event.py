"""Cancel event tool implementation."""
from typing import List, Optional
from pydantic import BaseModel, Field

from tool_selection.base_tool import BaseTool, ToolTestCase, ToolMetadata
from tool_selection.registry import register_tool


@register_tool
class CancelEventTool(BaseTool):
    """Tool for canceling events or reservations."""
    
    class Arguments(BaseModel):
        """Arguments for canceling an event."""
        event_id: str = Field(..., description="Event or reservation ID")
        reason: Optional[str] = Field(default="", description="Cancellation reason")
    
    metadata = ToolMetadata(
        name="cancel_event",
        description="Cancel an existing event or reservation",
        category="events",
        args_model=Arguments
    )
    
    def execute(self, event_id: str, reason: str = "") -> dict:
        """Execute the tool to cancel an event."""
        return {
            "status": "cancelled",
            "event_id": event_id,
            "reason": reason if reason else "No reason provided"
        }
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Cancel event EVT123 due to weather",
                expected_tools=["cancel_event"],
                description="Cancel event with reason"
            ),
            ToolTestCase(
                request="Cancel my reservation RES456",
                expected_tools=["cancel_event"],
                description="Cancel reservation"
            )
        ]