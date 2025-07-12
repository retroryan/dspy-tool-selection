"""Tests for ecommerce tools - order management, shopping cart, and product search."""
import pytest
from typing import List
from pydantic import ValidationError

from tools.ecommerce.get_order import GetOrderTool
from tools.ecommerce.list_orders import ListOrdersTool
from tools.ecommerce.add_to_cart import AddToCartTool
from tools.ecommerce.search_products import SearchProductsTool
from tools.ecommerce.track_order import TrackOrderTool
from tools.ecommerce.return_item import ReturnItemTool
from tool_selection.tool_sets import EcommerceToolSet


class TestGetOrderTool:
    """Test cases for GetOrderTool functionality."""
    
    def test_get_order_tool_implementation(self):
        """Test basic tool implementation."""
        tool = GetOrderTool()
        assert tool.name == "get_order"
        assert tool.description == "Get order details by order ID"
        assert len(tool.arguments) == 1
        assert tool.arguments[0].name == "order_id"
    
    def test_get_order_validation(self):
        """Test order ID validation."""
        tool = GetOrderTool()
        
        # Valid order ID
        result = tool.validate_and_execute(order_id="12345")
        assert "error" in result or "id" in result
        
        # Empty order ID should raise ValidationError
        with pytest.raises(ValidationError):
            tool.validate_and_execute(order_id="")
    
    def test_get_order_test_cases(self):
        """Test that test cases are properly defined."""
        test_cases = GetOrderTool.get_test_cases()
        assert len(test_cases) == 3
        assert all(case.expected_tools == ["get_order"] for case in test_cases)


class TestListOrdersTool:
    """Test cases for ListOrdersTool functionality."""
    
    def test_list_orders_tool_implementation(self):
        """Test basic tool implementation."""
        tool = ListOrdersTool()
        assert tool.name == "list_orders"
        assert tool.description == "List all orders for a customer by email address"
        assert len(tool.arguments) == 1
        assert tool.arguments[0].name == "email_address"
    
    def test_list_orders_validation(self):
        """Test email validation."""
        tool = ListOrdersTool()
        
        # Valid email
        result = tool.validate_and_execute(email_address="test@example.com")
        assert "error" in result or "orders" in result
        
        # Invalid email should raise ValidationError
        with pytest.raises(ValidationError):
            tool.validate_and_execute(email_address="invalid-email")
        
        # Empty email should raise ValidationError
        with pytest.raises(ValidationError):
            tool.validate_and_execute(email_address="")
    
    def test_list_orders_test_cases(self):
        """Test that test cases are properly defined."""
        test_cases = ListOrdersTool.get_test_cases()
        assert len(test_cases) == 3
        assert all(case.expected_tools == ["list_orders"] for case in test_cases)


class TestAddToCartTool:
    """Test cases for AddToCartTool functionality."""
    
    def test_add_to_cart_tool_implementation(self):
        """Test basic tool implementation."""
        tool = AddToCartTool()
        assert tool.name == "add_to_cart"
        assert tool.description == "Add a product to the shopping cart"
        assert len(tool.arguments) == 2
        
        # Check arguments
        product_id_arg = next(arg for arg in tool.arguments if arg.name == "product_id")
        quantity_arg = next(arg for arg in tool.arguments if arg.name == "quantity")
        
        assert product_id_arg.required is True
        assert quantity_arg.required is False
        assert quantity_arg.default == 1
    
    def test_add_to_cart_validation(self):
        """Test product ID and quantity validation."""
        tool = AddToCartTool()
        
        # Valid inputs
        result = tool.validate_and_execute(product_id="PROD123", quantity=2)
        assert result["status"] == "success"
        assert result["added"] == "PROD123"
        assert result["quantity"] == 2
        
        # Default quantity
        result = tool.validate_and_execute(product_id="PROD456")
        assert result["quantity"] == 1
        
        # Invalid quantity (negative)
        with pytest.raises(ValidationError):
            tool.validate_and_execute(product_id="PROD123", quantity=-1)
        
        # Invalid quantity (zero)
        with pytest.raises(ValidationError):
            tool.validate_and_execute(product_id="PROD123", quantity=0)
    
    def test_add_to_cart_test_cases(self):
        """Test that test cases are properly defined."""
        test_cases = AddToCartTool.get_test_cases()
        assert len(test_cases) == 2
        assert all(case.expected_tools == ["add_to_cart"] for case in test_cases)


class TestSearchProductsTool:
    """Test cases for SearchProductsTool functionality."""
    
    def test_search_products_tool_implementation(self):
        """Test basic tool implementation."""
        tool = SearchProductsTool()
        assert tool.name == "search_products"
        assert tool.description == "Search for products in the catalog"
        assert len(tool.arguments) == 3
        
        # Check arguments
        query_arg = next(arg for arg in tool.arguments if arg.name == "query")
        category_arg = next(arg for arg in tool.arguments if arg.name == "category")
        max_price_arg = next(arg for arg in tool.arguments if arg.name == "max_price")
        
        assert query_arg.required is True
        assert category_arg.required is False
        assert max_price_arg.required is False
    
    def test_search_products_validation(self):
        """Test search validation."""
        tool = SearchProductsTool()
        
        # Basic search
        result = tool.validate_and_execute(query="laptop")
        assert result["count"] == 10
        assert result["query"] == "laptop"
        
        # Search with filters
        result = tool.validate_and_execute(query="laptop", category="electronics", max_price=1000.0)
        assert result["filters"]["category"] == "electronics"
        assert result["filters"]["max_price"] == 1000.0
        
        # Invalid max_price (negative)
        with pytest.raises(ValidationError):
            tool.validate_and_execute(query="laptop", max_price=-100)
    
    def test_search_products_test_cases(self):
        """Test that test cases are properly defined."""
        test_cases = SearchProductsTool.get_test_cases()
        assert len(test_cases) == 3
        assert all(case.expected_tools == ["search_products"] for case in test_cases)


class TestTrackOrderTool:
    """Test cases for TrackOrderTool functionality."""
    
    def test_track_order_tool_implementation(self):
        """Test basic tool implementation."""
        tool = TrackOrderTool()
        assert tool.name == "track_order"
        assert tool.description == "Track the status of an order"
        assert len(tool.arguments) == 1
        assert tool.arguments[0].name == "order_id"
    
    def test_track_order_validation(self):
        """Test order tracking validation."""
        tool = TrackOrderTool()
        
        # Valid order ID
        result = tool.validate_and_execute(order_id="ORD123")
        assert result["order_id"] == "ORD123"
        assert result["status"] == "In transit"
        assert result["tracking_number"] == "TRKORD123"
    
    def test_track_order_test_cases(self):
        """Test that test cases are properly defined."""
        test_cases = TrackOrderTool.get_test_cases()
        assert len(test_cases) == 2
        assert all(case.expected_tools == ["track_order"] for case in test_cases)


class TestReturnItemTool:
    """Test cases for ReturnItemTool functionality."""
    
    def test_return_item_tool_implementation(self):
        """Test basic tool implementation."""
        tool = ReturnItemTool()
        assert tool.name == "return_item"
        assert tool.description == "Return an item for refund or exchange"
        assert len(tool.arguments) == 3
        
        # Check all arguments are required
        assert all(arg.required for arg in tool.arguments)
    
    def test_return_item_validation(self):
        """Test return item validation."""
        tool = ReturnItemTool()
        
        # Valid return request
        result = tool.validate_and_execute(
            order_id="ORD123",
            item_id="ITEM456",
            reason="Defective"
        )
        assert result["order_id"] == "ORD123"
        assert result["item_id"] == "ITEM456"
        assert result["reason"] == "Defective"
        assert result["status"] == "processing"
    
    def test_return_item_test_cases(self):
        """Test that test cases are properly defined."""
        test_cases = ReturnItemTool.get_test_cases()
        assert len(test_cases) == 2
        assert all(case.expected_tools == ["return_item"] for case in test_cases)


class TestEcommerceToolSet:
    """Test cases for EcommerceToolSet functionality."""
    
    def test_ecommerce_tool_set_creation(self):
        """Test tool set creation."""
        tool_set = EcommerceToolSet()
        assert tool_set.config.name == "ecommerce"
        assert "order management" in tool_set.config.description.lower()
        assert len(tool_set.config.tool_classes) == 6
    
    def test_ecommerce_tool_set_tools(self):
        """Test that all expected tools are included."""
        tool_set = EcommerceToolSet()
        tool_names = [tool_class.NAME for tool_class in tool_set.config.tool_classes]
        
        expected_tools = [
            "get_order",
            "list_orders", 
            "add_to_cart",
            "search_products",
            "track_order",
            "return_item"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tool_names
    
    def test_ecommerce_tool_set_test_cases(self):
        """Test that tool set test cases are properly defined."""
        test_cases = EcommerceToolSet.get_test_cases()
        assert len(test_cases) == 7
        assert all(case.tool_set == "ecommerce" for case in test_cases)
        
        # Check that we have test cases for different scenarios
        scenarios = [case.scenario for case in test_cases if case.scenario]
        assert "order_management" in scenarios
        assert "shopping" in scenarios
        assert "customer_support" in scenarios
    
    def test_ecommerce_tool_set_loading(self):
        """Test that tool set can be loaded without errors."""
        tool_set = EcommerceToolSet()
        loaded_tools = tool_set.get_loaded_tools()
        assert len(loaded_tools) == 6
        assert "get_order" in loaded_tools
        assert "add_to_cart" in loaded_tools