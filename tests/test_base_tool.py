"""Tests for base_tool.py - base classes and Pydantic models."""
import pytest
from typing import List
from pydantic import ValidationError

from tool_selection.base_tool import (
    BaseTool, ToolArgument, ToolTestCase
)
from typing import ClassVar, Type
from pydantic import BaseModel, Field


class MockTool(BaseTool):
    """Mock tool for testing."""
    NAME: ClassVar[str] = "mock_tool"
    MODULE: ClassVar[str] = "tests.test_base_tool"
    
    class Arguments(BaseModel):
        """Arguments for mock tool."""
        input: str = Field(..., description="Test input")
        count: int = Field(default=1, description="Count value")
    
    description: str = "A mock tool for testing"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, input: str, count: int = 1) -> dict:
        return {"result": f"Processed: {input} x {count}"}
    
    @classmethod
    def get_test_cases(cls):
        return [
            ToolTestCase(
                request="Use the mock tool",
                expected_tools=["mock_tool"],
                description="Mock test"
            )
        ]


class TestBaseTool:
    """Test cases for BaseTool functionality."""
    
    def test_base_tool_implementation(self):
        """Test basic tool implementation."""
        tool = MockTool()
        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"
        assert len(tool.arguments) == 2
        result = tool.execute(input="test", count=3)
        assert result["result"] == "Processed: test x 3"
    
    def test_tool_attributes(self):
        """Test tool attributes."""
        tool = MockTool()
        # Test that NAME is accessible
        assert tool.NAME == "mock_tool"
        assert tool.MODULE == "tests.test_base_tool"
        # Test that description is accessible
        assert tool.description == "A mock tool for testing"
    
    def test_tool_arguments(self):
        """Test tool arguments extraction."""
        tool = MockTool()
        # Arguments should be auto-extracted from args_model
        assert len(tool.arguments) == 2
        
        # Check first argument
        assert tool.arguments[0].name == "input"
        assert tool.arguments[0].type == "string"
        assert tool.arguments[0].required is True
        
        # Check second argument with default
        assert tool.arguments[1].name == "count"
        assert tool.arguments[1].type == "integer"
        assert tool.arguments[1].required is False
        assert tool.arguments[1].default == 1
    
    def test_pydantic_validation(self):
        """Test Pydantic validation in validate_and_execute."""
        tool = MockTool()
        
        # Valid arguments pass validation
        result = tool.validate_and_execute(input="test", count=2)
        assert result["result"] == "Processed: test x 2"
        
        # Invalid type raises ValidationError
        with pytest.raises(ValidationError) as exc_info:
            tool.validate_and_execute(input="test", count="not a number")
        assert "count" in str(exc_info.value)
        
        # Missing required argument raises error
        with pytest.raises(ValidationError) as exc_info:
            tool.validate_and_execute(count=2)  # Missing 'input'
        assert "input" in str(exc_info.value)
        
        # Optional argument with default works
        result = tool.validate_and_execute(input="test")  # count defaults to 1
        assert result["result"] == "Processed: test x 1"
    
    def test_tool_argument_type_safety(self):
        """Test type safety in ToolArgument."""
        tool = MockTool()
        str_arg = tool.arguments[0]
        int_arg = tool.arguments[1]
        
        assert str_arg.type == "string"
        assert int_arg.type == "integer"
    
    def test_tool_argument_validation(self):
        """Test ToolArgument validation."""
        # Valid argument
        arg = ToolArgument(name="test", type="string", description="Test")
        assert arg.type == "string"
        
        # Invalid name (not valid Python identifier)
        with pytest.raises(ValidationError):
            ToolArgument(name="123test", type="string", description="Test")
    
    def test_complex_types(self):
        """Test support for complex types like List[str]."""
        # ToolArgument now uses string type names
        arg = ToolArgument(
            name="items",
            type="array",
            description="List of items"
        )
        
        assert arg.type == "array"
    
    def test_test_cases(self):
        """Test that test cases are properly defined."""
        test_cases = MockTool.get_test_cases()
        assert len(test_cases) == 1
        assert test_cases[0].expected_tools == ["mock_tool"]
        assert test_cases[0].request == "Use the mock tool"


class ComplexTool(BaseTool):
    """Tool with complex argument types for testing."""
    NAME: ClassVar[str] = "complex_tool"
    MODULE: ClassVar[str] = "tests.test_base_tool"
    
    class Arguments(BaseModel):
        """Arguments for complex tool."""
        items: List[str] = Field(..., description="List of items")
        threshold: float = Field(default=0.5, description="Threshold value")
    
    description: str = "Tool with complex types"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, items: List[str], threshold: float = 0.5) -> dict:
        return {"result": f"Processing {len(items)} items with threshold {threshold}"}
    
    @classmethod
    def get_test_cases(cls):
        return []


class TestComplexTypes:
    """Test cases for complex type handling."""
    
    def test_list_type_validation(self):
        """Test validation of List types."""
        tool = ComplexTool()
        
        # Valid list
        result = tool.validate_and_execute(items=["a", "b", "c"], threshold=0.8)
        assert result["result"] == "Processing 3 items with threshold 0.8"
        
        # Invalid type for list
        with pytest.raises(ValidationError):
            tool.validate_and_execute(items="not a list", threshold=0.8)
        
        # List with wrong item type
        with pytest.raises(ValidationError):
            tool.validate_and_execute(items=[1, 2, 3], threshold=0.8)
    
    def test_float_validation(self):
        """Test float type validation."""
        tool = ComplexTool()
        
        # Int should be coerced to float
        result = tool.validate_and_execute(items=["test"], threshold=1)
        assert result["result"] == "Processing 1 items with threshold 1.0"
        
        # Invalid float
        with pytest.raises(ValidationError):
            tool.validate_and_execute(items=["test"], threshold="not a number")