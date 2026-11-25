#!/usr/bin/env python3
"""Local integrated CodeProbe reproduction. Use -I -S -B; see README_P7D.md."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'qualification/p7d'))
from pipeline import main
if __name__ == '__main__':
    raise SystemExit(main())
