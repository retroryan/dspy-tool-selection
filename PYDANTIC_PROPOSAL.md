# Proposal: Pydantic-Native Tool Definition

This document refines the original proposal in `TOOLS_LIBRARY.md` to leverage Pydantic more deeply for defining tools, as requested. This approach enhances type safety and developer experience without introducing the architectural complexity of dependency injection or custom schema builders.

### Core Idea: `BaseTool` as a Pydantic Model

Instead of being a standard Python class, `BaseTool` itself becomes a `pydantic.BaseModel`. More importantly, a tool's arguments are defined in a nested Pydantic model, allowing for automatic validation and schema generation.

---

### Revised Core Components

#### 1. Base Tool using Pydantic

The `BaseTool` is now a Pydantic model. The arguments for the tool are defined in a nested `Arguments` class, using standard Python types.

```python
# tool_selection/base_tool.py
from abc import ABC, abstractmethod
from typing import List, Any, Dict, Type
from pydantic import BaseModel, Field

class TestCase(BaseModel):
    request: str
    expected_tools: List[str]
    description: str

class BaseTool(BaseModel, ABC):
    """Base class for all tools, now based on Pydantic."""
    
    name: str = Field(..., description="The unique name of the tool.")
    description: str = Field(..., description="A brief description of what the tool does.")
    category: str = Field("general", description="The category the tool belongs to.")
    
    class Arguments(BaseModel):
        """A nested model to define the arguments for the tool."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool with validated arguments."""
        pass

    @classmethod
    @abstractmethod
    def get_test_cases(cls) -> List[TestCase]:
        """Return test cases for this tool."""
        pass

    def to_schema(self) -> Dict[str, Any]:
        """
        Convert the tool's arguments into the required schema format.
        This leverages Pydantic's built-in schema generation.
        """
        # Generate a standard JSON Schema from the Arguments model
        argument_schema = self.Arguments.schema()
        
        # Map JSON Schema types to the simple string types required
        type_mapping = {
            "integer": "integer",
            "string": "string",
            "number": "float",
            "boolean": "boolean",
        }

        arguments = []
        for prop_name, prop_details in argument_schema.get("properties", {}).items():
            arg_type = prop_details.get("type", "string")
            arguments.append({
                "name": prop_name,
                "type": type_mapping.get(arg_type, "string"),
                "description": prop_details.get("description", ""),
                "required": prop_name in argument_schema.get("required", []),
            })

        return {
            "name": self.name,
            "description": self.description,
            "arguments": arguments,
        }

    class Config:
        # Allows the class to be used as a type
        arbitrary_types_allowed = True
```

#### 2. Tool Implementation Example (Pydantic-native)

Defining a tool is now cleaner and safer. Arguments are declared with Python types, and `Field` can be used for descriptions and validation.

```python
# tools/treasure_hunt/give_hint.py
from typing import List
from pydantic import Field
from tool_selection.base_tool import BaseTool, TestCase
from tool_selection.registry import register_tool

@register_tool
class GiveHintTool(BaseTool):
    name: str = "give_hint"
    description: str = "Give a progressive hint about the treasure location"
    category: str = "treasure_hunt"

    # Define arguments using a nested Pydantic model with real types
    class Arguments(BaseTool.Arguments):
        attempt_number: int = Field(
            ..., 
            description="Which hint to give (1-3)",
            ge=1, # Example of built-in validation
            le=3,
        )

    def execute(self, attempt_number: int) -> str:
        # Pydantic has already validated that attempt_number is an int between 1 and 3
        hints = {
            1: "The treasure is hidden where knowledge grows...",
            2: "Look for the building with many books...",
            3: "Check behind the library!",
        }
        return hints.get(attempt_number, "No more hints available!")

    @classmethod
    def get_test_cases(cls) -> List[TestCase]:
        return [
            TestCase(
                request="I need a hint about the treasure",
                expected_tools=["give_hint"],
                description="Basic hint request"
            )
        ]
```

### How This Improves the Design

1.  **Superior Type Safety**: By using `attempt_number: int`, we replace `type: "integer"`. This allows static analysis tools (like Mypy) and IDEs to catch errors before the code is even run.
2.  **Automatic Validation**: Pydantic automatically validates incoming arguments. If a non-integer is passed to `GiveHintTool`, it will raise a validation error immediately, making the `execute` method more robust. You can add complex validation rules (e.g., `ge=1` for "greater than or equal to 1") with minimal effort.
3.  **Simplified and More Expressive**: The tool definition is more declarative and easier to read. It looks like a standard Pydantic model, a very common pattern in modern Python. There's no need to manually instantiate `ToolArgument` objects.
4.  **Self-Documenting**: The Pydantic `Arguments` model serves as clear documentation for the tool's inputs. The `to_schema` method leverages this automatically.

### Conclusion

Adopting this Pydantic-native approach is a significant **improvement** that does not add undue complexity. It directly addresses the goal of using Python's type system effectively, making the framework more robust, maintainable, and pleasant for developers to work with. It's a pragmatic step forward that delivers immediate benefits.
