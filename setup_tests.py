#!/usr/bin/env python
"""Setup script to configure test environment for claif_cla."""

import subprocess
import sys
from pathlib import Path


def setup_test_environment():
    """Set up the test environment with all necessary dependencies."""
    print("Setting up claif_cla test environment...")
    
    # Get the project root
    project_root = Path(__file__).parent
    
    # Install test dependencies
    print("Installing test dependencies...")
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "pytest>=8.3.4",
        "pytest-cov>=6.0.0",
        "pytest-asyncio>=0.26.0",
        "pytest-mock>=3.14.0",
        "-e", str(project_root)  # Install claif_cla in editable mode
    ], check=True)
    
    # Create test directories
    test_dir = project_root / "tests"
    test_dir.mkdir(exist_ok=True)
    
    print("Test environment setup complete!")
    print(f"Run tests with: hatch test")
    

if __name__ == "__main__":
    setup_test_environment()