#!/usr/bin/env python3
"""
Entry point for the Lightroom AI script.
"""

import sys
from lightroom_ai.cli import run_cli


def main():
    """Main entry point for the script."""
    return run_cli()


if __name__ == "__main__":
    sys.exit(main())
