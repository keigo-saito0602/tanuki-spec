---
name: tanuki-task-planner
description: Use when cc-sddを使えない単独運用で、承認済み要件を依存関係・完了条件・検証付きの実装タスクへ分解するとき、またはtanuki-spec成果物をcc-sddのkiro-spec-tasksへ引き渡す情報を確認するとき。
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
運用モード(任意):  # cc-sdd（既定） / standalone
```

入力を受け取ったら運用モードを確定する。既定の`cc-sdd`では未導入なら固定版を導入し、導入済みなら状態だけを記録する。

```bash
python3 evaluation/cc_sdd_preflight.py <project-root> --agent <codex|claude> --ensure
```

`standalone`は、ユーザーがcc-sddを使わないと明示した場合だけ選ぶ。この場合は環境を変更せず`--check`で状態を記録し、未導入でも単独タスク計画へ進む。

```bash
python3 evaluation/cc_sdd_preflight.py <project-root> --agent <codex|claude> --check
```

cc-sddはDiscovery、責任境界、実装運用（`.kiro/`）を担い、tanuki-specの正本はプロジェクトの`docs/spec/`とする。併用時の実装タスク正本はcc-sddの`.kiro/specs/<feature>/tasks.md`である。`task-plan.yaml`を別に生成しない。cc-sddを使わないと明示された単独運用だけは、`task-plan.yaml`と人向け計画を実装計画として扱う。詳細な同期規則と品質判断は[`references/cc-sdd-integration.md`](./references/cc-sdd-integration.md)と[`references/spec-quality-principles.md`](./references/spec-quality-principles.md)を読む。

## 手順

0. 入力として渡された`<phase>`から`docs/spec/system-baseline/`を解決する
   （カレントディレクトリ基準ではなく、`<phase>`の親を辿って解決する）。存在する場合は
   `システム構成・共通基盤.md`・`非機能ベースライン.md`を読み、記載と矛盾しない内容にする。
   共通用語は`GLOSSARY.md`を正とする。存在しない場合はこのステップを省略する
   （初回フェーズ等でまだ作られていないことがある）。
   参照した場合は、`reports/01_差分・未決事項.md`に「参照したベースライン文書」を記録する。

   さらに、プロジェクトルートの実装規約・運用制約、既存の`docs/spec/`、`.kiro/steering/`、対象`.kiro/specs/`の`brief.md`・`roadmap.md`・`research.md`・`tasks.md`（存在するもの）を読む。既存タスク、コード、CI、リリース手順も確認し、事実・推測・未確定事項を分ける。

1. `<phase>/system-traceability.yaml` と、phase配下の各 `func-<名前>/traceability.yaml` を読み、対象リリースのUS、BR/FR/NFR、AC、STを確認する。未確定・対象外の要件はタスク化しない。既存のcc-sdd `tasks.md`があれば、ファイル境界・実装順・実装メモの現行運用も確認する。
2. cc-sddを併用する場合は、共通ブリッジで`docs/spec/`の正本から`.kiro/specs/<spec>/spec.json`・`requirements.md`・`design.md`を生成する。これらは数値要件IDとtanuki IDの対応、正本への相対リンク、境界だけを持つ参照カードであり、手編集しない。
   ```bash
   python3 evaluation/cc_sdd_bridge.py render <project-root> --phase <phase-path> --func <func-名前> --spec <spec名>
   python3 evaluation/cc_sdd_bridge.py check <project-root> --phase <phase-path> --func <func-名前> --spec <spec名>
   ```
   tanukiのDoD通過とユーザー承認後、`draft`要件がないことを確認して同じ`render`へ`--approve`を付ける。その後`kiro-spec-tasks <spec名>`へ渡し、このSKILLでタスク本文を生成せず終了する。`-y`で未決要件を強制承認しない。
   cc-sddを使わない単独運用の場合だけ、[templates/task-plan-template.yaml](./templates/task-plan-template.yaml) をコピーし、要件を設計・データ・バックエンド・フロントエンド・連携・テスト・検証・文書化の実装単位へ分解する。
3. 以降は単独運用の場合だけ実行する。各 `TASK-xxx` に、対応要件、対応AC/ST、依存タスク、完了条件、検証方法を記入する。タスク名を「〜を作成する」のような成果物・変更内容で書き、曖昧な「対応する」は使わない。利用者・事業への影響、不確実性、技術的結合、失敗時の復旧難度が高いものほど、前提・代替案・根拠・トレードオフ・復旧検証をタスクの完了条件へ残す。
4. 次を実行する。
```bash
python3 evaluation/task_plan_gate.py <task-plan.yaml> --system-traceability <phase>/system-traceability.yaml
python3 evaluation/render_task_plan.py <task-plan.yaml> --output <implementation-task-plan.md>
```
5. 単独運用のゲートが不通過なら、孤立した要件・試験、未記入、依存関係の循環を解消してから実装へ渡す。cc-sdd併用へ途中で切り替えた場合は、以後のタスク正本を`tasks.md`へ一本化し、同じタスク本文を複製しない。
6. `implementation-task-plan.md`を出力する前に、[`references/cognitive-doc-principles.md`](./references/cognitive-doc-principles.md) の「文レベルの規範」「語彙の規範」で自己点検する。このMarkdownは人向けの橋渡しビューであり、cc-sddの実装タスク正本ではない。目的・実装境界・重要リスク・未決事項の順に再編集し、タスク名と完了条件は一文一動作で書く。案件固有の品質判断は[`references/spec-quality-principles.md`](./references/spec-quality-principles.md)に従う。

## 出力

- cc-sdd併用: 共通ブリッジが`.kiro/specs/<spec>/spec.json`・`requirements.md`・`design.md`を自動生成する。実装タスクの正本はcc-sddが生成する`tasks.md`。
- 単独運用: `<phase>/task-plan.yaml`、`<phase>/implementation-task-plan.md`。

`evaluation/cc_sdd_bridge.py`は共有コアへのsymlinkであり、ブリッジ生成物の所有権、入力パス、symlink、既存`tasks.md`を検査する。

## 分解基準

- 1タスクは、原則としてレビュー可能な1つの成果物または変更目的にする。
- BR/FR/NFR、AC、STのいずれもタスクから孤立させない。
- `depends_on` は着手順であり、循環を作らない。
- 完了条件は成果物の状態、検証方法は実行するテスト・確認手順を具体的に書く。
