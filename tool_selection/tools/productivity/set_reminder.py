"""
Set reminder tool implementation using the new base classes.

This module defines the `SetReminderTool`, which allows users to set reminders
with a specified message and time. It integrates with the tool selection
framework by extending `BaseTool` and registering itself.
"""
from typing import List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from tool_selection.base_tool import BaseTool, ToolTestCase
from tool_selection.registry import register_tool


@register_tool
class SetReminderTool(BaseTool):
    """
    A tool for setting reminders for the user.

    This tool takes a message and a time, and simulates setting a reminder.
    It demonstrates how to define a tool with arguments and provide test cases.
    """
    NAME = "set_reminder"
    MODULE = "productivity"
    
    class Arguments(BaseModel):
        """
        Defines the arguments required for the `set_reminder` tool.

        This Pydantic model ensures that the `message` and `time` arguments
        are provided and meet basic validation criteria.
        """
        message: str = Field(
            ..., 
            min_length=1, 
            max_length=500,
            description="The message content for the reminder (e.g., 'Call mom', 'Buy groceries')"
        )
        time: str = Field(
            ..., 
            description="When the reminder should trigger (e.g., '2pm', 'tomorrow morning', 'in 30 minutes')"
        )
        
        @field_validator('time')
        @classmethod
        def validate_time(cls, v: str) -> str:
            """Validates that the 'time' string is not empty or just whitespace."""
            if not v.strip():
                raise ValueError("Time cannot be empty or just whitespace.")
            return v.strip()
    
    # Tool-specific description and argument model linkage
    description: str = "Set a reminder for a specific time with a custom message."
    args_model: type[BaseModel] = Arguments
    
    def execute(self, message: str, time: str) -> dict:
        """
        Executes the set reminder action.

        In a real application, this method would interact with a reminder service
        or system API to schedule the reminder. Here, it simulates the action
        by returning a confirmation message.

        Args:
            message (str): The reminder message.
            time (str): The specified time for the reminder.

        Returns:
            dict: A dictionary indicating the status of the reminder setting operation.
        """
        # Simulate scheduling the reminder
        reminder_id = f"rem_{datetime.now().timestamp():.0f}"
        return {
            "status": "success",
            "message": f"Reminder set: '{message}' at {time}",
            "reminder_id": reminder_id
        }
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """
        Provides a list of `ToolTestCase` objects for testing the `SetReminderTool`.

        These test cases cover various natural language requests that should map
        to the `set_reminder` tool.
        """
        return [
            ToolTestCase(
                request="Remind me to call mom at 3pm",
                expected_tools=["set_reminder"],
                description="Basic reminder with time"
            ),
            ToolTestCase(
                request="Set a reminder for tomorrow to buy groceries",
                expected_tools=["set_reminder"],
                description="Future reminder"
            ),
            ToolTestCase(
                request="I need a reminder in 30 minutes to check the oven",
                expected_tools=["set_reminder"],
                description="Relative time reminder"
            ),
            ToolTestCase(
                request="Don't let me forget the meeting at 2pm",
                expected_tools=["set_reminder"],
                description="Alternative phrasing"
            )
        ]