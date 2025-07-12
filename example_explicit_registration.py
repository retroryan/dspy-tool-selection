"""
Example of explicit tool registration and usage.

This demonstrates the new explicit registration pattern without decorators.
"""

from shared.tool_set_registry import (
    create_tool_set_registry,
    create_ecommerce_tool_set_registry,
    create_productivity_tool_set_registry
)
from shared.models import ToolCall
from agentic_loop.activity_manager import ActivityManager
from agentic_loop.manual_agent_loop import ManualAgentLoop
from agentic_loop.agent_reasoner import AgentReasoner


def example_treasure_hunt_registry():
    """Example: Create and use treasure hunt tool registry."""
    print("=== Treasure Hunt Tool Registry ===")
    
    # Create registry with treasure hunt tools
    registry = create_tool_set_registry()
    
    # Show available tools
    print(f"Available tools: {registry.get_tool_names()}")
    print(f"Loaded tool sets: {registry.get_loaded_tool_sets()}")
    
    # Execute a tool
    tool_call = ToolCall(
        tool_name="give_hint",
        arguments={"hint_total": 0}
    )
    
    result = registry.execute_tool(tool_call)
    print(f"Tool execution result: {result.result}")
    print(f"Success: {result.success}")
    print()


def example_ecommerce_registry():
    """Example: Create and use ecommerce tool registry."""
    print("=== E-commerce Tool Registry ===")
    
    # Create registry with ecommerce tools
    registry = create_ecommerce_tool_set_registry()
    
    # Show available tools
    print(f"Available tools: {registry.get_tool_names()}")
    print(f"Loaded tool sets: {registry.get_loaded_tool_sets()}")
    
    # Execute a tool
    tool_call = ToolCall(
        tool_name="search_products",
        arguments={"query": "laptops", "max_price": 1000.0}
    )
    
    result = registry.execute_tool(tool_call)
    print(f"Tool execution result: {result.result}")
    print(f"Success: {result.success}")
    print()


def example_productivity_registry():
    """Example: Create and use productivity tool registry."""
    print("=== Productivity Tool Registry ===")
    
    # Create registry with productivity tools
    registry = create_productivity_tool_set_registry()
    
    # Show available tools
    print(f"Available tools: {registry.get_tool_names()}")
    print(f"Loaded tool sets: {registry.get_loaded_tool_sets()}")
    
    # Execute a tool
    tool_call = ToolCall(
        tool_name="set_reminder",
        arguments={"message": "Meeting at 3pm", "datetime": "2024-01-15 15:00"}
    )
    
    result = registry.execute_tool(tool_call)
    print(f"Tool execution result: {result.result}")
    print(f"Success: {result.success}")
    print()


def example_activity_manager():
    """Example: Use ActivityManager with explicit registry."""
    print("=== Activity Manager with Explicit Registry ===")
    
    # Create registry
    registry = create_tool_set_registry()
    
    # Create agent components (without actual LLM for demo)
    tool_names = registry.get_tool_names()
    
    # Create a simple mock agent loop for demonstration
    class MockAgentLoop:
        def __init__(self, tool_names):
            self.tool_names = tool_names
        
        def get_available_tools(self):
            return self.tool_names
    
    agent_loop = MockAgentLoop(tool_names)
    
    # Create activity manager
    activity_manager = ActivityManager(
        agent_loop=agent_loop,
        tool_registry=registry,
        max_iterations=3,
        timeout_seconds=30.0
    )
    
    print(f"Activity manager created with {len(activity_manager.get_available_tools())} tools")
    print(f"Available tools: {activity_manager.get_available_tools()}")
    
    # Note: Running the activity manager would require an actual LLM to be configured
    # This example just shows the setup
    print()


def main():
    """Run all examples."""
    print("Explicit Tool Registration Examples")
    print("="*50)
    
    example_treasure_hunt_registry()
    example_ecommerce_registry()
    example_productivity_registry()
    example_activity_manager()
    
    print("All examples completed successfully!")


if __name__ == "__main__":
    main()