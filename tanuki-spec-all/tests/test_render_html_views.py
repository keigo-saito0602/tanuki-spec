from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evaluation" / "render_html_views.py"
sys.path.insert(0, str(ROOT / "evaluation"))
import render_html_views as views


SUMMARY = """---
updated: 2026-08-16
---
# 予約サマリ

<!-- FILL:START summary -->
## 決定事項
[共有資料](../../_project/shared.md)を参照する。[要確認: 上限]。
<!-- FILL:END summary -->

> 🔍 **レビュー観点**
> - この作成者向けガイドは表示しない

> 📝 **記入形式**: `| 項目 | 内容 |`

> 🔍 **この節で確認すべきこと**
> - 抜け漏れを確認する

> FILL項目の数は変えない

> **ゴール**: 作成者向けの冒頭ガイド
> **読み手**: レビュアー

<script>alert(1)</script>
[危険](javascript:alert(1))
![追跡画像](https://example.test/pixel.png)

## 付録: 項目の根拠一覧
表示しない根拠。
"""


class HtmlViewTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.spec = self.root / "docs" / "spec"
        self.phase = self.spec / "phase-1_予約"
        self.func_a = self.phase / "func-予約"
        self.func_b = self.phase / "func-認証"
        (self.spec / "_project").mkdir(parents=True)
        (self.spec / "_project" / "shared.md").write_text("# 共有\n", encoding="utf-8")
        for func in (self.func_a, self.func_b):
            (func / "tests").mkdir(parents=True)
        (self.func_a / "00_サマリ.md").write_text(SUMMARY, encoding="utf-8")
        (self.func_b / "00_サマリ.md").write_text("# 認証サマリ\n\n## 目的\nログインする。\n", encoding="utf-8")
        (self.func_a / "01_要件定義書.md").write_text("# 予約要件\n\n## [必須] 範囲\n予約を扱う。\n", encoding="utf-8")
        (self.func_b / "01_要件定義書.md").write_text("# 認証要件\n\n## 範囲\n認証を扱う。\n", encoding="utf-8")
        (self.func_a / "02_基本設計書.md").write_text("# 基本設計\n\n## ER図・DB論理設計\nA (1) -- B\n", encoding="utf-8")
        (self.func_a / "03_詳細設計書.md").write_text("# 詳細設計\n\n## 内部処理シーケンス設計\nA -> B\n\n## DB物理設計・インデックス\nNoSQL定義\n", encoding="utf-8")
        (self.func_b / "02_基本設計書.md").write_text("# 認証基本設計\n\n## アクセス制御\n拒否する。\n", encoding="utf-8")
        (self.func_a / "tests" / "04_テスト項目書.md").write_text("# テスト項目書\n\n## 単体テスト\nUT-101\n", encoding="utf-8")
        (self.phase / "tests").mkdir()
        (self.phase / "tests" / "system-test-cases.md").write_text("# システムテスト\n\n## 正常系\nST-101\n", encoding="utf-8")
        (self.phase / "views").mkdir()
        (self.phase / "views" / "画面モック.html").write_text("<html>mock</html>", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def render(self) -> Path:
        self.assertTrue(views.render_phase(self.phase))
        return self.phase / "views"

    def test_generates_only_four_bundles_and_preserves_screen_mock(self):
        view_dir = self.render()
        generated = {path.name for path in view_dir.iterdir() if path.is_file()}
        self.assertEqual(generated, set(views.OUTPUT_FILES) | {views.SCREEN_MOCK})
        self.assertFalse((view_dir / "index.html").exists())
        self.assertFalse((view_dir / "README.md").exists())

    def test_aggregates_funcs_and_tests_without_reader_noise(self):
        view_dir = self.render()
        summary = (view_dir / "00_サマリ.html").read_text(encoding="utf-8")
        requirements = (view_dir / "01_要件定義書.html").read_text(encoding="utf-8")
        tests = (view_dir / "03_テストケース.html").read_text(encoding="utf-8")
        self.assertIn("func-予約", summary)
        self.assertIn("func-認証", summary)
        self.assertNotIn("FILL:START", summary)
        self.assertNotIn("この作成者向けガイド", summary)
        self.assertNotIn("記入形式", summary)
        self.assertNotIn("この節で確認すべきこと", summary)
        self.assertNotIn("FILL項目", summary)
        self.assertNotIn("作成者向けの冒頭ガイド", summary)
        self.assertNotIn("表示しない根拠", summary)
        self.assertIn("範囲", requirements)
        self.assertNotIn("[必須] 範囲", requirements)
        self.assertEqual(tests.count("ST-101"), 1)
        self.assertIn("UT-101", tests)

    def test_design_navigation_targets_real_unique_anchors(self):
        design = (self.render() / "02_設計書.html").read_text(encoding="utf-8")
        ids = re.findall(r' id="([^"]+)"', design)
        self.assertEqual(len(ids), len(set(ids)))
        coverage = re.search(r'<aside class="coverage-nav".*?</aside>', design)
        self.assertIsNotNone(coverage)
        hrefs = re.findall(r'href="#([^"]+)"', coverage.group(0))
        self.assertGreaterEqual(len(hrefs), 3)
        for target in hrefs:
            self.assertIn(target, ids)
        self.assertIn("ER・データモデル", design)
        self.assertIn("DDL / NoSQL物理スキーマ", design)
        self.assertRegex(design, r'href="#[^"]*内部処理シーケンス[^"]*">業務フロー・シーケンス</a>')
        self.assertRegex(design, r'href="#[^"]*db物理設計[^"]*">DDL / NoSQL物理スキーマ</a>')
        self.assertIn(">インデックス</a>", design)
        self.assertIn(">セキュリティルール</a>", design)

    def test_relative_source_link_is_rebased_from_original_markdown(self):
        summary_path = self.render() / "00_サマリ.html"
        content = summary_path.read_text(encoding="utf-8")
        match = re.search(r'<a href="([^"]+)">共有資料</a>', content)
        self.assertIsNotNone(match)
        resolved = (summary_path.parent / unquote(match.group(1))).resolve()
        self.assertEqual(resolved, (self.spec / "_project" / "shared.md").resolve())

    def test_source_link_supports_symlink_to_document_outside_phase(self):
        external = self.spec / "shared-requirements.md"
        external.write_text("# 共通要件\n", encoding="utf-8")
        linked = self.func_a / "01_要件定義書.md"
        linked.unlink()
        linked.symlink_to(external)

        requirements_path = self.render() / "01_要件定義書.html"
        content = requirements_path.read_text(encoding="utf-8")
        match = re.search(r'<span>正本: <a href="([^"]+)">func-予約/01_要件定義書.md</a>', content)
        self.assertIsNotNone(match)
        resolved = (requirements_path.parent / unquote(match.group(1))).resolve()
        self.assertEqual(resolved, external.resolve())

    def test_accessibility_and_unsafe_markdown(self):
        page = (self.render() / "00_サマリ.html").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"<h1(?:\s|>)", page)), 1)
        self.assertIn("Content-Security-Policy", page)
        self.assertIn("script-src 'none'", page)
        self.assertIn("@media(prefers-color-scheme:dark)", page)
        self.assertIn("@media print", page)
        self.assertIn('<span class="status status-pending">[要確認: 上限]</span>', page)
        self.assertNotIn("<script>", page)
        self.assertNotIn('href="javascript:', page)
        self.assertNotIn("<img", page)
        self.assertIn("画像: 追跡画像", page)

    def test_check_is_read_only_and_detects_change(self):
        view_dir = self.render()
        target = view_dir / "00_サマリ.html"
        before = target.read_text(encoding="utf-8")
        self.assertTrue(views.render_phase(self.phase, check=True))
        changed = SUMMARY.replace("[要確認: 上限]", "[要確認: 受付上限]")
        (self.func_a / "00_サマリ.md").write_text(changed, encoding="utf-8")
        self.assertFalse(views.render_phase(self.phase, check=True))
        self.assertEqual(target.read_text(encoding="utf-8"), before)

    def test_removes_legacy_outputs_but_preserves_unknown_and_screen(self):
        view_dir = self.phase / "views"
        legacy_dir = view_dir / "func-旧機能"
        legacy_dir.mkdir()
        (legacy_dir / "02_基本設計書.html").write_text("old", encoding="utf-8")
        (view_dir / "index.html").write_text("old", encoding="utf-8")
        (view_dir / "README.md").write_text("old", encoding="utf-8")
        (view_dir / "notes.html").write_text("keep", encoding="utf-8")
        self.assertFalse(views.render_phase(self.phase, check=True))
        self.assertTrue((view_dir / "index.html").exists())
        self.assertTrue(views.render_phase(self.phase))
        self.assertFalse(legacy_dir.exists())
        self.assertFalse((view_dir / "index.html").exists())
        self.assertFalse((view_dir / "README.md").exists())
        self.assertEqual((view_dir / "notes.html").read_text(encoding="utf-8"), "keep")
        self.assertEqual((view_dir / "画面モック.html").read_text(encoding="utf-8"), "<html>mock</html>")

    def test_symlinked_output_is_rejected(self):
        outside = self.root / "outside.html"
        outside.write_text("protected", encoding="utf-8")
        target = self.phase / "views" / "00_サマリ.html"
        target.symlink_to(outside)
        self.assertFalse(views.render_phase(self.phase))
        self.assertEqual(outside.read_text(encoding="utf-8"), "protected")

    def test_empty_phase_does_not_create_empty_documents(self):
        empty = self.root / "phase-9_empty"
        empty.mkdir()
        self.assertTrue(views.render_phase(empty))
        self.assertEqual(list((empty / "views").iterdir()), [])

    def test_discovery_cli_and_mtime_independence(self):
        self.assertEqual(views.discover_phase_dirs([self.root]), [self.phase.resolve()])
        generated = subprocess.run([sys.executable, str(SCRIPT), str(self.root)], text=True, capture_output=True, check=False)
        self.assertEqual(generated.returncode, 0, generated.stderr)
        first = (self.phase / "views" / "00_サマリ.html").read_bytes()
        for path in self.phase.rglob("*.md"):
            os.utime(path, (1_900_000_000, 1_900_000_000))
        views.render_phase(self.phase)
        self.assertEqual((self.phase / "views" / "00_サマリ.html").read_bytes(), first)


if __name__ == "__main__":
    unittest.main()
