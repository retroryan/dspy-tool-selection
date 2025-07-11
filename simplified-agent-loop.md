# DSPy ReAct Agent Loop Implementation

## Overview

This implementation leverages DSPy's native `ReAct` module to create agent loops that can iteratively select and execute tools. ReAct (Reasoning and Acting) is DSPy's built-in paradigm for tool-using agents that automatically handles the loop mechanics, tool selection, and termination logic.

## Why Use DSPy ReAct?

1. **Battle-tested**: ReAct is a proven pattern used in production systems
2. **Native DSPy**: Built-in module with full optimization support
3. **Automatic Loop Management**: Handles iterations, termination, and trajectory tracking
4. **Tool Integration**: First-class support for tools with automatic metadata extraction
5. **Signature Polymorphism**: Works with any signature, not just Q&A

## Core Implementation

### 1. Basic ReAct Agent

```python
import dspy
from typing import List, Dict, Any

# Define tools as simple functions
def search_products(query: str, category: str = "all") -> str:
    """Search for products in our catalog."""
    # In real implementation, this would call an API or database
    return f"Found 5 products matching '{query}' in category '{category}'"

def calculate_discount(price: float, discount_percent: float) -> str:
    """Calculate discounted price."""
    final_price = price * (1 - discount_percent / 100)
    return f"Original: ${price}, Discount: {discount_percent}%, Final: ${final_price:.2f}"

def check_inventory(product_id: str) -> str:
    """Check product availability in inventory."""
    # Mock implementation
    return f"Product {product_id} is in stock with 10 units available"

# Create ReAct agent with custom signature
agent = dspy.ReAct(
    signature="customer_query -> response",
    tools=[search_products, calculate_discount, check_inventory],
    max_iters=5
)

# Use the agent
result = agent(customer_query="I'm looking for laptops under $1000 with at least 20% discount")
print(result.response)
```

### 2. Advanced Multi-Step Agent

```python
import dspy
from dataclasses import dataclass
from typing import Optional

# More complex tools with structured inputs
@dataclass
class FlightSearchParams:
    origin: str
    destination: str
    date: str
    class_type: Optional[str] = "economy"

def search_flights(params: FlightSearchParams) -> str:
    """Search for available flights."""
    return f"Found 8 flights from {params.origin} to {params.destination} on {params.date}"

def get_weather(city: str, date: str) -> str:
    """Get weather forecast for a city on a specific date."""
    return f"Weather in {city} on {date}: Sunny, 72°F"

def book_hotel(city: str, checkin: str, checkout: str, guests: int = 1) -> str:
    """Search and book hotels."""
    return f"Found 5 hotels in {city} from {checkin} to {checkout} for {guests} guests"

def create_itinerary(trip_details: dict) -> str:
    """Create a complete trip itinerary."""
    return f"Itinerary created with {len(trip_details)} items"

# Create travel planning agent
travel_agent = dspy.ReAct(
    signature="travel_request -> itinerary, total_cost",
    tools=[search_flights, get_weather, book_hotel, create_itinerary],
    max_iters=10
)

# Complex multi-step request
result = travel_agent(
    travel_request="Plan a 3-day trip from NYC to Paris next month, including flights, hotel, and weather info"
)
print(f"Itinerary: {result.itinerary}")
print(f"Total Cost: {result.total_cost}")
```

### 3. Integration with Existing Tool System

```python
from tool_selection.models import MultiTool, MultiToolName
from typing import Callable

class DSPyReActAdapter:
    """Adapter to use existing tool definitions with DSPy ReAct."""
    
    @staticmethod
    def create_tool_function(tool_def: MultiTool, implementation: Callable) -> Callable:
        """Create a DSPy-compatible tool function from MultiTool definition."""
        
        def wrapped_tool(**kwargs):
            """Auto-generated tool function."""
            # DSPy will pass arguments as keyword arguments
            # Convert to the format expected by the implementation
            result = implementation(kwargs)
            
            # Ensure result is a string for ReAct
            if isinstance(result, dict):
                return str(result)
            return result
        
        # Set function metadata for DSPy
        wrapped_tool.__name__ = tool_def.name.value
        wrapped_tool.__doc__ = tool_def.description
        
        # Add parameter information to docstring
        if tool_def.arguments:
            param_docs = "\n\nParameters:\n"
            for arg in tool_def.arguments:
                param_docs += f"    {arg.name} ({arg.type}): {arg.description}\n"
            wrapped_tool.__doc__ += param_docs
        
        return wrapped_tool
    
    @staticmethod
    def create_react_agent(
        signature: str,
        tool_definitions: List[MultiTool],
        tool_implementations: Dict[str, Callable],
        max_iters: int = 10
    ) -> dspy.ReAct:
        """Create a ReAct agent from existing tool definitions."""
        
        # Convert tools to DSPy-compatible format
        dspy_tools = []
        for tool_def in tool_definitions:
            impl = tool_implementations.get(tool_def.name.value)
            if impl:
                dspy_tool = DSPyReActAdapter.create_tool_function(tool_def, impl)
                dspy_tools.append(dspy_tool)
        
        # Create ReAct agent
        return dspy.ReAct(
            signature=signature,
            tools=dspy_tools,
            max_iters=max_iters
        )

# Example usage with existing tools
from tool_selection.tool_registry import MultiToolRegistry

# Set up existing tools
registry = MultiToolRegistry()
registry.register_all_tools()

# Get tool definitions and implementations
tool_defs = registry.get_tool_definitions()
tool_impls = {name: func for name, func in registry._functions.items()}

# Create ReAct agent
agent = DSPyReActAdapter.create_react_agent(
    signature="user_request -> response, actions_taken",
    tool_definitions=tool_defs[:5],  # Use first 5 tools
    tool_implementations=tool_impls,
    max_iters=7
)

# Run the agent
result = agent(user_request="Find concerts in NYC and book the cheapest ticket")
print(f"Response: {result.response}")
print(f"Actions taken: {result.actions_taken}")
```

### 4. Optimizing ReAct Agents

```python
import dspy
from dspy.teleprompt import BootstrapFewShot

# Define evaluation metric
def is_successful_response(example, pred, trace=None):
    """Check if the agent successfully completed the task."""
    # Must have a response
    if not pred.response or len(pred.response) < 10:
        return False
    
    # Must have used at least one tool (check trajectory)
    if not hasattr(pred, 'trajectory') or not pred.trajectory:
        return False
    
    # Check if the response addresses the query
    query_keywords = example.customer_query.lower().split()
    response_lower = pred.response.lower()
    
    # At least half the query keywords should appear in response
    matches = sum(1 for keyword in query_keywords if keyword in response_lower)
    return matches >= len(query_keywords) / 2

# Create training examples
trainset = [
    dspy.Example(
        customer_query="Find me a laptop under $800",
        response="I found 3 laptops under $800: Dell Inspiron 15 ($699), HP Pavilion ($750), and Lenovo IdeaPad ($799)."
    ).with_inputs("customer_query"),
    dspy.Example(
        customer_query="What's the weather in Tokyo and are there flights from LAX?",
        response="The weather in Tokyo is currently 68°F with light rain. There are 8 daily flights from LAX to Tokyo, with prices starting at $599."
    ).with_inputs("customer_query"),
    # Add more examples...
]

# Optimize the agent
teleprompter = BootstrapFewShot(
    metric=is_successful_response,
    max_bootstrapped_demos=3,
    max_rounds=2
)

optimized_agent = teleprompter.compile(agent, trainset=trainset)

# The optimized agent now includes few-shot examples
result = optimized_agent(customer_query="I need a gaming laptop with good graphics")
```

### 5. Custom ReAct Signatures

```python
# ReAct works with any signature, not just Q&A

# Customer service with multiple outputs
service_agent = dspy.ReAct(
    signature="customer_issue -> solution, priority_level, follow_up_needed",
    tools=[check_account, process_refund, escalate_ticket, send_notification],
    max_iters=8
)

# Data analysis with structured outputs  
analyst_agent = dspy.ReAct(
    signature="dataset_name, analysis_request -> insights:list[str], visualization_urls:list[str], confidence_score:float",
    tools=[load_data, calculate_statistics, create_plots, generate_report],
    max_iters=10
)

# Multi-language support
translator_agent = dspy.ReAct(
    signature="text, source_lang, target_lang -> translation, quality_score, alternative_translations:list[str]",
    tools=[detect_language, translate_text, check_grammar, suggest_alternatives],
    max_iters=5
)
```

## Key Features of DSPy ReAct

### 1. Automatic Loop Management
- ReAct handles the iteration loop internally
- Automatically stops when task is complete or max_iters reached
- No manual loop implementation needed

### 2. Built-in Reasoning
- Generates "thoughts" before each tool use
- Maintains trajectory of all thoughts, actions, and observations
- Reasoning is part of the optimization process

### 3. Tool Integration
- Tools are just Python functions with docstrings
- Automatic parameter extraction from function signatures
- Error handling for failed tool calls

### 4. Signature Polymorphism
- Works with any DSPy signature
- Multiple outputs supported
- Type hints for better code completion

### 5. Optimization Support
- Compatible with all DSPy teleprompters
- Can learn from examples to improve performance
- Trajectory can be used for debugging

## Best Practices

### 1. Tool Design
```python
def good_tool(param1: str, param2: int = 10) -> str:
    """Clear description of what this tool does.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter with default
        
    Returns:
        String description of the result
    """
    # Always return strings for ReAct
    result = do_something(param1, param2)
    return f"Processed {param1} with value {param2}: {result}"
```

### 2. Signature Design
```python
# Be specific about inputs and outputs
specific_agent = dspy.ReAct(
    signature="product_name, customer_requirements -> recommendation, alternatives:list[str], price_range",
    tools=[...],
    max_iters=5
)

# Use type hints for clarity
from typing import List
typed_agent = dspy.ReAct(
    signature="query:str -> results:List[str], confidence:float",
    tools=[...],
    max_iters=7
)
```

### 3. Error Handling
```python
def robust_tool(data: str) -> str:
    """Tool with proper error handling."""
    try:
        result = process_data(data)
        return f"Success: {result}"
    except ValueError as e:
        return f"Error: Invalid data format - {str(e)}"
    except Exception as e:
        return f"Error: Unexpected issue - {str(e)}"
```

## Performance Considerations

1. **Iteration Limits**: Set appropriate max_iters based on task complexity
2. **Tool Design**: Keep tools focused and fast
3. **Caching**: DSPy supports caching for repeated calls
4. **Optimization**: Use teleprompters to reduce iterations needed

## Conclusion

DSPy's ReAct module provides a complete, production-ready solution for building agent loops. By using the native implementation instead of building custom loops, we get:

- **Less Code**: No need to implement loop logic
- **Better Performance**: Optimized by the DSPy team
- **Full Compatibility**: Works with all DSPy features
- **Proven Patterns**: Based on established research

The key insight is that DSPy ReAct already **is** an agent loop - we don't need to build one. Just define your tools, create a signature for your task, and ReAct handles the rest.