"""Create event tool implementation."""
from typing import List
from pydantic import BaseModel, Field

from tool_selection.base_tool import BaseTool, ToolTestCase, ToolMetadata


class CreateEventTool(BaseTool):
    """Tool for creating new events."""
    
    class Arguments(BaseModel):
        """Arguments for creating an event."""
        title: str = Field(..., description="Event title")
        date: str = Field(..., description="Event date")
        location: str = Field(..., description="Event location")
    
    metadata = ToolMetadata(
        name="create_event",
        description="Create a new event",
        category="events",
        args_model=Arguments
    )
    
    def execute(self, title: str, date: str, location: str) -> dict:
        """Execute the tool to create an event."""
        return {
            "event_id": "EVT123",
            "status": "created",
            "title": title,
            "date": date,
            "location": location
        }
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Create an event called 'Team Meeting' for tomorrow at the office",
                expected_tools=["create_event"],
                description="Create a new event"
            ),
            ToolTestCase(
                request="Schedule a birthday party on Saturday at the park",
                expected_tools=["create_event"],
                description="Schedule an event"
            )
        ]