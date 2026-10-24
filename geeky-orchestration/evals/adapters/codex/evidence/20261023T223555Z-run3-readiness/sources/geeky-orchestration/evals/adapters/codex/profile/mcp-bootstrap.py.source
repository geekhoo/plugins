"""Start the exported MCP server with the venv's base Python inside MXC.

The adapter supplies absolute paths; no package installation or network is needed.
"""
import argparse
from pathlib import Path
import runpy
import site
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-packages", required=True, type=Path)
    parser.add_argument("--server", required=True, type=Path)
    args = parser.parse_args()
    if not args.site_packages.is_dir() or not args.server.is_file():
        parser.error("MCP site-packages directory and exported server must exist")
    site.addsitedir(str(args.site_packages))
    sys.path.insert(0, str(args.server.parent))
    sys.argv = [str(args.server)]
    runpy.run_path(str(args.server), run_name="__main__")


if __name__ == "__main__":
    main()
