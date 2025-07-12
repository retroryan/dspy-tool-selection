"""
Simple test framework for integration tests.

This module provides a basic testing framework without pytest complexity.
"""

import time
import traceback
from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_name: str
    passed: bool
    duration: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class TestRunner:
    """Simple test runner for integration tests."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def run_test(self, test_func: Callable, test_name: str) -> TestResult:
        """Run a single test function."""
        if self.verbose:
            print(f"🔄 Running {test_name}...")
        
        start_time = time.time()
        
        try:
            # Execute the test function
            result = test_func()
            duration = time.time() - start_time
            
            # Check if test returned details
            details = None
            if isinstance(result, dict):
                details = result
            
            test_result = TestResult(
                test_name=test_name,
                passed=True,
                duration=duration,
                details=details
            )
            
            if self.verbose:
                print(f"✅ {test_name} PASSED ({duration:.2f}s)")
                if details:
                    print(f"   Details: {details}")
            
            self.passed_tests += 1
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            test_result = TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                error=error_msg
            )
            
            if self.verbose:
                print(f"❌ {test_name} FAILED ({duration:.2f}s)")
                print(f"   Error: {error_msg}")
                if self.verbose:
                    print(f"   Traceback:\n{traceback.format_exc()}")
            
            self.failed_tests += 1
        
        self.total_tests += 1
        self.results.append(test_result)
        return test_result
    
    def run_test_suite(self, test_functions: List[tuple]) -> None:
        """Run a list of test functions."""
        print(f"🧪 Running {len(test_functions)} integration tests...")
        print("=" * 60)
        
        for test_func, test_name in test_functions:
            self.run_test(test_func, test_name)
        
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print test execution summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        print(f"Total tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        
        if self.failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.test_name}: {result.error}")
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")
        
        total_duration = sum(result.duration for result in self.results)
        print(f"Total duration: {total_duration:.2f}s")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.failed_tests} TESTS FAILED")
    
    def assert_true(self, condition: bool, message: str = "") -> None:
        """Assert that a condition is true."""
        if not condition:
            raise AssertionError(message or "Condition was not true")
    
    def assert_equal(self, actual: Any, expected: Any, message: str = "") -> None:
        """Assert that two values are equal."""
        if actual != expected:
            raise AssertionError(
                message or f"Expected {expected}, but got {actual}"
            )
    
    def assert_not_none(self, value: Any, message: str = "") -> None:
        """Assert that a value is not None."""
        if value is None:
            raise AssertionError(message or "Value was None")
    
    def assert_contains(self, container: Any, item: Any, message: str = "") -> None:
        """Assert that a container contains an item."""
        if item not in container:
            raise AssertionError(
                message or f"Item {item} not found in {container}"
            )
    
    def assert_greater_than(self, value: float, threshold: float, message: str = "") -> None:
        """Assert that a value is greater than a threshold."""
        if value <= threshold:
            raise AssertionError(
                message or f"Value {value} is not greater than {threshold}"
            )


def create_test_runner(verbose: bool = True) -> TestRunner:
    """Create a new test runner instance."""
    return TestRunner(verbose=verbose)