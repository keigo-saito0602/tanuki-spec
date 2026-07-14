#!/usr/bin/env python3
"""共有コアと生成側の回帰テストを実行する。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    subprocess.run([sys.executable, "../tanuki-spec-all/evaluation/run_harness.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
