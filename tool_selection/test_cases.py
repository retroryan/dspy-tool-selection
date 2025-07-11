"""Test case definitions for tool selection evaluation."""

from typing import List
from shared_utils.models import TestCase


def get_default_test_cases() -> List[TestCase]:
    """Get the default set of test cases for tool selection evaluation."""
    return [
        TestCase(
            request="I'm stuck on the treasure hunt. Can you help?",
            expected_tools=["give_hint"],
            description="Single tool selection for hint request"
        ),
        TestCase(
            request="Is the treasure at the beach?",
            expected_tools=["guess_location"],
            description="Single tool selection for location guess"
        ),
        TestCase(
            request="I need a hint and also want to check if it's at the park",
            expected_tools=["give_hint", "guess_location"],
            description="Multi-tool selection for hint and guess"
        ),
        TestCase(
            request="Give me a hint, and let me guess both the beach and the park",
            expected_tools=["give_hint", "guess_location"],
            description="Multi-tool with multiple guesses (but only one tool instance)"
        ),
        TestCase(
            request="What's the weather like today?",
            expected_tools=[],
            description="No tool selection for unrelated request"
        ),
        TestCase(
            request="I want to check the library and museum, then get a hint if I'm wrong",
            expected_tools=["guess_location", "give_hint"],
            description="Multi-tool with conditional logic"
        ),
        TestCase(
            request="Tell me about the treasure hunt game",
            expected_tools=[],
            description="No tool selection for general inquiry"
        ),
        TestCase(
            request="hint please",
            expected_tools=["give_hint"],
            description="Single tool with minimal request"
        ),
        TestCase(
            request="I think I know where it is - the old oak tree!",
            expected_tools=["guess_location"],
            description="Implicit guess request"
        ),
        TestCase(
            request="Can you give me three hints and check if it's at the lighthouse?",
            expected_tools=["give_hint", "guess_location"],
            description="Multi-tool with quantity request"
        ),
        TestCase(
            request="I'm ready to make my final guess: the treasure is at the fountain",
            expected_tools=["guess_location"],
            description="Explicit final guess"
        ),
    ]


def get_multi_tool_test_cases() -> List[TestCase]:
    """Get test cases for multi-tool selection evaluation (14 tools)."""
    return [
        TestCase(
            request="What's the weather like today?",
            expected_tools=["get_weather"],
            description="Single tool selection - weather query"
        ),
        TestCase(
            request="I need to find concerts in Seattle next Friday and then buy tickets",
            expected_tools=["find_events", "search_products", "add_to_cart"],
            description="Multi-step event finding and purchasing"
        ),
        TestCase(
            request="Show me my checking account balance",
            expected_tools=["check_balance"],
            description="Simple finance query"
        ),
        TestCase(
            request="I want to return the shoes I bought last week and check on my refund status",
            expected_tools=["return_item", "track_order"],
            description="E-commerce return process"
        ),
        TestCase(
            request="Transfer $500 from savings to checking, then pay my electric bill of $150",
            expected_tools=["transfer_money", "pay_bill"],
            description="Sequential finance operations"
        ),
        TestCase(
            request="Find sports events this weekend and see if there are any tickets available under $100",
            expected_tools=["find_events", "search_products"],
            description="Event discovery with price constraint"
        ),
        TestCase(
            request="I need my bank statement and want to track my recent Amazon order",
            expected_tools=["get_statement", "track_order"],
            description="Mixed domain query"
        ),
        TestCase(
            request="Cancel my dinner reservation for tonight",
            expected_tools=["cancel_event"],
            description="Event cancellation (ambiguous - could be interpreted differently)"
        ),
        TestCase(
            request="Help me plan a party - find a venue, create the event, and look for decorations",
            expected_tools=["find_events", "create_event", "search_products"],
            description="Complex multi-tool party planning"
        ),
        TestCase(
            request="Check if I have enough money to buy that new laptop",
            expected_tools=["check_balance", "search_products"],
            description="Pre-purchase verification"
        ),
        TestCase(
            request="I want to invest some money after checking my balance",
            expected_tools=["check_balance", "invest"],
            description="Investment planning"
        )
    ]