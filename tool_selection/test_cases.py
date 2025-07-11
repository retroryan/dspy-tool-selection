"""
Test case definitions for tool selection evaluation.

This module provides predefined sets of `ToolTestCase` objects used for
evaluating the performance of the tool selection mechanism. These test cases
cover various scenarios, from single tool selection to complex multi-tool
requests, and are crucial for assessing the accuracy and robustness of the
language model's tool-calling abilities.
"""

from typing import List
from tool_selection.base_tool import ToolTestCase


def get_default_test_cases() -> List[ToolTestCase]:
    """
    Returns a default set of test cases primarily focused on treasure hunt tools.

    These cases are designed to test basic single and multi-tool selection
    within a limited domain.

    Returns:
        List[ToolTestCase]: A list of `ToolTestCase` objects.
    """
    return [
        ToolTestCase(
            request="I'm stuck on the treasure hunt. Can you help?",
            expected_tools=["give_hint"],
            description="Single tool selection for hint request"
        ),
        ToolTestCase(
            request="Is the treasure at the beach?",
            expected_tools=["guess_location"],
            description="Single tool selection for location guess"
        ),
        ToolTestCase(
            request="I need a hint and also want to check if it's at the park",
            expected_tools=["give_hint", "guess_location"],
            description="Multi-tool selection for hint and guess"
        ),
        ToolTestCase(
            request="Give me a hint, and let me guess both the beach and the park",
            expected_tools=["give_hint", "guess_location"],
            description="Multi-tool with multiple guesses (but only one tool instance)"
        ),
        ToolTestCase(
            request="What's the weather like today?",
            expected_tools=[],
            description="No tool selection for unrelated request"
        ),
        ToolTestCase(
            request="I want to check the library and museum, then get a hint if I'm wrong",
            expected_tools=["guess_location", "give_hint"],
            description="Multi-tool with conditional logic"
        ),
        ToolTestCase(
            request="Tell me about the treasure hunt game",
            expected_tools=[],
            description="No tool selection for general inquiry"
        ),
        ToolTestCase(
            request="hint please",
            expected_tools=["give_hint"],
            description="Single tool with minimal request"
        ),
        ToolTestCase(
            request="I think I know where it is - the old oak tree!",
            expected_tools=["guess_location"],
            description="Implicit guess request"
        ),
        ToolTestCase(
            request="Can you give me three hints and check if it's at the lighthouse?",
            expected_tools=["give_hint", "guess_location"],
            description="Multi-tool with quantity request"
        ),
        ToolTestCase(
            request="I'm ready to make my final guess: the treasure is at the fountain",
            expected_tools=["guess_location"],
            description="Explicit final guess"
        ),
    ]


def get_multi_tool_test_cases() -> List[ToolTestCase]:
    """
    Returns a set of test cases designed for evaluating multi-tool selection
    across a broader range of domains (e.g., events, e-commerce, finance).

    These cases are more complex and involve scenarios requiring multiple
    distinct tools to fulfill the user's request.

    Returns:
        List[ToolTestCase]: A list of `ToolTestCase` objects.
    """
    return [
        ToolTestCase(
            request="What's the weather like today?",
            expected_tools=["get_weather"],
            description="Single tool selection - weather query"
        ),
        ToolTestCase(
            request="I need to find concerts in Seattle next Friday and then buy tickets",
            expected_tools=["find_events", "search_products", "add_to_cart"],
            description="Multi-step event finding and purchasing"
        ),
        ToolTestCase(
            request="Show me my checking account balance",
            expected_tools=["check_balance"],
            description="Simple finance query"
        ),
        ToolTestCase(
            request="I want to return the shoes I bought last week and check on my refund status",
            expected_tools=["return_item", "track_order"],
            description="E-commerce return process"
        ),
        ToolTestCase(
            request="Transfer $500 from savings to checking, then pay my electric bill of $150",
            expected_tools=["transfer_money", "pay_bill"],
            description="Sequential finance operations"
        ),
        ToolTestCase(
            request="Find sports events this weekend and see if there are any tickets available under $100",
            expected_tools=["find_events", "search_products"],
            description="Event discovery with price constraint"
        ),
        ToolTestCase(
            request="I need my bank statement and want to track my recent Amazon order",
            expected_tools=["get_statement", "track_order"],
            description="Mixed domain query"
        ),
        ToolTestCase(
            request="Cancel my dinner reservation for tonight",
            expected_tools=["cancel_event"],
            description="Event cancellation (ambiguous - could be interpreted differently)"
        ),
        ToolTestCase(
            request="Help me plan a party - find a venue, create the event, and look for decorations",
            expected_tools=["find_events", "create_event", "search_products"],
            description="Complex multi-tool party planning"
        ),
        ToolTestCase(
            request="Check if I have enough money to buy that new laptop",
            expected_tools=["check_balance", "search_products"],
            description="Pre-purchase verification"
        ),
        ToolTestCase(
            request="I want to invest some money after checking my balance",
            expected_tools=["check_balance", "invest"],
            description="Investment planning"
        )
    ]