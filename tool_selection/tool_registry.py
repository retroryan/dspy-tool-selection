"""Multi-tool registry with multiple domain-specific tools for testing LLM tool selection."""

import sys
from pathlib import Path
from typing import List, Dict, Callable, Any

sys.path.append(str(Path(__file__).parent.parent / "tools"))

from .models import MultiToolName, MultiTool, MultiToolDecision, ToolCall, ToolArgument


class MultiToolRegistry:
    """Registry for multi-domain tools."""
    
    def __init__(self):
        self._tools: Dict[MultiToolName, MultiTool] = {}
        self._functions: Dict[MultiToolName, Callable] = {}
        
    def register(self, tool: MultiTool, func: Callable):
        """Register a tool with its schema and function."""
        self._tools[tool.name] = tool
        self._functions[tool.name] = func
        
    def get_tool_definitions(self) -> List[MultiTool]:
        """Get all tool schemas."""
        return list(self._tools.values())
        
    def get_tool_names(self) -> tuple[str, ...]:
        """Get all registered tool names."""
        return tuple(tool.name.value for tool in self._tools.values())
        
    def execute(self, decision: MultiToolDecision) -> List[dict]:
        """Execute multiple tools based on the decision."""
        results = []
        
        for tool_call in decision.tool_calls:
            # Convert string tool name to MultiToolName enum
            try:
                tool_name = MultiToolName(tool_call.tool_name)
            except ValueError:
                results.append({
                    "error": f"Tool '{tool_call.tool_name}' is not a valid tool name.",
                    "tool": tool_call.tool_name
                })
                continue
            
            if tool_name not in self._functions:
                results.append({
                    "error": f"Tool '{tool_name.value}' not found in registry.",
                    "tool": tool_name.value
                })
                continue
                
            tool_func = self._functions[tool_name]
            
            try:
                result = tool_func(tool_call.arguments)
                results.append({
                    "tool": tool_name.value,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "tool": tool_name.value,
                    "error": str(e)
                })
                
        return results
        
    def register_all_tools(self):
        """Register all multi-domain tools for testing."""
        
        # Events tools
        self.register(
            MultiTool(
                name=MultiToolName.FIND_EVENTS,
                description="Find events based on location, date, or type",
                arguments=[
                    ToolArgument(name="location", type="str", description="City or venue"),
                    ToolArgument(name="date", type="str", description="Date or date range"),
                    ToolArgument(name="event_type", type="str", description="Type of event (concert, sports, etc)")
                ],
                category="events"
            ),
            lambda args: {"events": f"Found 5 events in {args.get('location', 'your area')}"}
        )
        
        self.register(
            MultiTool(
                name=MultiToolName.CREATE_EVENT,
                description="Create a new event",
                arguments=[
                    ToolArgument(name="title", type="str", description="Event title"),
                    ToolArgument(name="date", type="str", description="Event date"),
                    ToolArgument(name="location", type="str", description="Event location")
                ],
                category="events"
            ),
            lambda args: {"event_id": "EVT123", "status": "created"}
        )
        
        self.register(
            MultiTool(
                name=MultiToolName.CANCEL_EVENT,
                description="Cancel an existing event or reservation",
                arguments=[
                    ToolArgument(name="event_id", type="str", description="Event or reservation ID"),
                    ToolArgument(name="reason", type="str", description="Cancellation reason")
                ],
                category="events"
            ),
            lambda args: {"status": "cancelled", "event_id": args.get("event_id", "unknown")}
        )
        
        # E-commerce tools
        self.register(
            MultiTool(
                name=MultiToolName.SEARCH_PRODUCTS,
                description="Search for products in the catalog",
                arguments=[
                    ToolArgument(name="query", type="str", description="Search query"),
                    ToolArgument(name="category", type="str", description="Product category"),
                    ToolArgument(name="max_price", type="float", description="Maximum price")
                ],
                category="ecommerce"
            ),
            lambda args: {"products": f"Found 10 products matching '{args.get('query', 'your search')}'"}
        )
        
        self.register(
            MultiTool(
                name=MultiToolName.ADD_TO_CART,
                description="Add a product to the shopping cart",
                arguments=[
                    ToolArgument(name="product_id", type="str", description="Product ID"),
                    ToolArgument(name="quantity", type="int", description="Quantity to add")
                ],
                category="ecommerce"
            ),
            lambda args: {"cart_total": 2, "added": args.get("product_id", "PROD123")}
        )
        
        self.register(
            MultiTool(
                name=MultiToolName.TRACK_ORDER,
                description="Track the status of an order",
                arguments=[
                    ToolArgument(name="order_id", type="str", description="Order ID")
                ],
                category="ecommerce"
            ),
            lambda args: {"status": "In transit", "delivery_date": "Tomorrow"}
        )
        
        self.register(
            MultiTool(
                name=MultiToolName.RETURN_ITEM,
                description="Return an item for refund or exchange",
                arguments=[
                    ToolArgument(name="order_id", type="str", description="Order ID"),
                    ToolArgument(name="item_id", type="str", description="Item ID to return"),
                    ToolArgument(name="reason", type="str", description="Return reason")
                ],
                category="ecommerce"
            ),
            lambda args: {"return_id": "RET456", "status": "processing", "refund_amount": "$99.99"}
        )
        
        # Finance tools
        self.register(
            MultiTool(
                name=MultiToolName.CHECK_BALANCE,
                description="Check account balance",
                arguments=[
                    ToolArgument(name="account_type", type="str", description="Account type (checking, savings)")
                ],
                category="finance"
            ),
            lambda args: {"balance": "$1,234.56", "account": args.get("account_type", "checking")}
        )
        
        self.register(
            MultiTool(
                name=MultiToolName.TRANSFER_MONEY,
                description="Transfer money between accounts or to another person",
                arguments=[
                    ToolArgument(name="amount", type="float", description="Amount to transfer"),
                    ToolArgument(name="to_account", type="str", description="Destination account"),
                    ToolArgument(name="from_account", type="str", description="Source account")
                ],
                category="finance"
            ),
            lambda args: {"transaction_id": "TXN456", "status": "completed"}
        )
        
        self.register(
            MultiTool(
                name=MultiToolName.PAY_BILL,
                description="Pay a bill",
                arguments=[
                    ToolArgument(name="biller", type="str", description="Biller name"),
                    ToolArgument(name="amount", type="float", description="Amount to pay"),
                    ToolArgument(name="account_number", type="str", description="Bill account number")
                ],
                category="finance"
            ),
            lambda args: {"confirmation": f"Paid ${args.get('amount', 0)} to {args.get('biller', 'biller')}"}
        )
        
        self.register(
            MultiTool(
                name=MultiToolName.GET_STATEMENT,
                description="Get account statement",
                arguments=[
                    ToolArgument(name="account", type="str", description="Account to get statement for"),
                    ToolArgument(name="period", type="str", description="Statement period (e.g., 'last month')")
                ],
                category="finance"
            ),
            lambda args: {"transactions": 42, "period": args.get("period", "last month")}
        )
        
        self.register(
            MultiTool(
                name=MultiToolName.INVEST,
                description="Invest money in stocks, bonds, or funds",
                arguments=[
                    ToolArgument(name="amount", type="float", description="Amount to invest"),
                    ToolArgument(name="investment_type", type="str", description="Type of investment (stocks, bonds, funds)")
                ],
                category="finance"
            ),
            lambda args: {"investment_id": "INV789", "amount": args.get("amount", 0), "type": args.get("investment_type", "stocks")}
        )