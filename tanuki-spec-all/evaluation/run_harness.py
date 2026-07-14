#!/usr/bin/env python3
"""決定論部分の回帰テストをまとめて実行する。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(command: list[str]) -> None:
    print("$ " + " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    run([sys.executable, "evaluation/generate_templates.py", "--check"])
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    print("決定論ハーネス: 通過")
    print("モデル評価は evals/cases.yaml をClaude Code/Codexで各3回実行し、結果を記録してください。")


if __name__ == "__main__":
    main()
