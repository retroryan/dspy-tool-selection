"""
Guess location tool implementation using the new base classes.

This module defines the `GuessLocationTool`, which allows users to guess
the location of a treasure. It integrates with the tool selection framework
by extending `BaseTool` and registering itself.
"""
from typing import List, Optional, Any
from pydantic import BaseModel, Field

from tool_selection.base_tool import BaseTool, ToolTestCase


class GuessLocationTool(BaseTool):
    """
    A tool for guessing the treasure location.

    This tool allows users to submit a guess for the treasure's location
    by providing an address, city, or state. It then checks if the guess
    matches the predefined correct location.
    """
    NAME = "guess_location"
    MODULE = "treasure_hunt"
    
    class Arguments(BaseModel):
        """
        Defines the arguments required for the `guess_location` tool.

        This Pydantic model allows for flexible input, where users can provide
        any combination of address, city, or state for their guess.
        """
        address: Optional[str] = Field(default="", description="The street address component of the guess")
        city: Optional[str] = Field(default="", description="The city component of the guess")
        state: Optional[str] = Field(default="", description="The state component of the guess")
        
        def model_post_init(self, __context: Any) -> None:
            """
            Pydantic hook called after model initialization.
            Ensures that at least one location field (address, city, or state) is provided.
            If none are provided, they are explicitly set to empty strings.
            """
            super().model_post_init(__context)
            if not any([self.address, self.city, self.state]):
                # If no location information is provided, ensure fields are empty strings
                self.address = ""
                self.city = ""
                self.state = ""
    
    # Tool-specific description and argument model linkage
    description: str = "Guess the treasure location based on address, city, or state."
    args_model: type[BaseModel] = Arguments
    
    def execute(self, address: str = "", city: str = "", state: str = "") -> dict:
        """
        Executes the location guessing action.

        Compares the provided guess against a hardcoded correct location.
        In a real game, this might involve more complex logic or a database lookup.

        Args:
            address (str): The guessed street address.
            city (str): The guessed city.
            state (str): The guessed state.

        Returns:
            dict: A dictionary indicating whether the guess was correct and a message.
        """
        # Hardcoded correct location for demonstration purposes
        correct_city = "seattle"
        correct_address_part = "lenora"

        # Check if the guess matches the correct location (case-insensitive for city and address part)
        if correct_city in city.lower() and correct_address_part in address.lower():
            return {
                "status": "Correct!",
                "message": "You found the treasure!"
            }
        else:
            return {
                "status": "Incorrect",
                "message": "Sorry, that's not the right location."
            }
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """
        Provides a list of `ToolTestCase` objects for testing the `GuessLocationTool`.

        These test cases cover various natural language requests that should map
        to the `guess_location` tool, including specific and general location guesses.
        """
        return [
            ToolTestCase(
                request="I think the treasure is at the library",
                expected_tools=["guess_location"],
                description="Guessing treasure location"
            ),
            ToolTestCase(
                request="Is it in Seattle on Lenora Street?",
                expected_tools=["guess_location"],
                description="Specific location guess"
            ),
            ToolTestCase(
                request="The treasure must be in Washington state",
                expected_tools=["guess_location"],
                description="State-level guess"
            )
        ]