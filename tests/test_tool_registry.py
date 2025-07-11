"""Tests for the tool registry."""

import pytest
from tool_selection.tool_registry import MultiToolRegistry
from tool_selection.models import MultiTool, MultiToolName, MultiToolDecision, ToolCall, ToolArgument


@pytest.fixture
def registry():
    """Create an empty registry."""
    return MultiToolRegistry()


@pytest.fixture
def sample_tool():
    """Create a sample tool."""
    return MultiTool(
        name=MultiToolName.CHECK_BALANCE,
        description="Check account balance",
        category="finance",
        arguments=[
            ToolArgument(name="account_type", type="str", description="Account type")
        ]
    )


def test_register_tool(registry, sample_tool):
    """Test registering a tool."""
    def check_balance_func(args):
        return {"balance": 1000, "account": args.get("account_type", "checking")}
    
    registry.register(sample_tool, check_balance_func)
    
    assert MultiToolName.CHECK_BALANCE in registry._tools
    assert MultiToolName.CHECK_BALANCE in registry._functions


def test_get_tool_definitions(registry, sample_tool):
    """Test getting all tool definitions."""
    registry.register(sample_tool, lambda args: {"result": "ok"})
    
    tools = registry.get_tool_definitions()
    assert len(tools) == 1
    assert tools[0].name == MultiToolName.CHECK_BALANCE


def test_execute_single_tool(registry, sample_tool):
    """Test executing a single tool."""
    def check_balance_func(args):
        return {"balance": 1000, "account": args.get("account_type", "checking")}
    
    registry.register(sample_tool, check_balance_func)
    
    decision = MultiToolDecision(
        tool_calls=[
            ToolCall(
                tool_name="check_balance",
                arguments={"account_type": "savings"}
            )
        ],
        reasoning="User wants to check balance"
    )
    
    results = registry.execute(decision)
    
    assert len(results) == 1
    assert results[0]["tool"] == "check_balance"
    assert "result" in results[0]
    assert results[0]["result"]["account"] == "savings"


def test_execute_multiple_tools(registry):
    """Test executing multiple tools."""
    # Register multiple tools
    registry.register(
        MultiTool(
            name=MultiToolName.CHECK_BALANCE,
            description="Check balance",
            category="finance",
            arguments=[]
        ),
        lambda args: {"balance": 1000}
    )
    
    registry.register(
        MultiTool(
            name=MultiToolName.FIND_EVENTS,
            description="Find events",
            category="events",
            arguments=[]
        ),
        lambda args: {"events": ["Concert", "Festival"]}
    )
    
    decision = MultiToolDecision(
        tool_calls=[
            ToolCall(tool_name="check_balance", arguments={}),
            ToolCall(tool_name="find_events", arguments={})
        ],
        reasoning="Multiple operations"
    )
    
    results = registry.execute(decision)
    
    assert len(results) == 2
    assert results[0]["tool"] == "check_balance"
    assert results[1]["tool"] == "find_events"


def test_execute_missing_tool(registry):
    """Test executing a tool that's not registered."""
    decision = MultiToolDecision(
        tool_calls=[
            ToolCall(tool_name="nonexistent_tool", arguments={})
        ],
        reasoning="Testing missing tool"
    )
    
    results = registry.execute(decision)
    
    assert len(results) == 1
    assert "error" in results[0]
    assert "not a valid tool name" in results[0]["error"]


def test_execute_tool_with_error(registry):
    """Test executing a tool that raises an exception."""
    def failing_tool(args):
        raise ValueError("Tool failed!")
    
    registry.register(
        MultiTool(
            name=MultiToolName.CHECK_BALANCE,
            description="Check balance",
            category="finance",
            arguments=[]
        ),
        failing_tool
    )
    
    decision = MultiToolDecision(
        tool_calls=[
            ToolCall(tool_name="check_balance", arguments={})
        ],
        reasoning="Testing error handling"
    )
    
    results = registry.execute(decision)
    
    assert len(results) == 1
    assert "error" in results[0]
    assert "Tool failed!" in results[0]["error"]


def test_register_all_tools():
    """Test the register_all_tools method."""
    registry = MultiToolRegistry()
    registry.register_all_tools()
    
    # Should have registered all tools from MultiToolName enum
    tool_names = registry.get_tool_names()
    assert len(tool_names) > 10  # Should have many tools
    
    # Check a few specific tools
    assert "find_events" in tool_names
    assert "check_balance" in tool_names
    assert "search_products" in tool_names