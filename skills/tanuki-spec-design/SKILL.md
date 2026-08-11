---
name: tanuki-spec-design
description: 未完成でもよい要件定義書を入力に、既存コード調査・確認質問・要件から設計へのトレーサビリティを伴う基本設計書と詳細設計書を生成・差分追従更新する。要件定義書から設計を起こす、設計変更を追従する、brownfield案件を設計するときに使う。
---

# tanuki-spec-design

> 🚀 **30秒でわかる**: 要件定義書を渡すと、それをどう作るかを描いた設計書に起こし、後から要件が変わっても追いかけて直してくれる。

> 📖 わからない用語は [用語集（GLOSSARY.md）](../../GLOSSARY.md) を参照。

要件定義書を入力に、基本設計書・詳細設計書と設計トレーサビリティを作る設計特化フロー。既存`tanuki-spec-generator`の設計工程は置き換えず、併用する。

## 起動テンプレート

```text
tanuki-spec-design
要件定義書:              # 必須。未完成でも可
既存コード:               # 任意。リポジトリまたは対象パス
要件トレーサビリティ:      # traceability.yaml。なければ作成を提案
モード:                   # new（既定）/ update
前回の設計成果物:          # updateでは必須
```

## 手順

1. 入力の要件定義書、`spec-items.yaml`、`templates/basic-design-template.md`、`templates/detailed-design-template.md`を読む。各項目の記入ガイド・出典・品質観点は、本文ではなくテンプレート末尾の「付録: 項目の根拠一覧」に表として集約されている。記入前に必ず付録の該当ID行を読み、ガイドに沿って記入する。要件IDが無い場合は、`traceability-template.yaml`を使い`BR-`、`FR-`、`NFR-`を採番する。
2. 既存コードがある場合、調査担当を分けてリポジトリ構成、実行経路、データ、外部連携、認証、テストを調べる。調査結果は事実と推測を分け、設計の根拠に使う。
3. 要件にないが設計に必要な決定事項を質問する。例: 利用者と権限、保存期間、外部連携、性能目標、障害時の復旧、移行、運用担当。回答なしは勝手に確定せず`[要確認: 質問]`を残す。
4. 基本設計書・詳細設計書のFILLブロックを記入する。各ブロックは`[入力] 要件ID`、`[参照] 既存コード`、または確認済みの回答を根拠として先頭に明記する。
5. `templates/design-traceability-template.yaml`から`design-traceability.yaml`を作る。要件ごとに設計要素を`BD-xxx`（基本設計）または`DD-xxx`（詳細設計）で表し、`requirement_ids`に`BR/FR/NFR`を指定する。既存`traceability.yaml`は変更しない。
6. `new`では成果物を新規作成する。`update`では要件定義書・`traceability.yaml`・前回の設計書・`design-traceability.yaml`を比較し、追加・変更・削除された要件と影響するBD/DDだけを更新する。削除された要件の設計要素は削除せず、まず`[要確認: 廃止してよいか]`として確認する。
7. 以下を実行し、未記入やリンク切れがあれば該当箇所を修正する。

```bash
python3 evaluation/coverage.py <基本設計書.md> --phase basic_design --strict
python3 evaluation/coverage.py <詳細設計書.md> --phase detailed_design --strict
python3 evaluation/design_traceability_gate.py <design-traceability.yaml>
python3 evaluation/render_design_traceability_docs.py <design-traceability.yaml> --output-dir <phase>/tests
python3 evaluation/render_html_views.py <phase>
python3 evaluation/render_html_views.py <phase> --check
```

HTMLレンダラはフェーズ内に存在する文書だけを生成対象とし、未着手工程はエラーにせずスキップする。HTMLは閲覧用の派生物なので、内容を直す場合は正本Markdown/YAMLを更新して再生成する。

8. レビューは`tanuki-spec-reviewer`へ渡す。設計工程は`--design-traceability`付きでレビュー記録を検証する。
9. 設計書の散文を出力する前に、[`references/cognitive-doc-principles.md`](./references/cognitive-doc-principles.md) の「症状を二つに分ける」「文レベルの規範」「語彙の規範」「想起を組み込む規範」で自己点検する。設計判断は、代替案とトレードオフを示して読み手が検証できる形に残す。

## 出力

> 置き場所・命名は [`../../docs/spec-directory-standard.md`](../../docs/spec-directory-standard.md) に従う（フェーズ別レイアウト）。

- `<phase>/02_基本設計書.md`、`<phase>/03_詳細設計書.md`
- `<phase>/design-traceability.yaml`（要件とBD/DDの正本）
- `<phase>/tests/design-traceability.md`（正本から生成する対応表）
- `<phase>/views/`（`index.html`、`README.md`、存在する要件・設計・対応表の閲覧用HTML。正本ではなく再生成する派生物）
- `<phase>/reports/01_差分・未決事項.md`（要確認事項、既存コード調査結果、update時の影響範囲）

## 共有コア

`spec-items.yaml`、`templates/`、評価スクリプトは`tanuki-spec-all`へのsymlinkを使う。複製や`sys.path`注入をしない。`approval_status`が`pending_owner_approval`の間、成果物はドラフトであり承認状態を変更しない。
