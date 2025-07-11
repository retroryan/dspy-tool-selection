"""Add to cart tool implementation."""
from typing import List
from pydantic import BaseModel, Field

from tool_selection.base_tool import BaseTool, ToolTestCase, ToolMetadata
from tool_selection.registry import register_tool


@register_tool
class AddToCartTool(BaseTool):
    """Tool for adding products to shopping cart."""
    
    class Arguments(BaseModel):
        """Arguments for adding to cart."""
        product_id: str = Field(..., description="Product ID")
        quantity: int = Field(default=1, ge=1, description="Quantity to add")
    
    metadata = ToolMetadata(
        name="add_to_cart",
        description="Add a product to the shopping cart",
        category="ecommerce",
        args_model=Arguments
    )
    
    def execute(self, product_id: str, quantity: int = 1) -> dict:
        """Execute the tool to add product to cart."""
        return {
            "cart_total": 2,
            "added": product_id,
            "quantity": quantity,
            "status": "success"
        }
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Add product PROD123 to my cart",
                expected_tools=["add_to_cart"],
                description="Add single product"
            ),
            ToolTestCase(
                request="Add 3 units of SKU456 to cart",
                expected_tools=["add_to_cart"],
                description="Add multiple quantities"
            )
        ]