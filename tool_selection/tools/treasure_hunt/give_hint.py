"""Give hint tool implementation using the new base classes."""
from typing import List
from pydantic import BaseModel, Field

from tool_selection.base_tool import BaseTool, ToolArgument, ToolTestCase, ToolMetadata
from tool_selection.registry import register_tool


class GiveHintArgs(BaseModel):
    """Argument validation model for give_hint tool."""
    hint_total: int = Field(
        default=0, 
        ge=0, 
        description="The total number of hints already given"
    )


@register_tool
class GiveHintTool(BaseTool):
    """Tool for giving progressive hints about the treasure location."""
    
    metadata = ToolMetadata(
        name="give_hint",
        description="Give a progressive hint about the treasure location",
        category="treasure_hunt",
        arguments=[
            ToolArgument(
                name="hint_total",
                type=int,
                description="The total number of hints already given",
                required=False,
                default=0,
                constraints={"ge": 0}  # Greater than or equal to 0
            )
        ]
    )
    
    def execute(self, hint_total: int = 0) -> dict:
        """Execute the tool to give a hint."""
        hints = [
            "The treasure is in a city known for its coffee and rain.",
            "It's located near a famous public market.",
            "The address is on a street named after a US President's wife."
        ]
        
        if hint_total < len(hints):
            return {"hint": hints[hint_total]}
        else:
            return {"hint": "No more hints available."}
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="I need a hint about the treasure",
                expected_tools=["give_hint"],
                description="Basic hint request"
            ),
            ToolTestCase(
                request="Give me another clue about where the treasure is",
                expected_tools=["give_hint"],
                description="Alternative hint request"
            ),
            ToolTestCase(
                request="Can you help me find the treasure?",
                expected_tools=["give_hint"],
                description="General help request"
            )
        ]