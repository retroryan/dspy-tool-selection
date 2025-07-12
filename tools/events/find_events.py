"""Find events tool implementation."""
from typing import List, Optional
from pydantic import BaseModel, Field

from tool_selection.base_tool import BaseTool, ToolTestCase, ToolMetadata


class FindEventsTool(BaseTool):
    """Tool for finding events based on location, date, or type."""
    
    class Arguments(BaseModel):
        """Arguments for finding events."""
        location: Optional[str] = Field(default=None, description="City or venue")
        date: Optional[str] = Field(default=None, description="Date or date range")
        event_type: Optional[str] = Field(default=None, description="Type of event (concert, sports, etc)")
    
    metadata = ToolMetadata(
        name="find_events",
        description="Find events based on location, date, or type",
        category="events",
        args_model=Arguments
    )
    
    def execute(self, location: str = None, date: str = None, event_type: str = None) -> dict:
        """Execute the tool to find events."""
        # Build response based on provided parameters
        criteria = []
        if location:
            criteria.append(f"in {location}")
        if date:
            criteria.append(f"on {date}")
        if event_type:
            criteria.append(f"type: {event_type}")
        
        criteria_str = " ".join(criteria) if criteria else "matching your criteria"
        
        return {
            "events": f"Found 5 events {criteria_str}",
            "count": 5,
            "criteria": {
                "location": location,
                "date": date,
                "event_type": event_type
            }
        }
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Find concerts in Seattle",
                expected_tools=["find_events"],
                description="Find events by type and location"
            ),
            ToolTestCase(
                request="What events are happening this weekend?",
                expected_tools=["find_events"],
                description="Find events by date"
            ),
            ToolTestCase(
                request="Show me sports events in New York",
                expected_tools=["find_events"],
                description="Find sports events by location"
            )
        ]