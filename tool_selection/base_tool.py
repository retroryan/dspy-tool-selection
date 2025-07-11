"""Base classes and models for the tool registry system using Pydantic."""
from typing import List, Any, Dict, Type, Optional, ClassVar, get_origin, get_args
from pydantic import BaseModel, Field, field_validator, create_model, ConfigDict
from abc import ABC, abstractmethod


class ToolArgument(BaseModel):
    """Tool argument with type validation."""
    name: str
    type: Any  # Can be any Python type including generics like List[str]
    description: str
    required: bool = True
    default: Any = None
    constraints: Dict[str, Any] = Field(default_factory=dict)  # For Pydantic field constraints
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Ensure type is a valid Python type."""
        # Check if it's a type or a generic type (like List[str])
        if not (isinstance(v, type) or hasattr(v, '__origin__')):
            raise ValueError(f"Invalid type: {v}")
        return v
    
    def to_schema_type(self) -> str:
        """Convert Python type to schema string representation."""
        # Handle generic types
        origin = get_origin(self.type)
        if origin is list:
            return "array"
        elif origin is dict:
            return "object"
        
        # Handle basic types
        type_map = {
            str: "string",
            int: "integer", 
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object"
        }
        return type_map.get(self.type, "string")


class ToolTestCase(BaseModel):
    """Test case for tool selection."""
    request: str
    expected_tools: List[str]
    description: str


class ToolMetadata(BaseModel):
    """Tool metadata as a Pydantic model."""
    model_config = ConfigDict(frozen=True)  # Make metadata immutable
    
    name: str
    description: str
    category: str
    arguments: Optional[List[ToolArgument]] = Field(default=None)  # Deprecated - use args_model
    args_model: Optional[Type[BaseModel]] = None  # New: Pydantic model for arguments


class BaseTool(BaseModel, ABC):
    """Base class for all tools using Pydantic."""
    model_config = ConfigDict(arbitrary_types_allowed=True)  # Allow arbitrary types for flexibility
    
    # Class-level metadata that must be defined by subclasses
    metadata: ClassVar[ToolMetadata]
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool with given arguments."""
        pass
    
    @classmethod
    @abstractmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        pass
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert to MultiTool schema format."""
        arguments = []
        
        # Use args_model if available (new pattern)
        if self.metadata.args_model:
            # Extract schema from Pydantic model
            schema = self.metadata.args_model.model_json_schema()
            properties = schema.get('properties', {})
            required_fields = schema.get('required', [])
            
            for field_name, field_info in properties.items():
                arg_schema = {
                    "name": field_name,
                    "type": field_info.get('type', 'string'),
                    "description": field_info.get('description', ''),
                    "required": field_name in required_fields
                }
                if 'default' in field_info:
                    arg_schema['default'] = field_info['default']
                arguments.append(arg_schema)
        
        # Fall back to old pattern with arguments list
        elif self.metadata.arguments:
            arguments = [
                {
                    "name": arg.name,
                    "type": arg.to_schema_type(),
                    "description": arg.description,
                    "required": arg.required,
                    **({"default": arg.default} if arg.default is not None else {})
                }
                for arg in self.metadata.arguments
            ]
        
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "arguments": arguments
        }
    
    def validate_and_execute(self, **kwargs) -> Any:
        """Validate arguments before execution."""
        # Use args_model if available (new pattern)
        if self.metadata.args_model:
            # Validate using the provided Pydantic model
            validated_args = self.metadata.args_model(**kwargs)
            # Execute with validated arguments
            return self.execute(**validated_args.model_dump())
        
        # Fall back to old pattern with arguments list
        elif self.metadata.arguments:
            # Build field definitions for create_model
            field_definitions = {}
            for arg in self.metadata.arguments:
                # Build field kwargs including constraints
                field_kwargs = {
                    'description': arg.description,
                    **arg.constraints  # Include any additional constraints
                }
                
                if arg.default is not None:
                    field_kwargs['default'] = arg.default
                elif not arg.required:
                    field_kwargs['default'] = None
                    
                field_definitions[arg.name] = (arg.type, Field(**field_kwargs))
            
            # Create dynamic model using create_model
            DynamicModel = create_model(
                'DynamicArgs',
                **field_definitions
            )
            
            # Validate arguments
            validated_args = DynamicModel(**kwargs)
            
            # Execute with validated arguments
            return self.execute(**validated_args.model_dump())
        
        # No validation if no args defined
        return self.execute(**kwargs)