"""
Simple test script that runs a subset of tests to verify the environment is working.
"""

import os
import sys
import pytest

if __name__ == "__main__":
    print("Running basic tests to validate the environment...")
    # Add the current directory to sys.path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Run a subset of tests that are expected to pass
    test_files = [
        'tests/test_app.py', 
        'tests/test_ping.py', 
        'tests/test_with_mocks.py',
        'tests/simple_test.py'
    ]
    
    exit_code = pytest.main(['-v'] + test_files)
    
    if exit_code == 0:
        print("\n✅ Basic tests passed successfully!")
        print("The testing environment is properly set up.")
    else:
        print("\n❌ Some tests failed.")
        print("Check the output above for details.")
    
    sys.exit(exit_code)