from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evaluation" / "render_html_views.py"
sys.path.insert(0, str(ROOT / "evaluation"))
import render_html_views as views


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
    """func-*/system名前空間の下で、既存の描画・安全性・再生成ロジックが
    引き続き成立することを確認する（Task 10でパスをfunc/system配下へ移動）。"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.phase = self.root / "docs" / "spec" / "phase-1_予約"
        self.func = self.phase / "func-予約"
        self.func.mkdir(parents=True)
        (self.func / "00_サマリ.md").write_text(SAMPLE, encoding="utf-8")
        (self.func / "01_要件定義書.md").write_text("# 要件\n\n## 範囲\n本文\n", encoding="utf-8")
        (self.func / "02_基本設計書.md").write_text("# 基本設計\n\n## 方針\n本文\n", encoding="utf-8")
        (self.phase / "tests").mkdir()
        (self.phase / "tests" / "system-test-cases.md").write_text(
            "# テスト\n\n| ID | 結果 |\n| --- | --- |\n| ST-101 | 成功 |\n", encoding="utf-8"
        )
        for path in self.phase.rglob("*.md"):
            os.utime(path, (1_700_000_000, 1_700_000_000))

    def tearDown(self):
        self.temp.cleanup()

    def test_generation_mapping_navigation_and_readme(self):
        self.assertTrue(views.render_phase(self.phase))
        view_dir = self.phase / "views"
        generated_html = {str(path.relative_to(view_dir)) for path in view_dir.rglob("*.html")}
        self.assertEqual(
            generated_html,
            {
                "index.html",
                "func-予約/index.html",
                "func-予約/00_サマリ.html",
                "func-予約/01_要件定義書.html",
                "func-予約/02_基本設計書.html",
                "system/system-test-cases.html",
            },
        )
        self.assertTrue((view_dir / "README.md").is_file())

        top_index = (view_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn("<h3>func-予約</h3>", top_index)
        self.assertIn("機能ごとの文書", top_index)
        self.assertIn("phase共通の文書", top_index)
        func_index_match = re.search(r'<a href="([^"]+)">func-予約の目次</a>', top_index)
        self.assertIsNotNone(func_index_match)
        resolved_func_index = (view_dir / unquote(func_index_match.group(1))).resolve()
        self.assertEqual(resolved_func_index, (view_dir / "func-予約" / "index.html").resolve())

        func_index = (view_dir / "func-予約" / "index.html").read_text(encoding="utf-8")
        self.assertIn("読む順番", func_index)
        self.assertIn("未決事項・注意事項を確認する", func_index)
        self.assertIn("2026-07-29T15:33:12", func_index)
        source_link_match = re.search(r'<a href="([^"]+)">正本: 00_サマリ\.md</a>', func_index)
        self.assertIsNotNone(source_link_match)
        resolved_source = (view_dir / "func-予約" / unquote(source_link_match.group(1))).resolve()
        self.assertEqual(resolved_source, (self.func / "00_サマリ.md").resolve())
        self.assertTrue(resolved_source.is_file())

        page = (view_dir / "func-予約" / "01_要件定義書.html").read_text(encoding="utf-8")
        self.assertIn('rel="prev"', page)
        self.assertIn('rel="next"', page)
        self.assertIn("閲覧用の派生成果物", page)

        readme = (view_dir / "README.md").read_text(encoding="utf-8")
        self.assertIn("Local HTML Embed", readme)
        self.assertIn("--check", readme)

    def test_accessible_structure_and_safe_markdown(self):
        views.render_phase(self.phase)
        page = (self.phase / "views" / "func-予約" / "00_サマリ.html").read_text(encoding="utf-8")
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
        views.render_phase(self.phase)
        target = self.phase / "views" / "func-予約" / "00_サマリ.html"
        before = target.read_text(encoding="utf-8")
        self.assertTrue(views.render_phase(self.phase, check=True))
        (self.func / "00_サマリ.md").write_text(SAMPLE + "\n変更\n", encoding="utf-8")
        self.assertFalse(views.render_phase(self.phase, check=True))
        self.assertEqual(target.read_text(encoding="utf-8"), before)
        target.unlink()
        self.assertFalse(views.render_phase(self.phase, check=True))
        self.assertFalse(target.exists())

    def test_known_stale_html_is_removed_but_unknown_html_is_preserved(self):
        view_dir = self.phase / "views"
        (view_dir / "func-予約").mkdir(parents=True)
        stale = view_dir / "func-予約" / "03_詳細設計書.html"
        stale.write_text("stale", encoding="utf-8")
        unknown = view_dir / "notes.html"
        unknown.write_text("keep", encoding="utf-8")
        self.assertFalse(views.render_phase(self.phase, check=True))
        self.assertTrue(stale.exists(), "--check は削除もしない")
        views.render_phase(self.phase)
        self.assertFalse(stale.exists())
        self.assertEqual(unknown.read_text(encoding="utf-8"), "keep")

    def test_missing_sources_are_skipped(self):
        empty = self.root / "phase-9_empty"
        empty.mkdir()
        self.assertTrue(views.render_phase(empty))
        self.assertTrue((empty / "views" / "index.html").exists())
        self.assertFalse((empty / "views" / "00_サマリ.html").exists())

    def test_standard_phase_directory_discovery_and_cli(self):
        self.assertEqual(views.discover_phase_dirs([self.root]), [self.phase.resolve()])
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
        # views/index.html（phase_index_html）はsource_updated()を呼ばない静的な内容のため、
        # source_updated()の出力を実際に描画するfunc-予約/index.html（func_index）を対象にする。
        views.render_phase(self.phase)
        first = (self.phase / "views" / "func-予約" / "index.html").read_bytes()
        for path in self.phase.rglob("*.md"):
            os.utime(path, (1_900_000_000, 1_900_000_000))
        views.render_phase(self.phase)
        second = (self.phase / "views" / "func-予約" / "index.html").read_bytes()
        self.assertEqual(first, second)

    def test_source_without_frontmatter_has_fixed_update_label(self):
        views.render_phase(self.phase)
        page = (self.phase / "views" / "func-予約" / "01_要件定義書.html").read_text(encoding="utf-8")
        self.assertIn("更新日時: 正本に記載なし", page)

    def test_symlinked_views_or_known_output_is_rejected_without_writing(self):
        outside = self.root / "outside"
        outside.mkdir()
        linked_phase = self.root / "phase-2_linked"
        linked_phase.mkdir()
        (linked_phase / "views").symlink_to(outside, target_is_directory=True)
        self.assertFalse(views.render_phase(linked_phase))
        self.assertEqual(list(outside.iterdir()), [])

        view_dir = self.phase / "views"
        view_dir.mkdir()
        target = outside / "protected.html"
        target.write_text("保護", encoding="utf-8")
        (view_dir / "01_要件定義書.html").symlink_to(target)
        self.assertFalse(views.render_phase(self.phase))
        self.assertFalse(views.render_phase(self.phase, check=True))
        self.assertEqual(target.read_text(encoding="utf-8"), "保護")
        self.assertFalse((view_dir / "index.html").exists())

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
        body, _ = views.markdown_to_html(markdown)
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


class DiscoverFuncsTest(unittest.TestCase):
    def test_finds_func_prefixed_directories_only(self):
        with tempfile.TemporaryDirectory() as directory_str:
            phase_dir = Path(directory_str)
            (phase_dir / "func-予約").mkdir()
            (phase_dir / "func-認証").mkdir()
            (phase_dir / "system-baseline").mkdir()
            funcs = views.discover_funcs(phase_dir)
            self.assertEqual([path.name for path in funcs], ["func-予約", "func-認証"])


class RenderPhaseWithFuncsTest(unittest.TestCase):
    def _make_phase(self, phase_dir: Path) -> None:
        func_dir = phase_dir / "func-予約"
        func_dir.mkdir(parents=True)
        (func_dir / "01_要件定義書.md").write_text("---\nupdated: 2026-08-01\n---\n# 要件\n", encoding="utf-8")
        (phase_dir / "tests").mkdir()
        (phase_dir / "tests" / "system-test-cases.md").write_text("# ST\n", encoding="utf-8")

    def test_generates_func_namespaced_and_system_namespaced_views(self):
        with tempfile.TemporaryDirectory() as directory_str:
            phase_dir = Path(directory_str) / "phase-1_予約"
            self._make_phase(phase_dir)
            self.assertTrue(views.render_phase(phase_dir))
            self.assertTrue((phase_dir / "views" / "func-予約" / "01_要件定義書.html").is_file())
            self.assertTrue((phase_dir / "views" / "system" / "system-test-cases.html").is_file())
            self.assertTrue((phase_dir / "views" / "index.html").is_file())

    def test_check_mode_detects_no_diff_after_generation(self):
        with tempfile.TemporaryDirectory() as directory_str:
            phase_dir = Path(directory_str) / "phase-1_予約"
            self._make_phase(phase_dir)
            views.render_phase(phase_dir)
            self.assertTrue(views.render_phase(phase_dir, check=True))

    def test_index_links_to_screen_mock_html_when_present(self):
        with tempfile.TemporaryDirectory() as directory_str:
            phase_dir = Path(directory_str) / "phase-1_予約"
            self._make_phase(phase_dir)
            (phase_dir / "views").mkdir(exist_ok=True)
            (phase_dir / "views" / "画面モック.html").write_text("<html></html>", encoding="utf-8")
            views.render_phase(phase_dir)
            index_content = (phase_dir / "views" / "index.html").read_text(encoding="utf-8")
            self.assertIn("画面モック.html", index_content)

    def test_func_page_source_link_resolves_to_real_file(self):
        """views/func-予約/01_要件定義書.htmlの「正本を開く」リンクが、実在する
        func-予約/01_要件定義書.md を指すことを、実際にパスを解決して確認する。"""
        import re

        with tempfile.TemporaryDirectory() as directory_str:
            phase_dir = Path(directory_str) / "phase-1_予約"
            self._make_phase(phase_dir)
            views.render_phase(phase_dir)
            html_path = phase_dir / "views" / "func-予約" / "01_要件定義書.html"
            content = html_path.read_text(encoding="utf-8")
            match = re.search(r'正本Markdownを開く</a>', content)
            self.assertIsNotNone(match, msg="「正本Markdownを開く」リンクが見つかりません")
            href_match = re.search(r'<a href="([^"]+)">正本Markdownを開く</a>', content)
            self.assertIsNotNone(href_match)
            # hrefはquote()でURLエンコードされているため、ファイルパスとして解決する前にunquoteする
            # （namespace「func-予約」は非ASCII文字を含み、そのままでは実在パスと一致しない）。
            resolved = (html_path.parent / unquote(href_match.group(1))).resolve()
            self.assertEqual(resolved, (phase_dir / "func-予約" / "01_要件定義書.md").resolve())
            self.assertTrue(resolved.is_file())

    def test_system_page_source_link_resolves_to_real_file(self):
        import re

        with tempfile.TemporaryDirectory() as directory_str:
            phase_dir = Path(directory_str) / "phase-1_予約"
            self._make_phase(phase_dir)
            views.render_phase(phase_dir)
            html_path = phase_dir / "views" / "system" / "system-test-cases.html"
            content = html_path.read_text(encoding="utf-8")
            href_match = re.search(r'<a href="([^"]+)">正本Markdownを開く</a>', content)
            self.assertIsNotNone(href_match)
            resolved = (html_path.parent / unquote(href_match.group(1))).resolve()
            self.assertEqual(resolved, (phase_dir / "tests" / "system-test-cases.md").resolve())
            self.assertTrue(resolved.is_file())

    def test_readme_links_resolve_to_real_func_and_system_files(self):
        """views/README.mdのMarkdownリンク（[出力](パス)）を実際に解決し、
        func・system双方の実在ファイルを指すことを確認する。"""
        import re

        with tempfile.TemporaryDirectory() as directory_str:
            phase_dir = Path(directory_str) / "phase-1_予約"
            self._make_phase(phase_dir)
            views.render_phase(phase_dir)
            readme_path = phase_dir / "views" / "README.md"
            content = readme_path.read_text(encoding="utf-8")
            links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", content)
            # 対応表の行に含まれるリンク（HTMLビュー側・正本側の両方）だけを対象にする
            table_links = [link for link in links if link.startswith("./") or link.startswith("../")]
            self.assertTrue(table_links, msg="対応表のリンクが見つかりません")
            for link in table_links:
                resolved = (readme_path.parent / link).resolve()
                self.assertTrue(resolved.is_file(), msg=f"リンク先が実在しません: {link} -> {resolved}")

    def test_func_page_phase_entry_link_resolves_to_real_file(self):
        """views/func-予約/01_要件定義書.htmlの「フェーズ入口」リンクが、実在する
        views/index.html を指すことを確認する（namespace配下は実際にはviews/phase_dir
        への相対深さ2なので、素の"index.html"のままだと存在しないviews/func-予約/index.html
        を指してしまう回帰）。"""
        with tempfile.TemporaryDirectory() as directory_str:
            phase_dir = Path(directory_str) / "phase-1_予約"
            self._make_phase(phase_dir)
            views.render_phase(phase_dir)
            html_path = phase_dir / "views" / "func-予約" / "01_要件定義書.html"
            content = html_path.read_text(encoding="utf-8")
            href_matches = re.findall(r'<a href="([^"]+)">フェーズ入口', content)
            self.assertTrue(href_matches, msg="「フェーズ入口」リンクが見つかりません")
            for href in href_matches:
                resolved = (html_path.parent / unquote(href)).resolve()
                self.assertEqual(resolved, (phase_dir / "views" / "index.html").resolve())
                self.assertTrue(resolved.is_file())

    def test_system_page_phase_entry_link_resolves_to_real_file(self):
        """views/system/system-test-cases.htmlの「フェーズ入口」リンクも同様に、
        実在するviews/index.html を指すことを確認する。"""
        with tempfile.TemporaryDirectory() as directory_str:
            phase_dir = Path(directory_str) / "phase-1_予約"
            self._make_phase(phase_dir)
            views.render_phase(phase_dir)
            html_path = phase_dir / "views" / "system" / "system-test-cases.html"
            content = html_path.read_text(encoding="utf-8")
            href_matches = re.findall(r'<a href="([^"]+)">フェーズ入口', content)
            self.assertTrue(href_matches, msg="「フェーズ入口」リンクが見つかりません")
            for href in href_matches:
                resolved = (html_path.parent / unquote(href)).resolve()
                self.assertEqual(resolved, (phase_dir / "views" / "index.html").resolve())
                self.assertTrue(resolved.is_file())

    def test_func_index_readme_link_resolves_to_real_file(self):
        """views/func-予約/index.htmlの「Obsidian・ブラウザでの閲覧方法」リンクが、
        実在するviews/README.md を指すことを確認する（同様のnamespace配下の
        リンク深さの回帰）。"""
        with tempfile.TemporaryDirectory() as directory_str:
            phase_dir = Path(directory_str) / "phase-1_予約"
            self._make_phase(phase_dir)
            views.render_phase(phase_dir)
            html_path = phase_dir / "views" / "func-予約" / "index.html"
            content = html_path.read_text(encoding="utf-8")
            href_match = re.search(r'<a href="([^"]+)">Obsidian', content)
            self.assertIsNotNone(href_match, msg="README.mdへのリンクが見つかりません")
            resolved = (html_path.parent / unquote(href_match.group(1))).resolve()
            self.assertEqual(resolved, (phase_dir / "views" / "README.md").resolve())
            self.assertTrue(resolved.is_file())


if __name__ == "__main__":
    unittest.main()
