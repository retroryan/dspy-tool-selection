"""Search products tool implementation using the unified base class."""
from typing import List, Optional, ClassVar, Dict, Any, Type
from pydantic import BaseModel, Field

from tool_selection.base_tool import BaseTool, ToolTestCase


class SearchProductsTool(BaseTool):
    """Tool for searching products in the catalog."""
    
    NAME: ClassVar[str] = "search_products"
    MODULE: ClassVar[str] = "tools.ecommerce.search_products"
    
    class Arguments(BaseModel):
        """Arguments for searching products."""
        query: str = Field(..., description="Search query")
        category: Optional[str] = Field(default=None, description="Product category")
        max_price: Optional[float] = Field(default=None, ge=0, description="Maximum price")
    
    # Tool definition as instance attributes
    description: str = "Search for products in the catalog"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, query: str, category: str = None, max_price: float = None) -> dict:
        """Execute the tool to search products."""
        filters = []
        if category:
            filters.append(f"category: {category}")
        if max_price is not None:
            filters.append(f"under ${max_price}")
        
        filter_str = f" ({', '.join(filters)})" if filters else ""
        
        return {
            "products": f"Found 10 products matching '{query}'{filter_str}",
            "count": 10,
            "query": query,
            "filters": {
                "category": category,
                "max_price": max_price
            }
        }
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Search for laptops under $1000",
                expected_tools=["search_products"],
                description="Search with price filter"
            ),
            ToolTestCase(
                request="Find electronics in the catalog",
                expected_tools=["search_products"],
                description="Search by category"
            ),
            ToolTestCase(
                request="Look for wireless headphones",
                expected_tools=["search_products"],
                description="General product search"
            )
        ]