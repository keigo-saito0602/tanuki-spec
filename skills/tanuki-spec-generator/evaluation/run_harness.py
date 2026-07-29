#!/usr/bin/env python3
"""共有コアと生成側の回帰テストを実行する。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    subprocess.run([sys.executable, "../tanuki-spec-all/evaluation/run_harness.py"], cwd=ROOT, check=True)
    sample_dir = ROOT / "examples" / "sample-user-story"
    subprocess.run([sys.executable, "evaluation/traceability_gate.py", str(sample_dir / "traceability.yaml")], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable,
        "evaluation/render_traceability_docs.py",
        str(sample_dir / "traceability.yaml"),
        "--output-dir",
        str(sample_dir),
        "--check",
    ], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable,
        "evaluation/render_feature_files.py",
        str(sample_dir / "traceability.yaml"),
        "--output-dir",
        str(sample_dir / "features"),
        "--check",
    ], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable,
        "evaluation/render_html_views.py",
        str(sample_dir / "phase-1_レッスン予約"),
        "--check",
    ], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
