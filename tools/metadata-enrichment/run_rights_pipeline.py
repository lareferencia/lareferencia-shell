#!/usr/bin/env python3
"""Compatibility entry point for the migrated metadata tools."""

import os
from pathlib import Path

try:
    from lareferencia_metadata_tools.run_rights_pipeline import main
except ModuleNotFoundError as error:
    raise SystemExit(f"{error}. Install lareferencia-metadata-tools in this Python environment.") from error


if __name__ == "__main__":
    os.environ.setdefault("LR_SHELL_DIR", str(Path(__file__).resolve().parents[2]))
    raise SystemExit(main())
