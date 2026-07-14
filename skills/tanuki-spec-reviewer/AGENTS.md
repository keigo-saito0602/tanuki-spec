# AGENTS.md — tanuki-spec-reviewer

Codex等のエージェントは[SKILL.md](./SKILL.md)を読み、生成担当とは別の立場でレビューする。

## 最短フロー

1. 対象仕様書と生成側の出力ゲート結果を確認する。
2. 6軸を独立して採点し、レビューYAMLを作成する。
3. `validate_review.py`で記録を検証する。
4. DoD判定と残課題を報告する。
