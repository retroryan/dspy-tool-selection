"""Track order tool implementation."""
from typing import List
from pydantic import BaseModel, Field

from tool_selection.base_tool import BaseTool, ToolTestCase, ToolMetadata
from tool_selection.registry import register_tool


@register_tool
class TrackOrderTool(BaseTool):
    """Tool for tracking order status."""
    
    class Arguments(BaseModel):
        """Arguments for tracking an order."""
        order_id: str = Field(..., description="Order ID")
    
    metadata = ToolMetadata(
        name="track_order",
        description="Track the status of an order",
        category="ecommerce",
        args_model=Arguments
    )
    
    def execute(self, order_id: str) -> dict:
        """Execute the tool to track an order."""
        return {
            "order_id": order_id,
            "status": "In transit",
            "delivery_date": "Tomorrow",
            "tracking_number": f"TRK{order_id}"
        }
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Track my order ORD789",
                expected_tools=["track_order"],
                description="Track specific order"
            ),
            ToolTestCase(
                request="Where is my package ORDER123?",
                expected_tools=["track_order"],
                description="Check package location"
            )
        ]