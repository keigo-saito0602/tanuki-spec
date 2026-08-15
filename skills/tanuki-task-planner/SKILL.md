---
name: tanuki-task-planner
description: Use when decomposing approved requirements or a feature request into implementation tasks with dependencies, definitions of done, verification, and links to requirements and tests.
---

# tanuki-task-planner

> 🚀 **30秒でわかる**: 固まった要件を、作る順番と「どこまでやれば完了か」つきの作業リストに分解する。

> 📖 わからない用語は [用語集（GLOSSARY.md）](../../GLOSSARY.md) を参照。

## 起動テンプレート

```text
tanuki-task-planner
対象機能:          # 例: レッスン予約機能
対象phase:         # phaseディレクトリのパス
対象リリース:      # MVP / Release 2 など
```

## 手順

0. 入力として渡された`<phase>`から`docs/spec/system-baseline/`を解決する
   （カレントディレクトリ基準ではなく、`<phase>`の親を辿って解決する）。存在する場合は
   `システム構成・共通基盤.md`・`非機能ベースライン.md`を読み、記載と矛盾しない内容にする。
   共通用語は`GLOSSARY.md`を正とする。存在しない場合はこのステップを省略する
   （初回フェーズ等でまだ作られていないことがある）。
   参照した場合は、`reports/01_差分・未決事項.md`に「参照したベースライン文書」を記録する。

1. `<phase>/system-traceability.yaml` と、phase配下の各 `func-<名前>/traceability.yaml` を読み、対象リリースのUS、BR/FR/NFR、AC、STを確認する。未確定・対象外の要件はタスク化しない。
2. [templates/task-plan-template.yaml](./templates/task-plan-template.yaml) をコピーし、要件を設計・データ・バックエンド・フロントエンド・連携・テスト・検証・文書化の実装単位へ分解する。
3. 各 `TASK-xxx` に、対応要件、対応AC/ST、依存タスク、完了条件、検証方法を記入する。タスク名を「〜を作成する」のような成果物・変更内容で書き、曖昧な「対応する」は使わない。
4. 次を実行する。
```bash
python3 evaluation/task_plan_gate.py <task-plan.yaml> --system-traceability <phase>/system-traceability.yaml
python3 evaluation/render_task_plan.py <task-plan.yaml> --output <implementation-task-plan.md>
```
5. ゲートが不通過なら、孤立した要件・試験、未記入、依存関係の循環を解消してから実装へ渡す。
6. `implementation-task-plan.md` を出力する前に、[`references/cognitive-doc-principles.md`](./references/cognitive-doc-principles.md) の「文レベルの規範」「語彙の規範」で自己点検する。タスク名と完了条件は一文一動作で書き、実装者が読み返さずに着手できる状態にする。

## 出力

- `<phase>/task-plan.yaml`（タスク分解の正本）
- `<phase>/implementation-task-plan.md`（人が読む実装タスク計画。着手可能なタスク一覧、WBS・依存関係・ガントのMermaid図、詳細テーブルを含む）

## 分解基準

- 1タスクは、原則としてレビュー可能な1つの成果物または変更目的にする。
- BR/FR/NFR、AC、STのいずれもタスクから孤立させない。
- `depends_on` は着手順であり、循環を作らない。
- 完了条件は成果物の状態、検証方法は実行するテスト・確認手順を具体的に書く。
