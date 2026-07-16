# AGENTS.md — tanuki-spec-test-item

Codex等のエージェントは[SKILL.md](./SKILL.md)を読み、UT/IT のテスト項目書とテストトレーサビリティを生成・更新する。

## 最短フロー

1. 要件定義書、設計書、`traceability.yaml`、`design-traceability.yaml` を確認する。
2. `test-traceability.yaml` を作成または更新し、UT/IT の帳票を生成する。
3. `test_traceability_gate.py` と `render_test_item_docs.py --check` で整合を検証する。

## 変更禁止・注意

- AC/ST は既存正本を再利用し、重複生成しない。
- テスト工程には `coverage.py` を使わない。
- 不明点は埋めず、`[要確認: 質問]` を残す。
