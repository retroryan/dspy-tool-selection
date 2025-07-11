"""Tests for base_tool.py - base classes and Pydantic models."""
import pytest
from typing import List
from pydantic import ValidationError

from tool_selection.base_tool import (
    BaseTool, ToolArgument, ToolTestCase, ToolMetadata
)


class MockTool(BaseTool):
    """Mock tool for testing."""
    metadata = ToolMetadata(
        name="mock_tool",
        description="A mock tool for testing",
        category="test",
        arguments=[
            ToolArgument(name="input", type=str, description="Test input"),
            ToolArgument(name="count", type=int, description="Count value", required=False, default=1)
        ]
    )
    
    def execute(self, input: str, count: int = 1) -> str:
        return f"Processed: {input} x {count}"
    
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
        assert tool.metadata.name == "mock_tool"
        assert tool.metadata.category == "test"
        assert len(tool.metadata.arguments) == 2
        assert tool.execute(input="test", count=3) == "Processed: test x 3"
    
    def test_tool_metadata_immutable(self):
        """Test that tool metadata is immutable."""
        # Try to create a new metadata with same values (should work)
        metadata = ToolMetadata(
            name="test",
            description="Test",
            category="test"
        )
        
        # Metadata fields should not be modifiable after creation
        with pytest.raises(ValidationError):  # Frozen model raises ValidationError in Pydantic v2
            metadata.name = "new_name"
    
    def test_tool_schema_generation(self):
        """Test schema generation for LLM compatibility."""
        tool = MockTool()
        schema = tool.to_schema()
        
        assert schema["name"] == "mock_tool"
        assert schema["description"] == "A mock tool for testing"
        assert len(schema["arguments"]) == 2
        
        # Check first argument
        assert schema["arguments"][0]["name"] == "input"
        assert schema["arguments"][0]["type"] == "string"
        assert schema["arguments"][0]["required"] is True
        
        # Check second argument with default
        assert schema["arguments"][1]["name"] == "count"
        assert schema["arguments"][1]["type"] == "integer"
        assert schema["arguments"][1]["required"] is False
        assert schema["arguments"][1]["default"] == 1
    
    def test_pydantic_validation(self):
        """Test Pydantic validation in validate_and_execute."""
        tool = MockTool()
        
        # Valid arguments pass validation
        result = tool.validate_and_execute(input="test", count=2)
        assert result == "Processed: test x 2"
        
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
        assert result == "Processed: test x 1"
    
    def test_tool_argument_type_safety(self):
        """Test type safety in ToolArgument."""
        tool = MockTool()
        str_arg = tool.metadata.arguments[0]
        int_arg = tool.metadata.arguments[1]
        
        assert str_arg.type == str
        assert str_arg.to_schema_type() == "string"
        assert int_arg.type == int
        assert int_arg.to_schema_type() == "integer"
    
    def test_tool_argument_validation(self):
        """Test ToolArgument type validation."""
        # Valid type
        arg = ToolArgument(name="test", type=str, description="Test")
        assert arg.type == str
        
        # Invalid type should raise error
        with pytest.raises(ValidationError):
            ToolArgument(name="test", type="not a type", description="Test")
    
    def test_complex_types(self):
        """Test support for complex types like List[str]."""
        from typing import List as ListType, get_origin
        
        arg = ToolArgument(
            name="items",
            type=ListType[str],
            description="List of items"
        )
        
        assert arg.to_schema_type() == "array"
        assert get_origin(arg.type) is list
    
    def test_test_cases(self):
        """Test that test cases are properly defined."""
        test_cases = MockTool.get_test_cases()
        assert len(test_cases) == 1
        assert test_cases[0].expected_tools == ["mock_tool"]
        assert test_cases[0].request == "Use the mock tool"


class ComplexTool(BaseTool):
    """Tool with complex argument types for testing."""
    metadata = ToolMetadata(
        name="complex_tool",
        description="Tool with complex types",
        category="test",
        arguments=[
            ToolArgument(
                name="items",
                type=List[str],
                description="List of items"
            ),
            ToolArgument(
                name="threshold",
                type=float,
                description="Threshold value",
                required=False,
                default=0.5
            )
        ]
    )
    
    def execute(self, items: List[str], threshold: float = 0.5) -> str:
        return f"Processing {len(items)} items with threshold {threshold}"
    
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
        assert result == "Processing 3 items with threshold 0.8"
        
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
        assert result == "Processing 1 items with threshold 1.0"
        
        # Invalid float
        with pytest.raises(ValidationError):
            tool.validate_and_execute(items=["test"], threshold="not a number")