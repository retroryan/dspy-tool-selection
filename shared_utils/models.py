"""Pydantic models for test results and evaluation data."""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Import ToolTestCase to use instead of local TestCase
from tool_selection.base_tool import ToolTestCase



class ToolSelectionEvaluation(BaseModel):
    """Evaluation metrics for a tool selection."""
    precision: float = Field(ge=0, le=1, description="Precision score")
    recall: float = Field(ge=0, le=1, description="Recall score")
    f1_score: float = Field(ge=0, le=1, description="F1 score")
    is_perfect_match: bool = Field(description="Whether selection perfectly matched expected")


class TestResult(BaseModel):
    """Result of a single test case execution."""
    test_case: ToolTestCase = Field(description="The test case that was executed")
    actual_tools: List[str] = Field(description="Tools actually selected")
    reasoning: str = Field(description="LLM's reasoning for the selection")
    evaluation: ToolSelectionEvaluation = Field(description="Evaluation metrics")
    execution_results: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        description="Results from executing the selected tools"
    )
    error: Optional[str] = Field(default=None, description="Error message if test failed")
    duration_ms: Optional[float] = Field(default=None, description="Test execution time in milliseconds")


class TestSummary(BaseModel):
    """Summary of test suite execution."""
    model: str = Field(description="Model used for testing")
    timestamp: datetime = Field(default_factory=datetime.now, description="When tests were run")
    total_tests: int = Field(description="Total number of tests executed")
    passed_tests: int = Field(description="Number of tests that passed")
    perfect_matches: int = Field(description="Number of perfect matches")
    avg_precision: float = Field(ge=0, le=1, description="Average precision across all tests")
    avg_recall: float = Field(ge=0, le=1, description="Average recall across all tests")
    avg_f1_score: float = Field(ge=0, le=1, description="Average F1 score across all tests")
    total_duration_seconds: float = Field(description="Total execution time in seconds")
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        return (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0.0
    
    @property
    def perfect_match_rate(self) -> float:
        """Calculate the perfect match rate as a percentage."""
        return (self.perfect_matches / self.total_tests * 100) if self.total_tests > 0 else 0.0


class ModelComparisonResult(BaseModel):
    """Result of comparing multiple models."""
    models: List[str] = Field(description="Models that were compared")
    summaries: Dict[str, TestSummary] = Field(description="Summary for each model")
    detailed_results: Dict[str, List[TestResult]] = Field(
        description="Detailed results for each model"
    )
    comparison_timestamp: datetime = Field(
        default_factory=datetime.now, 
        description="When comparison was run"
    )