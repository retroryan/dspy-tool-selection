"""Tests for registry.py - tool registry with type-safe operations."""
import pytest
from typing import List, Type
from pydantic import ValidationError

from tool_selection.registry import registry, register_tool
from tool_selection.base_tool import BaseTool, ToolTestCase, ToolArgument
from typing import ClassVar, Dict, Any
from pydantic import BaseModel, Field


# Create test tools
class TestTool1(BaseTool):
    NAME: ClassVar[str] = "test_tool_1"
    MODULE: ClassVar[str] = "tests.test_registry"
    
    description: str = "First test tool"
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        return {"result": "Tool 1 executed"}
    
    @classmethod
    def get_test_cases(cls):
        return [ToolTestCase(request="Use tool 1", expected_tools=["test_tool_1"], description="Test 1")]


class TestTool2(BaseTool):
    NAME: ClassVar[str] = "test_tool_2"
    MODULE: ClassVar[str] = "tests.test_registry"
    
    class Arguments(BaseModel):
        value: int = Field(default=42, description="Test value")
    
    description: str = "Second test tool"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, value: int = 42) -> Dict[str, Any]:
        return {"result": f"Tool 2 executed with {value}"}
    
    @classmethod
    def get_test_cases(cls):
        return [ToolTestCase(request="Use tool 2", expected_tools=["test_tool_2"], description="Test 2")]


class DifferentCategoryTool(BaseTool):
    NAME: ClassVar[str] = "other_tool"
    MODULE: ClassVar[str] = "tests.test_registry"
    
    description: str = "Tool in different category"
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        return {"result": "Other tool executed"}
    
    @classmethod
    def get_test_cases(cls):
        return []


class TestToolRegistry:
    """Test cases for ToolRegistry functionality."""
    
    def setup_method(self):
        """Clear registry before each test."""
        # Clear the global registry before each test
        registry.clear()
    
    def test_tool_registration(self):
        """Test basic tool registration."""
        registry.register(TestTool1)
        registry.register(TestTool2)
        
        all_tools = registry.get_all_tools()
        assert "test_tool_1" in all_tools
        assert "test_tool_2" in all_tools
        assert len(all_tools) >= 2
    
    def test_get_tool(self):
        """Test getting tools by name."""
        registry.register(TestTool1)
        registry.register(TestTool2)
        
        tool1 = registry.get_tool("test_tool_1")
        assert tool1 is not None
        assert tool1.name == "test_tool_1"
        result = tool1.execute()
        assert result["result"] == "Tool 1 executed"
        
        tool2 = registry.get_tool("test_tool_2")
        assert tool2 is not None
        assert tool2.name == "test_tool_2"
    
    def test_get_tool_instance(self):
        """Test getting tool instances."""
        registry.register(TestTool1)
        
        # Should return the tool when it exists
        tool = registry.get_tool("test_tool_1")
        assert tool is not None
        assert isinstance(tool, TestTool1)
        
        # Should return None when tool doesn't exist
        tool = registry.get_tool("nonexistent_tool")
        assert tool is None
    
    def test_get_all_tools(self):
        """Test getting all registered tools."""
        registry.register(TestTool1)
        registry.register(TestTool2)
        registry.register(DifferentCategoryTool)
        
        all_tools = registry.get_all_tools()
        assert "test_tool_1" in all_tools
        assert "test_tool_2" in all_tools
        assert "other_tool" in all_tools
        assert len(all_tools) >= 3
    
    def test_get_all_test_cases(self):
        """Test aggregating test cases from all tools."""
        registry.register(TestTool1)
        registry.register(TestTool2)
        registry.register(DifferentCategoryTool)
        
        test_cases = registry.get_all_test_cases()
        assert len(test_cases) >= 2
        assert any(tc.description == "Test 1" for tc in test_cases)
        assert any(tc.description == "Test 2" for tc in test_cases)
    
    def test_nonexistent_tool(self):
        """Test getting non-existent tool."""
        tool = registry.get_tool("nonexistent")
        assert tool is None
    
    def test_execute_tool_with_validation(self):
        """Test executing tools with automatic validation."""
        registry.register(TestTool2)
        
        tool = registry.get_tool("test_tool_2")
        
        # Valid execution
        result = tool.validate_and_execute(value=100)
        assert result["result"] == "Tool 2 executed with 100"
        
        # Default value works
        result = tool.validate_and_execute()
        assert result["result"] == "Tool 2 executed with 42"
        
        # Invalid type raises error
        with pytest.raises(ValidationError):
            tool.validate_and_execute(value="not a number")
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        registry.register(TestTool1)
        registry.register(TestTool2)
        
        all_tools = registry.get_all_tools()
        assert len(all_tools) >= 2
        
        registry.clear()
        
        all_tools = registry.get_all_tools()
        assert len(all_tools) == 0
        assert registry.get_tool("test_tool_1") is None


class TestRegistryDecorator:
    """Test the @register_tool decorator."""
    
    def test_decorator_registration(self):
        """Test that decorator properly registers tools."""
        # Clear registry first
        registry.clear()
        
        @register_tool
        class DecoratedTool(BaseTool):
            NAME: ClassVar[str] = "decorated_tool"
            MODULE: ClassVar[str] = "tests.test_registry"
            
            description: str = "Tool registered via decorator"
            
            def execute(self, **kwargs) -> Dict[str, Any]:
                return {"result": "Decorated tool executed"}
            
            @classmethod
            def get_test_cases(cls):
                return []
        
        # Tool should be registered
        all_tools = registry.get_all_tools()
        assert "decorated_tool" in all_tools
        tool = registry.get_tool("decorated_tool")
        assert tool is not None
        result = tool.execute()
        assert result["result"] == "Decorated tool executed"


class TestComplexToolValidation:
    """Test validation with complex argument types."""
    
    def test_tool_with_list_arguments(self):
        """Test tool with List type arguments."""
        # Clear registry first
        registry.clear()
        
        class ListTool(BaseTool):
            NAME: ClassVar[str] = "list_tool"
            MODULE: ClassVar[str] = "tests.test_registry"
            
            class Arguments(BaseModel):
                items: List[str] = Field(..., description="List of items")
            
            description: str = "Tool with list arguments"
            args_model: Type[BaseModel] = Arguments
            
            def execute(self, items: List[str]) -> Dict[str, Any]:
                return {"result": f"Processed {len(items)} items"}
            
            @classmethod
            def get_test_cases(cls):
                return []
        
        registry.register(ListTool)
        tool = registry.get_tool("list_tool")
        
        # Valid list
        result = tool.validate_and_execute(items=["a", "b", "c"])
        assert result["result"] == "Processed 3 items"
        
        # Invalid type
        with pytest.raises(ValidationError):
            tool.validate_and_execute(items="not a list")
        
        # Wrong item type
        with pytest.raises(ValidationError):
            tool.validate_and_execute(items=[1, 2, 3])