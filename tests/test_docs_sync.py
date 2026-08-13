"""ドキュメントとスキル実体の同期を検証する。

スキルを追加・変更・削除したのに一覧を直し忘れると、実行できないスキルを
実行できるものとして案内することになる。その取り違えを機械的に落とす。
規約は AGENTS.md の「ドキュメント同期」を正本とする。
"""
from __future__ import annotations

import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

DOCS = {name: (ROOT / name).read_text(encoding="utf-8") for name in ("README.md", "SKILLS.md", "AGENTS.md", "TEMPLATES.md")}


def actual_skills() -> set[str]:
    return {p.parent.name for p in ROOT.glob("skills/tanuki-*/SKILL.md")}


def skills_md_status() -> dict[str, str]:
    """SKILLS.md の表から スキル名 -> 状態 を読む。"""
    status = {}
    for row in re.finditer(r"^\|\s*\[`(tanuki-[\w-]+)`\].*\|\s*(実装済み|設計のみ)\s*\|\s*$", DOCS["SKILLS.md"], re.M):
        status[row.group(1)] = row.group(2)
    return status


def extract_template(text: str, skill: str) -> str | None:
    """SKILL.md / TEMPLATES.md から起動テンプレートのコードブロックを取り出す。"""
    match = re.search(rf"```(?:text)?\n({re.escape(skill)}\n.*?)```", text, re.S)
    return match.group(1).strip() if match else None


REFERENCED_FILE_PATTERN = re.compile(
    r"(?:\.\./[\w-]+/)?(?:evaluation|scripts|templates|references|assets)/[A-Za-z0-9_.-]+\.(?:py|md|ya?ml|json|html)"
)


def referenced_files(text: str) -> set[str]:
    return set(REFERENCED_FILE_PATTERN.findall(text))


class DocsSyncTest(unittest.TestCase):
    def test_skills_md_lists_every_skill(self):
        self.assertEqual(skills_md_status().keys() | set(), actual_skills(), "SKILLS.md の一覧が実体と一致していない")

    def test_agents_md_lists_every_skill(self):
        listed = set(re.findall(r"^\|\s*`(tanuki-[\w-]+)`\s*\|", DOCS["AGENTS.md"], re.M))
        self.assertEqual(listed, actual_skills(), "AGENTS.md の一覧が実体と一致していない")

    def test_readme_tree_lists_every_skill(self):
        listed = set(re.findall(r"^[│├└─\s]+(tanuki-[\w-]+)/", DOCS["README.md"], re.M))
        self.assertEqual(listed, actual_skills(), "README.md の構成が実体と一致していない")

    def test_templates_md_documents_every_skill(self):
        listed = set(re.findall(r"^## (tanuki-[\w-]+)\s*$", DOCS["TEMPLATES.md"], re.M))
        self.assertEqual(listed, actual_skills(), "TEMPLATES.md の起動テンプレート集が実体と一致していない")

    def test_startup_template_matches_between_skill_md_and_templates_md(self):
        for skill in sorted(actual_skills()):
            with self.subTest(skill=skill):
                own = extract_template((ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8"), skill)
                self.assertIsNotNone(own, f"{skill}/SKILL.md に起動テンプレートがない")
                catalog = extract_template(DOCS["TEMPLATES.md"], skill)
                self.assertEqual(catalog, own, f"{skill} の起動テンプレートが SKILL.md と TEMPLATES.md で食い違っている")

    def test_implemented_skills_reference_only_existing_files(self):
        """`実装済み` のスキルは、SKILL.md が指すスクリプトとテンプレートが揃っていること。"""
        for skill, status in sorted(skills_md_status().items()):
            if status != "実装済み":
                continue
            with self.subTest(skill=skill):
                text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                referenced = referenced_files(text)
                missing = sorted(ref for ref in referenced if not (ROOT / "skills" / skill / ref).exists())
                self.assertEqual(missing, [], f"{skill}/SKILL.md が存在しないファイルを参照している")


if __name__ == "__main__":
    unittest.main()
