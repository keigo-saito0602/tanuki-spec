---
name: tanuki-spec-test-item
description: Use when generating or updating unit/integration test case documents from requirements and design specs, tracing tests back to BR/FR/NFR and BD/DD, or asking for V-model coverage across UT/IT/ST/UAT.
---

# tanuki-spec-test-item

要件定義書・設計書・既存トレーサビリティ正本を入力に、UT/IT のテスト項目書、`test-traceability.yaml`、`v-model-coverage.md` を作るためのスキル。既存の AC/ST を重複生成せず、V字モデルの下半分だけを新規に扱う。

## 起動テンプレート

```text
tanuki-spec-test-item
要件定義書:                   # 必須
基本設計書:                    # 必須
詳細設計書:                    # 必須
要件トレーサビリティ:           # traceability.yaml。必須
設計トレーサビリティ:           # design-traceability.yaml。必須
モード:                        # new（既定）/ update
前回のテスト成果物:             # update では必須
```

## 手順

1. 入力の要件定義書、基本設計書、詳細設計書、`traceability.yaml`、`design-traceability.yaml` を読む。`design-traceability.yaml` の `requirements_traceability` が指す要件正本と、明示的に渡された `traceability.yaml` が同一か確認する。
2. 既存 AC/ST は `traceability.yaml` と `render_traceability_docs.py` が正本であることを前提にし、UT/IT だけを新規対象にする。`ST` の `test_type: integration` と、V字モデルの `IT` を混同しない。
3. テスト観点として、`spec-items.yaml` の `test_perspectives`、詳細設計にあるデシジョンテーブル・状態遷移、非機能要件、既存 AC/ST を確認する。要件外だが試験設計に必要な前提は質問し、回答がない場合は `[要確認: 質問]` を残す。
4. `new` では `test-traceability-template.yaml` をもとに `test-traceability.yaml` を作る。`UT-xxx` は `DD-xxx`、`IT-xxx` は `BD-xxx` に紐づけ、各 `requirement_ids` は紐づく設計要素の `requirement_ids` の部分集合にする。横断テストが必要でも v1 では勝手に例外を作らない。
5. `update` では前回成果物と今回の要件・設計正本を比較し、影響を受ける `UT/IT` だけを更新する。削除候補のテスト項目は即削除せず、`[要確認: 廃止してよいか]` を残す。
6. `render_test_item_docs.py` で `unit-test-cases.md`、`integration-test-cases.md`、`v-model-coverage.md` を生成する。`v-model-coverage.md` には既存の `AC(UAT)` と `ST` を参照表示し、再定義しない。
7. 次を実行し、未被覆・不整合・列崩れがあれば修正する。

```bash
python3 evaluation/test_traceability_gate.py <test-traceability.yaml>
python3 evaluation/render_test_item_docs.py <test-traceability.yaml> --output-dir <成果物ディレクトリ> --check
```

8. テスト工程のレビューが必要な場合は `tanuki-spec-reviewer` に渡し、`unit_test` または `integration_test` を `target` にしたレビュー記録を検証する。この工程では `--spec` や `coverage.py` を使わない。

## 出力

- `test-traceability.yaml`（UT/IT と設計・要件の正本）
- `unit-test-cases.md`
- `integration-test-cases.md`
- `v-model-coverage.md`
- 要確認事項、差分追従時の影響範囲、既存 AC/ST の再利用方針

## 禁止事項

- `traceability.yaml`、`design-traceability.yaml`、既存 AC/ST 生成器を改変しない。
- テスト工程を `coverage.py` や `generate_templates.py` の対象フェーズへ足さない。
- `test_items[].requirement_ids` に、紐づく設計要素と無関係な要件 ID を入れない。
- `approval_status` を変更しない。

## 共有コア

`spec-items.yaml`、`templates/`、評価スクリプトは `tanuki-spec-all` の SSOT を symlink 参照する。共有コアの複製、再パッケージ化、`sys.path` 注入はしない。
