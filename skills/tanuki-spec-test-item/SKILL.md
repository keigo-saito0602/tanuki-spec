---
name: tanuki-spec-test-item
description: Use when generating or updating unit/integration test case documents from requirements and design specs, tracing tests back to BR/FR/NFR and BD/DD, or asking for V-model coverage across UT/IT/ST/UAT.
---

# tanuki-spec-test-item

> 🚀 **30秒でわかる**: 要件と設計から、テストすべき項目の一覧と「どこまで確かめられているか」を洗い出す。

> 📖 わからない用語は [用語集（GLOSSARY.md）](../../GLOSSARY.md) を参照。

要件定義書・設計書・既存トレーサビリティ正本を入力に、UT/ITとV字カバレッジを統合した `04_テスト項目書.md`、`test-traceability.yaml` を作るためのスキル。既存の AC/ST を重複生成せず、V字モデルの下半分だけを新規に扱う。

## 起動テンプレート

```text
tanuki-spec-test-item
要件定義書:                   # 必須
基本設計書:                    # 必須
詳細設計書:                    # 必須
対象phase:                    # phaseディレクトリのパス
対象func:                     # phase内の機能名（例: 予約）。出力先 <phase>/func-<名前>/ の <名前> になる
要件トレーサビリティ:           # func直下のtraceability.yaml。必須
設計トレーサビリティ:           # func直下のdesign-traceability.yaml。必須
モード:                        # new（既定）/ update
前回のテスト成果物:             # update では必須
```

## 手順

0. 入力として渡された`<phase>`から`docs/spec/system-baseline/`を解決する
   （カレントディレクトリ基準ではなく、`<phase>`の親を辿って解決する）。存在する場合は
   `システム構成・共通基盤.md`・`非機能ベースライン.md`を読み、記載と矛盾しない内容にする。
   共通用語は`GLOSSARY.md`を正とする。存在しない場合はこのステップを省略する
   （初回フェーズ等でまだ作られていないことがある）。
   参照した場合は、`reports/01_差分・未決事項.md`に「参照したベースライン文書」を記録する。

1. 入力の要件定義書、基本設計書、詳細設計書、`traceability.yaml`、`design-traceability.yaml` を読む。`design-traceability.yaml` の `requirements_traceability` が指す要件正本と、明示的に渡された `traceability.yaml` が同一か確認する。
2. 既存 AC/ST は phase直下の `system-traceability.yaml` と `render_traceability_docs.py` が正本であることを前提にし、UT/IT だけを新規対象にする。`ST` の `test_type: integration` と、V字モデルの `IT` を混同しない。
3. テスト観点として、`spec-items.yaml` の `test_perspectives`、詳細設計にあるデシジョンテーブル・状態遷移、非機能要件、既存 AC/ST を確認する。要件外だが試験設計に必要な前提は質問し、回答がない場合は `[要確認: 質問]` を残す。
4. `new` では `test-traceability-template.yaml` をもとに `test-traceability.yaml` を作る。作成時は `system_traceability: ../system-traceability.yaml` を明記し、AC/STの正本がphase直下の `system-traceability.yaml` であることを示す。`UT-xxx` は `DD-xxx`、`IT-xxx` は `BD-xxx` に紐づけ、各 `requirement_ids` は紐づく設計要素の `requirement_ids` の部分集合にする。横断テストが必要でも v1 では勝手に例外を作らない。
5. `update` では前回成果物と今回の要件・設計正本を比較し、影響を受ける `UT/IT` だけを更新する。削除候補のテスト項目は即削除せず、`[要確認: 廃止してよいか]` を残す。
6. `render_test_item_docs.py` で `04_テスト項目書.md` を生成する。`## 単体テスト（UT）`、`## 結合テスト（IT）`、`## V字モデルカバレッジ` の3節を1本にまとめ、V字モデルカバレッジには既存の `AC(UAT)` と `ST` を参照表示して再定義しない。
7. 次を実行し、未被覆・不整合・列崩れがあれば修正する。

```bash
python3 evaluation/test_traceability_gate.py <test-traceability.yaml>
python3 evaluation/render_test_item_docs.py <test-traceability.yaml> --output-dir <phase>/func-<名前>/tests
python3 evaluation/render_test_item_docs.py <test-traceability.yaml> --output-dir <phase>/func-<名前>/tests --check
python3 evaluation/render_html_views.py <phase>
python3 evaluation/render_html_views.py <phase> --check
```

HTMLレンダラはフェーズ内に存在する文書だけを生成対象とし、未着手工程はエラーにせずスキップする。HTMLは閲覧用の派生物なので、内容を直す場合は正本Markdown/YAMLを更新して再生成する。

8. テスト工程のレビューが必要な場合は `tanuki-spec-reviewer` に渡し、`unit_test` または `integration_test` を `target` にしたレビュー記録を検証する。この工程では `--spec` や `coverage.py` を使わない。
9. テスト項目書の散文を出力する前に、[`references/cognitive-doc-principles.md`](./references/cognitive-doc-principles.md) の「文レベルの規範」「語彙の規範」で自己点検する。手順と期待結果は一文一動作で書き、指示語で前の項目を指さない。

## 出力

> 置き場所・命名は [`../../docs/spec-directory-standard.md`](../../docs/spec-directory-standard.md) に従う（フェーズ別レイアウト）。

- `<phase>/func-<名前>/test-traceability.yaml`（UT/IT と設計・要件の正本。`system_traceability: ../system-traceability.yaml`でAC/STの正本を参照する）
- `<phase>/func-<名前>/tests/04_テスト項目書.md`（単体・結合・V字カバレッジを1本に統合。見出しは `## 単体テスト（UT）`、`## 結合テスト（IT）`、`## V字モデルカバレッジ`）
- `<phase>/views/`（`index.html`、`README.md`、存在する文書の閲覧用HTML。正本ではなく再生成する派生物）
- `<phase>/func-<名前>/reports/01_差分・未決事項.md`（要確認事項、差分追従時の影響範囲、既存 AC/ST の再利用方針）

## 禁止事項

- `traceability.yaml`、`design-traceability.yaml`、既存 AC/ST 生成器を改変しない。
- テスト工程を `coverage.py` や `generate_templates.py` の対象フェーズへ足さない。
- `test_items[].requirement_ids` に、紐づく設計要素と無関係な要件 ID を入れない。
- `approval_status` を変更しない。

## 共有コア

`spec-items.yaml`、`templates/`、評価スクリプトは `tanuki-spec-all` の SSOT を symlink 参照する。共有コアの複製、再パッケージ化、`sys.path` 注入はしない。
