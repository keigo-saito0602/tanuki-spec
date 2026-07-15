# AGENTS.md — tanuki-spec-generator（Codex 向けエントリ）

このディレクトリは仕様書ジェネレーターSKILLです。**手順の正本は [`SKILL.md`](./SKILL.md)** にあります。
Codex（および任意のAIエージェント）は `SKILL.md` の手順に従って実行してください。

## 最短フロー
1. `SKILL.md` を読む。
2. 品質項目マスター `spec-items.yaml` と、対象工程の `templates/<工程>-template.md` を読む。
3. ユーザーストーリー（＋任意で参照仕様の提供内容）から、要件定義書と `traceability.yaml` を生成する（根拠明記ルール順守）。
4. `python3 evaluation/coverage.py <記入済み.md> --strict`、`python3 evaluation/traceability_gate.py <traceability.yaml>`、`python3 evaluation/spec_gate.py <記入済み.md> --traceability <traceability.yaml>` で評価。
5. 出力ゲート通過後は、`tanuki-spec-reviewer`へ独立レビューを引き継ぐ。

## 依存
- Python 3.9+ / `pyyaml`（`pip install pyyaml`）

## 変更禁止・注意
- 品質項目は `spec-items.yaml` が唯一の正本。テンプレは手編集せず `evaluation/generate_templates.py` で再生成する。
- 生成物の文言はすべて日本語。根拠不明な項目は埋めず `[要確認: 質問]` を残す。これは充足ではない。
