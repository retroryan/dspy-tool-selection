"""
Give hint tool implementation using the new base classes.

This module defines the `GiveHintTool`, which provides progressive hints
about a treasure's location. It integrates with the tool selection framework
by extending `BaseTool` and registering itself.
"""
from typing import List
from pydantic import BaseModel, Field

from tool_selection.base_tool import BaseTool, ToolTestCase
from tool_selection.registry import register_tool


@register_tool
class GiveHintTool(BaseTool):
    """
    A tool for giving progressive hints about the treasure location.

    This tool provides a series of predefined hints. Each time it's called,
    it can provide the next hint in the sequence, based on the `hint_total`
    argument, simulating a progressive hint system.
    """
    NAME = "give_hint"
    MODULE = "treasure_hunt"
    
    class Arguments(BaseModel):
        """
        Defines the arguments required for the `give_hint` tool.

        This Pydantic model ensures that the `hint_total` argument is provided
        and is a non-negative integer.
        """
        hint_total: int = Field(
            default=0, 
            ge=0, 
            description="The total number of hints already given. Used to determine which hint to provide next."
        )
    
    # Tool-specific description and argument model linkage
    description: str = "Give a progressive hint about the treasure location."
    args_model: type[BaseModel] = Arguments
    
    def execute(self, hint_total: int = 0) -> dict:
        """
        Executes the hint-giving action.

        Based on the `hint_total`, it returns a specific hint from a predefined
        list. If all hints have been given, it indicates that no more hints are available.

        Args:
            hint_total (int): The count of hints already provided, determining the next hint.

        Returns:
            dict: A dictionary containing the hint or a message indicating no more hints.
        """
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
        """
        Provides a list of `ToolTestCase` objects for testing the `GiveHintTool`.

        These test cases cover various natural language requests that should map
        to the `give_hint` tool.
        """
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