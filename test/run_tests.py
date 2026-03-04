#!/usr/bin/env python
"""
Test Runner for Python Projects
Discovers and runs all tests in the current directory
Supports both unittest and pytest test files
"""

import argparse
import glob
import os
import subprocess
import sys
import time
from pathlib import Path


def run_pytest(test_dir=".", pattern="test_*.py", verbose=False, specific_file=None):
    """
    Run pytest on files matching the pattern in the specified directory
    
    Parameters:
    -----------
    test_dir : str
        Directory containing test files (default: current directory)
    pattern : str
        Pattern to match test files (default: test_*.py)
    verbose : bool
        Whether to use verbose output
    specific_file : str
        Run a specific test file
        
    Returns:
    --------
    bool
        True if all tests pass, False otherwise
    """
    start_time = time.time()
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("pytest is not installed. Install it with: pip install pytest")
        return False
    
    # Find project root (looking for src directory or setup.py)
    project_root = os.getcwd()
    while project_root and not (
        os.path.exists(os.path.join(project_root, "src")) or 
        os.path.exists(os.path.join(project_root, "setup.py"))
    ):
        parent = os.path.dirname(project_root)
        if parent == project_root:  # Reached filesystem root
            break
        project_root = parent
    
    print(f"Using project root: {project_root}")
    
    # Add src to Python path if it exists
    src_path = os.path.join(project_root, "src")
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)
        print(f"Added src directory to Python path: {src_path}")
    
    # Prepare pytest arguments
    pytest_args = ["-v"] if verbose else []
    
    if specific_file:
        print(f"Running tests from file: {specific_file}")
        if not os.path.exists(specific_file):
            print(f"Error: Test file '{specific_file}' does not exist.")
            return False
        test_files = [specific_file]
    else:
        print(f"Discovering tests in directory '{test_dir}' with pattern '{pattern}'...")
        # Find all test files matching the pattern
        test_files = glob.glob(os.path.join(test_dir, pattern))
        if not test_files:
            print(f"No test files matching '{pattern}' found in '{test_dir}'.")
            return False
    
    # Add files to pytest arguments
    pytest_args.extend(test_files)
    
    print(f"Found {len(test_files)} test files")
    for file in test_files:
        print(f"  - {file}")
    
    # Run pytest
    print("\nRunning tests with pytest...")
    # Set up environment variables for the subprocess
    env = os.environ.copy()
    
    # Add src directory to PYTHONPATH if it exists
    src_path = os.path.join(project_root, "src")
    if os.path.exists(src_path):
        pythonpath = env.get("PYTHONPATH", "")
        if pythonpath:
            env["PYTHONPATH"] = f"{src_path}{os.pathsep}{pythonpath}"
        else:
            env["PYTHONPATH"] = src_path
        print(f"Added src directory to PYTHONPATH: {src_path}")
    
    # Use subprocess instead of pytest.main to avoid argument conflicts with pyproject.toml config
    cmd = [sys.executable, "-m", "pytest"] + pytest_args
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=not verbose, env=env)
    
    if verbose:
        # Output already shown
        pass
    elif result.returncode != 0:
        print("Tests failed. Showing output:")
        print(result.stdout.decode('utf-8'))
        print(result.stderr.decode('utf-8'))
    
    # Report results
    elapsed_time = time.time() - start_time
    print(f"\nTest run completed in {elapsed_time:.2f} seconds")
    
    return result.returncode == 0


def main():
    """Main entry point for the test runner"""
    parser = argparse.ArgumentParser(description="Run tests for Python projects")
    parser.add_argument("-d", "--directory", default=".", 
                      help="Directory containing test files (default: current directory)")
    parser.add_argument("-p", "--pattern", default="test_*.py", 
                      help="Pattern to match test files (default: test_*.py)")
    parser.add_argument("-v", "--verbose", action="store_true", 
                      help="Increase verbosity")
    parser.add_argument("-f", "--file", help="Run a specific test file")
    args = parser.parse_args()
    
    success = run_pytest(
        test_dir=args.directory, 
        pattern=args.pattern, 
        verbose=args.verbose,
        specific_file=args.file
    )
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()