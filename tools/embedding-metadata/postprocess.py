#!/usr/bin/env python3
"""Compatibility entry point for the migrated metadata tools."""

try:
    from lareferencia_embedding_metadata.postprocess import main
except ModuleNotFoundError as error:
    raise SystemExit(f"{error}. Install lareferencia-metadata-tools in this Python environment.") from error


if __name__ == "__main__":
    raise SystemExit(main())
