"""Comprehensive test suite for all 14 multi-domain tools."""
import pytest
from pydantic import ValidationError

# Import all tools to register them
# Events
import tools.events.find_events
import tools.events.create_event
import tools.events.cancel_event

# E-commerce
import tools.ecommerce.search_products
import tools.ecommerce.add_to_cart
import tools.ecommerce.track_order
import tools.ecommerce.return_item

# Finance
import tools.finance.check_balance
import tools.finance.transfer_money
import tools.finance.pay_bill
import tools.finance.get_statement
import tools.finance.invest

# Existing tools
import tools.treasure_hunt.give_hint
import tools.treasure_hunt.guess_location
import tools.productivity.set_reminder

from tool_selection.registry import registry
from tool_selection.tool_sets import tool_set_registry


class TestAllToolsRegistration:
    """Test that all tools are properly registered."""
    
    def test_all_tools_registered(self):
        """Verify all 14 multi-domain tools plus existing tools are registered."""
        expected_tools = [
            # Events (3)
            "find_events", "create_event", "cancel_event",
            # E-commerce (4)
            "search_products", "add_to_cart", "track_order", "return_item",
            # Finance (5)
            "check_balance", "transfer_money", "pay_bill", "get_statement", "invest",
            # Existing tools (3)
            "give_hint", "guess_location", "set_reminder"
        ]
        
        registered_tools = registry.get_tool_names()
        
        for tool_name in expected_tools:
            assert tool_name in registered_tools, f"Tool {tool_name} not registered"
        
        # Total should be at least 15 tools
        assert len(registered_tools) >= 15
    
    def test_tool_categories(self):
        """Test that tools are properly categorized."""
        # Check events tools
        events_tools = registry.get_tools_by_category("events")
        assert len(events_tools) == 3
        assert "find_events" in events_tools
        assert "create_event" in events_tools
        assert "cancel_event" in events_tools
        
        # Check e-commerce tools
        ecommerce_tools = registry.get_tools_by_category("ecommerce")
        assert len(ecommerce_tools) == 4
        assert "search_products" in ecommerce_tools
        assert "add_to_cart" in ecommerce_tools
        assert "track_order" in ecommerce_tools
        assert "return_item" in ecommerce_tools
        
        # Check finance tools
        finance_tools = registry.get_tools_by_category("finance")
        assert len(finance_tools) == 5
        assert "check_balance" in finance_tools
        assert "transfer_money" in finance_tools
        assert "pay_bill" in finance_tools
        assert "get_statement" in finance_tools
        assert "invest" in finance_tools


class TestEventTools:
    """Test event management tools."""
    
    def test_find_events_execution(self):
        """Test find_events tool execution."""
        result = registry.execute_tool(
            "find_events",
            location="Seattle",
            date="this weekend",
            event_type="concert"
        )
        assert "events" in result
        assert "Seattle" in result["events"]
        assert "concert" in result["events"]
    
    def test_create_event_execution(self):
        """Test create_event tool execution."""
        result = registry.execute_tool(
            "create_event",
            title="Team Meeting",
            date="2024-12-25",
            location="Conference Room A"
        )
        assert result["status"] == "created"
        assert result["event_id"] == "EVT123"
        assert result["title"] == "Team Meeting"
    
    def test_cancel_event_execution(self):
        """Test cancel_event tool execution."""
        result = registry.execute_tool(
            "cancel_event",
            event_id="EVT123",
            reason="Weather conditions"
        )
        assert result["status"] == "cancelled"
        assert result["event_id"] == "EVT123"
        assert result["reason"] == "Weather conditions"
    
    def test_cancel_event_without_reason(self):
        """Test cancel_event without optional reason."""
        result = registry.execute_tool(
            "cancel_event",
            event_id="EVT456"
        )
        assert result["status"] == "cancelled"
        assert result["reason"] == "No reason provided"


class TestEcommerceTools:
    """Test e-commerce tools."""
    
    def test_search_products_execution(self):
        """Test search_products tool execution."""
        result = registry.execute_tool(
            "search_products",
            query="laptop",
            category="electronics",
            max_price=1500.0
        )
        assert "products" in result
        assert "laptop" in result["products"]
        assert result["filters"]["max_price"] == 1500.0
    
    def test_add_to_cart_execution(self):
        """Test add_to_cart tool execution."""
        result = registry.execute_tool(
            "add_to_cart",
            product_id="PROD123",
            quantity=2
        )
        assert result["status"] == "success"
        assert result["added"] == "PROD123"
        assert result["quantity"] == 2
    
    def test_track_order_execution(self):
        """Test track_order tool execution."""
        result = registry.execute_tool(
            "track_order",
            order_id="ORD789"
        )
        assert result["order_id"] == "ORD789"
        assert result["status"] == "In transit"
        assert "tracking_number" in result
    
    def test_return_item_execution(self):
        """Test return_item tool execution."""
        result = registry.execute_tool(
            "return_item",
            order_id="ORD456",
            item_id="ITEM123",
            reason="Defective product"
        )
        assert result["return_id"] == "RET456"
        assert result["status"] == "processing"
        assert result["reason"] == "Defective product"


class TestFinanceTools:
    """Test finance tools."""
    
    def test_check_balance_execution(self):
        """Test check_balance tool execution."""
        result = registry.execute_tool(
            "check_balance",
            account_type="savings"
        )
        assert result["account"] == "savings"
        assert "balance" in result
        assert "available" in result
    
    def test_transfer_money_execution(self):
        """Test transfer_money tool execution."""
        result = registry.execute_tool(
            "transfer_money",
            amount=500.0,
            to_account="checking",
            from_account="savings"
        )
        assert result["status"] == "completed"
        assert result["amount"] == 500.0
        assert result["transaction_id"] == "TXN456"
    
    def test_pay_bill_execution(self):
        """Test pay_bill tool execution."""
        result = registry.execute_tool(
            "pay_bill",
            biller="Electric Company",
            amount=150.0,
            account_number="12345"
        )
        assert "Paid $150" in result["confirmation"]
        assert "Electric Company" in result["confirmation"]
        assert result["status"] == "completed"
    
    def test_get_statement_execution(self):
        """Test get_statement tool execution."""
        result = registry.execute_tool(
            "get_statement",
            account="checking",
            period="last month"
        )
        assert result["account"] == "checking"
        assert result["period"] == "last month"
        assert result["transactions"] == 42
    
    def test_invest_execution(self):
        """Test invest tool execution."""
        result = registry.execute_tool(
            "invest",
            amount=1000.0,
            investment_type="stocks"
        )
        assert result["amount"] == 1000.0
        assert result["type"] == "stocks"
        assert result["investment_id"] == "INV789"


class TestToolValidation:
    """Test argument validation for tools."""
    
    def test_invalid_transfer_amount(self):
        """Test transfer_money with negative amount."""
        with pytest.raises(ValidationError):
            registry.execute_tool(
                "transfer_money",
                amount=-100.0,  # Invalid negative amount
                to_account="checking",
                from_account="savings"
            )
    
    def test_invalid_add_to_cart_quantity(self):
        """Test add_to_cart with invalid quantity."""
        with pytest.raises(ValidationError):
            registry.execute_tool(
                "add_to_cart",
                product_id="PROD123",
                quantity=0  # Invalid zero quantity
            )
    
    def test_missing_required_arguments(self):
        """Test tools with missing required arguments."""
        with pytest.raises(ValidationError):
            registry.execute_tool(
                "create_event",
                title="Meeting"  # Missing date and location
            )


class TestToolSets:
    """Test tool sets functionality."""
    
    def test_all_tool_sets_registered(self):
        """Test that all tool sets are registered."""
        all_sets = tool_set_registry.get_all_tool_sets()
        
        expected_sets = [
            "treasure_hunt", "productivity", 
            "events", "ecommerce", "finance", "multi_domain"
        ]
        
        for set_name in expected_sets:
            assert set_name in all_sets, f"Tool set {set_name} not registered"
    
    def test_events_tool_set(self):
        """Test events tool set loads correct tools."""
        tool_set = tool_set_registry.tool_sets["events"]
        loaded_tools = tool_set.get_loaded_tools()
        
        assert "find_events" in loaded_tools
        assert "create_event" in loaded_tools
        assert "cancel_event" in loaded_tools
    
    def test_finance_tool_set(self):
        """Test finance tool set loads correct tools."""
        tool_set = tool_set_registry.tool_sets["finance"]
        loaded_tools = tool_set.get_loaded_tools()
        
        assert len(loaded_tools) == 5
        assert "check_balance" in loaded_tools
        assert "transfer_money" in loaded_tools
        assert "pay_bill" in loaded_tools
        assert "get_statement" in loaded_tools
        assert "invest" in loaded_tools
    
    def test_multi_domain_tool_set(self):
        """Test multi-domain tool set combines tools from different categories."""
        tool_set = tool_set_registry.tool_sets["multi_domain"]
        loaded_tools = tool_set.get_loaded_tools()
        
        # Should have tools from multiple domains
        assert "find_events" in loaded_tools  # Events
        assert "search_products" in loaded_tools  # E-commerce
        assert "check_balance" in loaded_tools  # Finance
        assert "set_reminder" in loaded_tools  # Productivity


class TestAllTestCases:
    """Test that all tools provide test cases."""
    
    def test_all_tools_have_test_cases(self):
        """Verify every tool provides at least one test case."""
        all_tools = registry.get_all_tools()
        
        for tool_name, tool in all_tools.items():
            test_cases = tool.get_test_cases()
            assert len(test_cases) > 0, f"Tool {tool_name} has no test cases"
            
            # Verify test case format
            for tc in test_cases:
                assert hasattr(tc, 'request')
                assert hasattr(tc, 'expected_tools')
                assert hasattr(tc, 'description')
                assert tool_name in tc.expected_tools
    
    def test_total_test_case_count(self):
        """Test that we have a comprehensive set of test cases."""
        all_test_cases = registry.get_all_test_cases()
        
        # Should have at least 2 test cases per tool (15 tools * 2 = 30)
        assert len(all_test_cases) >= 30
        
        # Plus tool set test cases
        tool_set_test_cases = tool_set_registry.get_all_test_cases()
        assert len(tool_set_test_cases) >= 10
        
        # Total should be substantial
        total_test_cases = len(all_test_cases) + len(tool_set_test_cases)
        assert total_test_cases >= 40