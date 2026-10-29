#!/usr/bin/env python3
"""Portable entry point. Only the explicit probe subcommand contacts an endpoint."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from responses_contract.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
