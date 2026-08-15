#!/usr/bin/env python3
"""共有コアと生成側の回帰テストを実行する。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    subprocess.run([sys.executable, "../../tanuki-spec-all/evaluation/run_harness.py"], cwd=ROOT, check=True)
    sample_dir = ROOT / "examples" / "sample-user-story"

    phase1_dir = sample_dir / "phase-1_レッスン予約"
    func1_dir = phase1_dir / "func-予約"
    subprocess.run([
        sys.executable, "evaluation/traceability_gate.py", str(func1_dir / "traceability.yaml"),
    ], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable, "evaluation/system_traceability_gate.py", str(phase1_dir / "system-traceability.yaml"),
    ], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable,
        "evaluation/render_traceability_docs.py",
        str(phase1_dir / "system-traceability.yaml"),
        "--output-dir",
        str(phase1_dir / "tests"),
        "--check",
    ], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable,
        "evaluation/render_feature_files.py",
        str(phase1_dir / "system-traceability.yaml"),
        "--output-dir",
        str(phase1_dir / "features"),
        "--check",
    ], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable,
        "evaluation/render_html_views.py",
        str(phase1_dir),
        "--check",
    ], cwd=ROOT, check=True)

    phase2_dir = sample_dir / "phase-2_複数機能例"
    for func_name in ("func-予約", "func-認証"):
        subprocess.run([
            sys.executable, "evaluation/traceability_gate.py", str(phase2_dir / func_name / "traceability.yaml"),
        ], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable, "evaluation/system_traceability_gate.py", str(phase2_dir / "system-traceability.yaml"),
    ], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable,
        "evaluation/render_traceability_docs.py",
        str(phase2_dir / "system-traceability.yaml"),
        "--output-dir",
        str(phase2_dir / "tests"),
        "--check",
    ], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable,
        "evaluation/render_feature_files.py",
        str(phase2_dir / "system-traceability.yaml"),
        "--output-dir",
        str(phase2_dir / "features"),
        "--check",
    ], cwd=ROOT, check=True)
    subprocess.run([
        sys.executable,
        "evaluation/render_html_views.py",
        str(phase2_dir),
        "--check",
    ], cwd=ROOT, check=True)

    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
