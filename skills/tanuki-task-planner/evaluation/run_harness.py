#!/usr/bin/env python3
"""tanuki-task-planner の決定論的回帰テストを実行する。"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)
    print("タスク計画ハーネス: 通過")
