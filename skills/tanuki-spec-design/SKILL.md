---
name: tanuki-spec-design
description: 未完成でもよい要件定義書を入力に、既存コード調査・確認質問・要件から設計へのトレーサビリティを伴う基本設計書と詳細設計書を生成・差分追従更新する。要件定義書から設計を起こす、設計変更を追従する、brownfield案件を設計するときに使う。
---

# tanuki-spec-design

> 🚀 **30秒でわかる**: 要件定義書を渡すと、それをどう作るかを描いた設計書に起こし、後から要件が変わっても追いかけて直してくれる。

> 📖 わからない用語は [用語集（GLOSSARY.md）](../../GLOSSARY.md) を参照。

要件定義書だけでなく、既存プロジェクトと調査記録を読み、リスクに応じた基本設計書・詳細設計書と設計トレーサビリティを作る設計特化フロー。既存`tanuki-spec-generator`の設計工程は置き換えず、併用する。テンプレートは構造のガイドであり、全項目を均等に埋めることを目的にしない。

## 起動テンプレート

```text
tanuki-spec-design
要件定義書:              # 必須。未完成でも可
対象func:                # phase内の機能名（例: 予約）。出力先 <phase>/func-<名前>/ の <名前> になる
既存コード:               # 任意。リポジトリまたは対象パス
要件トレーサビリティ:      # traceability.yaml。なければ作成を提案
モード:                   # new（既定）/ update
前回の設計成果物:          # updateでは必須
```

入力を受け取ったら、設計開始前にまず読み取り専用でcc-sddの導入状態を確認する。

```bash
python3 evaluation/cc_sdd_preflight.py <project-root> --agent <codex|claude> --check
```

`missing`の場合は、固定版`cc-sdd@3.0.2`と、追加先（Codexは`.agents/skills/`、Claudeは`.claude/skills/`、共通は`.kiro/settings/`）をユーザーへ提示する。**ユーザーがこの導入へ明示的に同意した後だけ**、同じコマンドの`--check`を`--ensure --consent`へ変えて実行する。`--agent`は省略しない。`partial`または`legacy`の場合は`--ensure`を実行せず、既存状態と手動移行が必要な理由を報告する。

cc-sddはDiscovery、責任境界、実装運用（`.kiro/`）を担う。tanuki-specの正本はプロジェクトの`docs/spec/`であり、cc-sddの`requirements.md`・`design.md`は参照カードまたは自動生成要約に限る。詳しい同期規則、調査の深さ、読者向け再編集は[`references/cc-sdd-integration.md`](./references/cc-sdd-integration.md)と[`references/spec-quality-principles.md`](./references/spec-quality-principles.md)を読む。

## 手順

0. 入力として渡された`<phase>`から`docs/spec/system-baseline/`を解決する
   （カレントディレクトリ基準ではなく、`<phase>`の親を辿って解決する）。存在する場合は
   `システム構成・共通基盤.md`・`非機能ベースライン.md`を読み、記載と矛盾しない内容にする。
   共通用語は`GLOSSARY.md`を正とする。存在しない場合はこのステップを省略する
   （初回フェーズ等でまだ作られていないことがある）。
   参照した場合は、`reports/01_差分・未決事項.md`に「参照したベースライン文書」を記録する。

   さらに、プロジェクトルートの規約・目的・利用者、既存の`docs/spec/`、`.kiro/steering/`、対象`.kiro/specs/`の`brief.md`・`roadmap.md`・`research.md`（存在するもの）を読み、既存コード・画面・データ・外部連携の事実を確認する。事実・推測・未確定事項を分け、見つからない資料は推測で補わない。

1. 入力の要件定義書、`spec-items.yaml`、`templates/basic-design-template.md`、`templates/detailed-design-template.md`を読む。テンプレートは構造のガイドとして使い、リスク分類と読者の判断に必要な項目を選ぶ。選んだ項目の記入ガイド・出典・品質観点は、テンプレート末尾の「付録: 項目の根拠一覧」の該当ID行から確認する。要件IDが無い場合は、`traceability-template.yaml`を使い`BR-`、`FR-`、`NFR-`を採番する。
2. 既存コードがある場合、調査担当を分けてリポジトリ構成、実行経路、データ、外部連携、認証、テストを調べる。`research.md`または案件の調査記録には、問い・情報源・確認できた事実・比較した案・採用しなかった理由を残す。調査結果は事実と推測を分け、設計の根拠に使う。
3. 要件にないが設計に必要な決定事項を質問する。例: 利用者と権限、保存期間、外部連携、性能目標、障害時の復旧、移行、運用担当。回答なしは勝手に確定せず`[要確認: 質問]`を残す。
4. 基本設計書・詳細設計書は、先頭を読者向け本文として案件別に編集する。**本文は概要ではなく、監査付録を開かなくても実装判断が完結する一枚設計書**にする。目的・境界・主要シナリオ・方式と判断理由・データ・失敗と復旧・リスク・未決事項から必要な章だけを選び、低リスク部分は表へ畳み、高リスク部分を深掘りする。テンプレートの全FILLブロックと根拠一覧は`## 付録: 監査用項目`以下へ隔離する。付録には`[入力] 要件ID`、`[参照] 既存コード`と本文の見出し・`BD/DD-ID`への参照を置き、本文と同じ設計説明を再掲しない。本文にない設計判断を付録だけへ書いた場合は不合格とする。該当する場合は次を本文へ明記する。
   - 状態変化、外部連携、競合がある処理はシーケンスまたは番号付きフローで示す。
   - データ間の関係はER図とキー・多重度で示す。
   - RDBはDDL、NoSQLはコレクション・主要フィールド・インデックス・セキュリティルールを物理設計として示す。該当しない方式のDDLを捏造しない。
5. `templates/design-traceability-template.yaml`から`design-traceability.yaml`を作る。要件ごとに設計要素を`BD-xxx`（基本設計）または`DD-xxx`（詳細設計）で表し、`requirement_ids`に`BR/FR/NFR`を指定する。既存`traceability.yaml`は変更しない。
6. `new`では成果物を新規作成する。`update`では要件定義書・`traceability.yaml`・前回の設計書・`design-traceability.yaml`を比較し、追加・変更・削除された要件と影響するBD/DDだけを更新する。削除された要件の設計要素は削除せず、まず`[要確認: 廃止してよいか]`として確認する。
7. 以下を実行し、未記入やリンク切れがあれば該当箇所を修正する。

```bash
python3 evaluation/coverage.py <基本設計書.md> --phase basic_design --strict
python3 evaluation/coverage.py <詳細設計書.md> --phase detailed_design --strict
python3 evaluation/design_traceability_gate.py <design-traceability.yaml>
python3 evaluation/render_design_traceability_docs.py <design-traceability.yaml> --output-dir <phase>/func-<名前>/tests
python3 evaluation/render_html_views.py <phase>
python3 evaluation/render_html_views.py <phase> --check
```

HTMLレンダラはフェーズ内に存在する文書だけを生成対象とし、未着手工程はエラーにせずスキップする。`--check` はファイルを書き換えず、生成対象の欠落・正本との差分・不要な旧派生物・未記入の読者向け本文・マーカー不整合だけを表示し、スキップ対象自体は表示しない。HTMLは閲覧用の派生物なので、内容を直す場合は正本Markdown/YAMLを更新して再生成する。

8. レビューは`tanuki-spec-reviewer`へ渡す。設計工程は`--design-traceability`付きでレビュー記録を検証する。
9. 設計書の散文を出力する前に、[`references/cognitive-doc-principles.md`](./references/cognitive-doc-principles.md) の「症状を二つに分ける」「文レベルの規範」「語彙の規範」「想起を組み込む規範」で自己点検する。設計判断は、代替案・根拠・トレードオフ・再検討条件を示して読み手が検証できる形に残す。案件固有の品質判断は[`references/spec-quality-principles.md`](./references/spec-quality-principles.md)に従う。

## 出力

> 置き場所・命名は [`../../docs/spec-directory-standard.md`](../../docs/spec-directory-standard.md) に従う（フェーズ別レイアウト）。

- `<phase>/func-<名前>/02_基本設計書.md`、`<phase>/func-<名前>/03_詳細設計書.md`
- `<phase>/func-<名前>/design-traceability.yaml`（要件とBD/DDの正本）
- `<phase>/func-<名前>/tests/design-traceability.md`（正本から生成する対応表）
- `<phase>/views/02_設計書.html`（全funcの基本・詳細設計を統合し、シーケンス・ER・DDLまたはNoSQL物理設計を確認できる一枚の閲覧用HTML）
- `<phase>/func-<名前>/reports/01_差分・未決事項.md`（要確認事項、既存コード調査結果、update時の影響範囲）

## 共有コア

`spec-items.yaml`、`templates/`、評価スクリプトは`tanuki-spec-all`へのsymlinkを使う。複製や`sys.path`注入をしない。`approval_status`が`pending_owner_approval`の間、成果物はドラフトであり承認状態を変更しない。
