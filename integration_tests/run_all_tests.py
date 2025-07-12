"""
Run all integration tests for the agentic loop implementation.

This script executes all integration tests in the correct order and provides
a comprehensive report of the test results.
"""

import os
import sys
import time
from typing import List, Dict, Any

# Add parent directory to path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integration_tests.test_framework import create_test_runner


def check_environment() -> Dict[str, Any]:
    """Check that the environment is properly configured."""
    print("🔍 Checking Environment Configuration...")
    
    # Load .env file explicitly
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not available, relying on pre-loaded environment")
    
    # Check for required environment variables
    required_vars = []
    
    provider = os.getenv("DSPY_PROVIDER")
    if not provider:
        return {"valid": False, "error": "DSPY_PROVIDER not set in .env"}
    
    if provider == "ollama":
        required_vars.extend(["OLLAMA_BASE_URL", "OLLAMA_MODEL"])
    elif provider == "claude":
        required_vars.extend(["ANTHROPIC_API_KEY", "CLAUDE_MODEL"])
    else:
        return {"valid": False, "error": f"Unknown provider: {provider}"}
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        return {
            "valid": False,
            "error": f"Missing required environment variables: {', '.join(missing_vars)}"
        }
    
    # Check for .env file
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.exists(env_file):
        return {"valid": False, "error": ".env file not found"}
    
    config = {
        "provider": provider,
        "model": os.getenv("OLLAMA_MODEL") if provider == "ollama" else os.getenv("CLAUDE_MODEL"),
        "base_url": os.getenv("OLLAMA_BASE_URL") if provider == "ollama" else "anthropic",
        "debug": os.getenv("DSPY_DEBUG", "false").lower() == "true"
    }
    
    print(f"✅ Environment Configuration Valid:")
    print(f"   Provider: {config['provider']}")
    print(f"   Model: {config['model']}")
    print(f"   Base URL: {config['base_url']}")
    print(f"   Debug: {config['debug']}")
    
    return {"valid": True, "config": config}


def run_test_module(module_name: str, description: str) -> Dict[str, Any]:
    """Run a specific test module."""
    print(f"\n🧪 Running {description}...")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Import and run the test module
        if module_name == "test_full_workflow":
            from integration_tests.test_full_workflow import FullWorkflowTests
            tests = FullWorkflowTests()
            tests.run_all_tests()
            
        elif module_name == "test_real_model_tools":
            from integration_tests.test_real_model_tools import RealModelToolTests
            tests = RealModelToolTests()
            tests.run_all_tests()
            
        else:
            raise ValueError(f"Unknown test module: {module_name}")
        
        duration = time.time() - start_time
        
        # Get results from the test runner
        results = {
            "success": True,
            "duration": duration,
            "total_tests": tests.test_runner.total_tests,
            "passed_tests": tests.test_runner.passed_tests,
            "failed_tests": tests.test_runner.failed_tests,
            "success_rate": (tests.test_runner.passed_tests / tests.test_runner.total_tests) * 100 if tests.test_runner.total_tests > 0 else 0
        }
        
        return results
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ {description} failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "duration": duration,
            "error": str(e),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 1,
            "success_rate": 0
        }


def print_final_summary(results: Dict[str, Dict[str, Any]]) -> None:
    """Print a comprehensive summary of all test results."""
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_duration = 0
    
    for module_name, result in results.items():
        print(f"\n{module_name}:")
        print(f"  Status: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
        print(f"  Duration: {result['duration']:.2f}s")
        print(f"  Tests: {result['total_tests']} total, {result['passed_tests']} passed, {result['failed_tests']} failed")
        print(f"  Success Rate: {result['success_rate']:.1f}%")
        
        if 'error' in result:
            print(f"  Error: {result['error']}")
        
        total_tests += result['total_tests']
        total_passed += result['passed_tests']
        total_failed += result['failed_tests']
        total_duration += result['duration']
    
    print(f"\n" + "=" * 80)
    print("🎯 OVERALL RESULTS")
    print("=" * 80)
    print(f"Total Test Modules: {len(results)}")
    print(f"Total Tests: {total_tests}")
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Overall Success Rate: {(total_passed / total_tests) * 100 if total_tests > 0 else 0:.1f}%")
    print(f"Total Duration: {total_duration:.2f}s")
    
    successful_modules = sum(1 for result in results.values() if result['success'])
    print(f"Successful Modules: {successful_modules}/{len(results)}")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED! The agentic loop implementation is working correctly.")
    else:
        print(f"\n⚠️  {total_failed} TESTS FAILED. Please review the failures above.")
    
    print("\n" + "=" * 80)


def main():
    """Main function to run all integration tests."""
    print("🚀 Starting Comprehensive Integration Tests")
    print("🔬 Testing DSPy Agentic Loop Implementation")
    print("=" * 80)
    
    # Check environment configuration
    env_check = check_environment()
    if not env_check["valid"]:
        print(f"❌ Environment check failed: {env_check['error']}")
        print("\nPlease ensure:")
        print("1. .env file exists in the project root")
        print("2. DSPY_PROVIDER is set (ollama or claude)")
        print("3. Required model configuration is present")
        print("4. If using Ollama, ensure the service is running")
        sys.exit(1)
    
    # Define test modules to run
    test_modules = [
        ("test_full_workflow", "Full Workflow Integration Tests"),
        ("test_real_model_tools", "Real Model and Tools Integration Tests")
    ]
    
    print(f"\n📋 Test Plan:")
    for i, (module, description) in enumerate(test_modules, 1):
        print(f"   {i}. {description}")
    
    # Run all test modules
    results = {}
    
    for module_name, description in test_modules:
        result = run_test_module(module_name, description)
        results[description] = result
    
    # Print comprehensive summary
    print_final_summary(results)
    
    # Exit with appropriate code
    all_passed = all(result['success'] for result in results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()