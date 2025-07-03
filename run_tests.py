#!/usr/bin/env python3
"""Simple test runner for claif_cla tests."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run pytest with appropriate configuration."""
    # Get the directory containing this script
    test_dir = Path(__file__).parent

    # Basic pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",  # Verbose
        "--tb=short",  # Short traceback
        "tests/",  # Test directory
    ]

    # Add coverage if requested
    if "--coverage" in sys.argv:
        cmd.extend(
            [
                "--cov=claif_cla",
                "--cov-report=term-missing",
                "--cov-report=html",
            ]
        )

    # Add specific test file if provided
    for arg in sys.argv[1:]:
        if arg.startswith("tests/") or arg.endswith(".py"):
            cmd.append(arg)

    # Run pytest
    result = subprocess.run(cmd, check=False, cwd=test_dir)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
