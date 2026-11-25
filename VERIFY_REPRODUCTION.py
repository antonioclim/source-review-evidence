#!/usr/bin/env python3
"""Verify a P7D result directory with an explicit scope for omitted stage bytes."""
from pathlib import Path
import runpy
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'qualification/p7d'))
runpy.run_path(str(Path(__file__).resolve().parent/'qualification/p7d/verify_results.py'),run_name='__main__')
