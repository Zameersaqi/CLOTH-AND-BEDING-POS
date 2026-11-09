"""
Automated Test Runner for Arooj POS
Uses Python's standard library unittest - requires zero external dependencies to execute!
"""

import sys
import unittest
import time
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def run_all_tests():
    print("\n=======================================================")
    print(" AROOJ CLOTH AND BEDSHEET PARDA - AUTOMATED TEST SUITE")
    print("=======================================================")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Discover and add test modules
    tests_dir = Path(__file__).parent
    discovered = loader.discover(start_dir=str(tests_dir), pattern="test_*.py")
    suite.addTests(discovered)

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    duration = time.time() - start_time

    print("\n-------------------------------------------------------")
    print(f"Total Tests Run   : {result.testsRun}")
    print(f"Passed            : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed            : {len(result.failures)}")
    print(f"Errors            : {len(result.errors)}")
    print(f"Time Taken        : {duration:.3f} seconds")
    print("-------------------------------------------------------")

    if result.wasSuccessful():
        print(">>> ALL AUTOMATED TESTS PASSED SUCCESSFULLY! <<<\n")
        return 0
    else:
        print(">>> TEST FAILURES DETECTED! <<<\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
