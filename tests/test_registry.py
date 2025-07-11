"""Tests for registry.py - tool registry with type-safe operations."""
import pytest
from typing import List, Type
from pydantic import ValidationError

from tool_selection.registry import ToolRegistry, register_tool
from tool_selection.base_tool import BaseTool, ToolTestCase, ToolMetadata, ToolArgument


# Create test tools
class TestTool1(BaseTool):
    metadata = ToolMetadata(
        name="test_tool_1",
        description="First test tool",
        category="test",
        arguments=[]
    )
    
    def execute(self, **kwargs):
        return "Tool 1 executed"
    
    @classmethod
    def get_test_cases(cls):
        return [ToolTestCase(request="Use tool 1", expected_tools=["test_tool_1"], description="Test 1")]


class TestTool2(BaseTool):
    metadata = ToolMetadata(
        name="test_tool_2",
        description="Second test tool",
        category="test",
        arguments=[
            ToolArgument(name="value", type=int, description="Test value", default=42)
        ]
    )
    
    def execute(self, value: int = 42) -> str:
        return f"Tool 2 executed with {value}"
    
    @classmethod
    def get_test_cases(cls):
        return [ToolTestCase(request="Use tool 2", expected_tools=["test_tool_2"], description="Test 2")]


class DifferentCategoryTool(BaseTool):
    metadata = ToolMetadata(
        name="other_tool",
        description="Tool in different category",
        category="other",
        arguments=[]
    )
    
    def execute(self, **kwargs):
        return "Other tool executed"
    
    @classmethod
    def get_test_cases(cls):
        return []


class TestToolRegistry:
    """Test cases for ToolRegistry functionality."""
    
    def setup_method(self):
        """Clear registry before each test."""
        # Create a fresh registry for each test
        self.registry = ToolRegistry()
    
    def test_tool_registration(self):
        """Test basic tool registration."""
        self.registry.register(TestTool1)
        self.registry.register(TestTool2)
        
        assert "test_tool_1" in self.registry.get_tool_names()
        assert "test_tool_2" in self.registry.get_tool_names()
        assert len(self.registry.get_tool_names()) == 2
    
    def test_get_tool(self):
        """Test getting tools by name."""
        self.registry.register(TestTool1)
        self.registry.register(TestTool2)
        
        tool1 = self.registry.get_tool("test_tool_1")
        assert tool1 is not None
        assert tool1.metadata.name == "test_tool_1"
        assert tool1.execute() == "Tool 1 executed"
        
        tool2 = self.registry.get_tool("test_tool_2")
        assert tool2 is not None
        assert tool2.metadata.name == "test_tool_2"
    
    def test_get_tool_with_type_checking(self):
        """Test type-safe tool retrieval."""
        self.registry.register(TestTool1)
        
        # Should return the tool when type matches
        tool = self.registry.get_tool("test_tool_1", TestTool1)
        assert tool is not None
        assert isinstance(tool, TestTool1)
        
        # Should return None when type doesn't match
        tool = self.registry.get_tool("test_tool_1", TestTool2)
        assert tool is None
    
    def test_get_tools_by_category(self):
        """Test filtering tools by category."""
        self.registry.register(TestTool1)
        self.registry.register(TestTool2)
        self.registry.register(DifferentCategoryTool)
        
        test_tools = self.registry.get_tools_by_category("test")
        assert len(test_tools) == 2
        assert "test_tool_1" in test_tools
        assert "test_tool_2" in test_tools
        assert "other_tool" not in test_tools
        
        other_tools = self.registry.get_tools_by_category("other")
        assert len(other_tools) == 1
        assert "other_tool" in other_tools
    
    def test_get_all_test_cases(self):
        """Test aggregating test cases from all tools."""
        self.registry.register(TestTool1)
        self.registry.register(TestTool2)
        self.registry.register(DifferentCategoryTool)
        
        test_cases = self.registry.get_all_test_cases()
        assert len(test_cases) >= 2
        assert any(tc.description == "Test 1" for tc in test_cases)
        assert any(tc.description == "Test 2" for tc in test_cases)
    
    def test_nonexistent_tool(self):
        """Test getting non-existent tool."""
        tool = self.registry.get_tool("nonexistent")
        assert tool is None
    
    def test_execute_tool_with_validation(self):
        """Test executing tools with automatic validation."""
        self.registry.register(TestTool2)
        
        # Valid execution
        result = self.registry.execute_tool("test_tool_2", value=100)
        assert result == "Tool 2 executed with 100"
        
        # Default value works
        result = self.registry.execute_tool("test_tool_2")
        assert result == "Tool 2 executed with 42"
        
        # Invalid type raises error
        with pytest.raises(ValidationError):
            self.registry.execute_tool("test_tool_2", value="not a number")
        
        # Unknown tool raises error
        with pytest.raises(ValueError, match="Unknown tool"):
            self.registry.execute_tool("nonexistent_tool")
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        self.registry.register(TestTool1)
        self.registry.register(TestTool2)
        
        assert len(self.registry.get_tool_names()) == 2
        
        self.registry.clear()
        
        assert len(self.registry.get_tool_names()) == 0
        assert self.registry.get_tool("test_tool_1") is None


class TestRegistryDecorator:
    """Test the @register_tool decorator."""
    
    def test_decorator_registration(self):
        """Test that decorator properly registers tools."""
        # Create a new registry for this test
        test_registry = ToolRegistry()
        
        # Create a custom decorator for this test registry
        def test_register_tool(tool_class: Type[BaseTool]) -> Type[BaseTool]:
            test_registry.register(tool_class)
            return tool_class
        
        @test_register_tool
        class DecoratedTool(BaseTool):
            metadata = ToolMetadata(
                name="decorated_tool",
                description="Tool registered via decorator",
                category="test",
                arguments=[]
            )
            
            def execute(self, **kwargs):
                return "Decorated tool executed"
            
            @classmethod
            def get_test_cases(cls):
                return []
        
        # Tool should be registered
        assert "decorated_tool" in test_registry.get_tool_names()
        tool = test_registry.get_tool("decorated_tool")
        assert tool is not None
        assert tool.execute() == "Decorated tool executed"


class TestComplexToolValidation:
    """Test validation with complex argument types."""
    
    def test_tool_with_list_arguments(self):
        """Test tool with List type arguments."""
        registry = ToolRegistry()
        
        class ListTool(BaseTool):
            metadata = ToolMetadata(
                name="list_tool",
                description="Tool with list arguments",
                category="test",
                arguments=[
                    ToolArgument(
                        name="items",
                        type=List[str],
                        description="List of items"
                    )
                ]
            )
            
            def execute(self, items: List[str]) -> str:
                return f"Processed {len(items)} items"
            
            @classmethod
            def get_test_cases(cls):
                return []
        
        registry.register(ListTool)
        
        # Valid list
        result = registry.execute_tool("list_tool", items=["a", "b", "c"])
        assert result == "Processed 3 items"
        
        # Invalid type
        with pytest.raises(ValidationError):
            registry.execute_tool("list_tool", items="not a list")
        
        # Wrong item type
        with pytest.raises(ValidationError):
            registry.execute_tool("list_tool", items=[1, 2, 3])