from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evaluation" / "render_html_views.py"
sys.path.insert(0, str(ROOT / "evaluation"))
import render_html_views


SAMPLE = """---
date: 2026-07-01
updated: 2026-07-29T15:33:12
---
# 予約機能

## 決定事項
予約を受け付ける。

## 未決事項
[要確認: 上限] と ⚠️ リスク。`[未記入]` はコード内。

| ID | 要件 |
| --- | --- |
| FR-101 | 予約する |

<script>alert(1)</script>
[危険](javascript:alert(1))
![追跡画像](https://example.test/pixel.png)

## 付録
長い根拠。
"""


class HtmlViewTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.phase = self.root / "docs" / "spec" / "phase-1_予約"
        self.phase.mkdir(parents=True)
        (self.phase / "00_サマリ.md").write_text(SAMPLE, encoding="utf-8")
        (self.phase / "01_要件定義書.md").write_text("# 要件\n\n## 範囲\n本文\n", encoding="utf-8")
        (self.phase / "tests").mkdir()
        (self.phase / "tests" / "system-test-cases.md").write_text(
            "# テスト\n\n| ID | 結果 |\n| --- | --- |\n| ST-101 | 成功 |\n", encoding="utf-8"
        )
        for path in self.phase.rglob("*.md"):
            os.utime(path, (1_700_000_000, 1_700_000_000))

    def tearDown(self):
        self.temp.cleanup()

    def test_generation_mapping_navigation_and_readme(self):
        self.assertTrue(render_html_views.render_phase(self.phase))
        views = self.phase / "views"
        self.assertEqual(
            {path.name for path in views.iterdir()},
            {
                "index.html", "README.md", "00_サマリ.html",
                "01_要件定義書.html", "system-test-cases.html",
            },
        )
        index = (views / "index.html").read_text(encoding="utf-8")
        self.assertIn("読む順番", index)
        self.assertIn("未決事項・注意事項を確認する", index)
        self.assertIn("../00_%E3%82%B5%E3%83%9E%E3%83%AA.md", index)
        self.assertIn("2026-07-29T15:33:12", index)
        page = (views / "01_要件定義書.html").read_text(encoding="utf-8")
        self.assertIn('rel="prev"', page)
        self.assertIn('rel="next"', page)
        self.assertIn("閲覧用の派生成果物", page)
        readme = (views / "README.md").read_text(encoding="utf-8")
        self.assertIn("Local HTML Embed", readme)
        self.assertIn("--check", readme)

    def test_accessible_structure_and_safe_markdown(self):
        render_html_views.render_phase(self.phase)
        page = (self.phase / "views" / "00_サマリ.html").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"<h1(?:\s|>)", page)), 1)
        self.assertIn('href="#決定事項"', page)
        self.assertIn('id="決定事項"', page)
        self.assertIn('<div class="table-scroll" tabindex="0"', page)
        self.assertIn("<caption>文書内の表</caption>", page)
        self.assertIn('<th scope="col">', page)
        self.assertIn('<span class="status status-pending">[要確認: 上限]</span>', page)
        self.assertIn("<code>[未記入]</code>", page, "コード内の状態語は装飾しない")
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn('href="javascript:', page)
        self.assertNotIn("<img", page)
        self.assertIn("画像: 追跡画像", page)
        self.assertNotIn("https://example.test/pixel.png", page)
        self.assertIn("@media(prefers-color-scheme:dark)", page)
        self.assertIn("@media print", page)
        self.assertIn("max-width:75ch", page)
        self.assertIn("Content-Security-Policy", page)
        self.assertIn("script-src 'none'", page)
        self.assertIn('<meta name="referrer" content="no-referrer">', page)
        self.assertIn('<details class="supporting-detail" open>', page)
        self.assertIn("「付録」詳細を表示/折りたたむ</summary>", page)
        self.assertIn('<h3 id="付録">付録</h3>', page)
        self.assertIn(":target", page)

    def test_check_is_read_only_and_detects_source_change_or_missing_output(self):
        render_html_views.render_phase(self.phase)
        target = self.phase / "views" / "00_サマリ.html"
        before = target.read_text(encoding="utf-8")
        self.assertTrue(render_html_views.render_phase(self.phase, check=True))
        (self.phase / "00_サマリ.md").write_text(SAMPLE + "\n変更\n", encoding="utf-8")
        self.assertFalse(render_html_views.render_phase(self.phase, check=True))
        self.assertEqual(target.read_text(encoding="utf-8"), before)
        target.unlink()
        self.assertFalse(render_html_views.render_phase(self.phase, check=True))
        self.assertFalse(target.exists())

    def test_known_stale_html_is_removed_but_unknown_html_is_preserved(self):
        views = self.phase / "views"
        views.mkdir()
        stale = views / "03_詳細設計書.html"
        stale.write_text("stale", encoding="utf-8")
        unknown = views / "notes.html"
        unknown.write_text("keep", encoding="utf-8")
        self.assertFalse(render_html_views.render_phase(self.phase, check=True))
        self.assertTrue(stale.exists(), "--check は削除もしない")
        render_html_views.render_phase(self.phase)
        self.assertFalse(stale.exists())
        self.assertEqual(unknown.read_text(encoding="utf-8"), "keep")

    def test_missing_sources_are_skipped(self):
        empty = self.root / "phase-9_empty"
        empty.mkdir()
        self.assertTrue(render_html_views.render_phase(empty))
        self.assertTrue((empty / "views" / "index.html").exists())
        self.assertFalse((empty / "views" / "00_サマリ.html").exists())

    def test_standard_phase_directory_discovery_and_cli(self):
        self.assertEqual(render_html_views.discover_phase_dirs([self.root]), [self.phase.resolve()])
        generated = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.root)],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(generated.returncode, 0, generated.stderr)
        checked = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.root), "--check"],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_rendering_does_not_depend_on_filesystem_mtime(self):
        render_html_views.render_phase(self.phase)
        first = (self.phase / "views" / "index.html").read_bytes()
        for path in self.phase.rglob("*.md"):
            os.utime(path, (1_900_000_000, 1_900_000_000))
        render_html_views.render_phase(self.phase)
        second = (self.phase / "views" / "index.html").read_bytes()
        self.assertEqual(first, second)

    def test_source_without_frontmatter_has_fixed_update_label(self):
        render_html_views.render_phase(self.phase)
        page = (self.phase / "views" / "01_要件定義書.html").read_text(encoding="utf-8")
        self.assertIn("更新日時: 正本に記載なし", page)

    def test_symlinked_views_or_known_output_is_rejected_without_writing(self):
        outside = self.root / "outside"
        outside.mkdir()
        linked_phase = self.root / "phase-2_linked"
        linked_phase.mkdir()
        (linked_phase / "01_要件定義書.md").write_text("# 要件", encoding="utf-8")
        (linked_phase / "views").symlink_to(outside, target_is_directory=True)
        self.assertFalse(render_html_views.render_phase(linked_phase))
        self.assertEqual(list(outside.iterdir()), [])

        views = self.phase / "views"
        views.mkdir()
        target = outside / "protected.html"
        target.write_text("保護", encoding="utf-8")
        (views / "01_要件定義書.html").symlink_to(target)
        self.assertFalse(render_html_views.render_phase(self.phase))
        self.assertFalse(render_html_views.render_phase(self.phase, check=True))
        self.assertEqual(target.read_text(encoding="utf-8"), "保護")
        self.assertFalse((views / "index.html").exists())

    def test_all_supported_documents_are_generated_with_fixed_names(self):
        for document in render_html_views.DOCUMENTS:
            source = self.phase / document.source
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(f"# {document.label}\n", encoding="utf-8")
        self.assertTrue(render_html_views.render_phase(self.phase))
        generated = {path.name for path in (self.phase / "views").glob("*.html")}
        self.assertEqual(
            generated,
            {"index.html", *(document.output for document in render_html_views.DOCUMENTS)},
        )

    def test_encoded_or_network_path_urls_are_not_executable_links(self):
        markdown = "\n".join(
            [
                "[script](java%73cript:alert(1))",
                "[data](data:text/html,attack)",
                "[network](//evil.example/path)",
                "[file](file:///tmp/attack)",
                "[relative](../safe.md)",
                "[web](https://safe.example/path)",
            ]
        )
        body, _ = render_html_views.markdown_to_html(markdown)
        self.assertNotIn('href="java%73cript:', body)
        self.assertNotIn('href="data:', body)
        self.assertNotIn('href="//evil.example', body)
        self.assertNotIn('href="file:', body)
        self.assertEqual(
            body.count('class="unsafe-link"'),
            2,
            "Markdown parserが文字列化したdata/file以外も安全なspanへ変換する",
        )
        self.assertIn('href="../safe.md"', body)
        self.assertIn('href="https://safe.example/path"', body)


if __name__ == "__main__":
    unittest.main()
