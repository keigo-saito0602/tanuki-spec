# 起動テンプレート集

各スキルを呼び出すときの入力書式をまとめた。使うスキルの節をコピーし、コメント（`#`）の指示に従って値を埋めて渡す。

テンプレートの正本は各スキルの`SKILL.md`にある。このファイルはそこから転記した横断カタログであり、`tests/test_docs_sync.py`が両者の一致を検証する。片方だけを直すとテストが落ちるため、変更するときは両方を同じ内容に揃える。

スキルの一覧と役割は[SKILLS.md](./SKILLS.md)、工程の流れは[FLOW.md](./FLOW.md)を参照する。

## tanuki-spec-generator

ユーザーストーリーから要件定義書・基本設計書・詳細設計書のドラフトを作る。`工程`と`ストーリー`が埋まるまで生成は始まらない。

```text
tanuki-spec-generator
工程:            # requirements（要件定義）/ basic_design（基本設計）/ detailed_design（詳細設計）
対象func:        # phase内の機能名（例: 予約）。出力先 <phase>/func-<名前>/ の <名前> になる
ストーリー:      # 誰が/いつ/何を/なぜ、のユーザーストーリー群
参照仕様:        # 過去仕様から今回使う内容の抜粋。無ければ空欄
モード:          # full（既定・全項目＋評価）/ quick（必須のみ＋簡易）。空欄ならfull
```

## tanuki-spec-design

要件定義書を入力に、基本設計書・詳細設計書と`design-traceability.yaml`を作る。要件定義書は未完成でも受け付ける。

```text
tanuki-spec-design
要件定義書:              # 必須。未完成でも可
対象func:                # phase内の機能名（例: 予約）。出力先 <phase>/func-<名前>/ の <名前> になる
既存コード:               # 任意。リポジトリまたは対象パス
要件トレーサビリティ:      # traceability.yaml。なければ作成を提案
モード:                   # new（既定）/ update
前回の設計成果物:          # updateでは必須
```

## tanuki-spec-test-item

要件定義書と設計書からUT/ITのテスト項目書とV字カバレッジを作る。

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

## tanuki-spec-reviewer

生成済みの仕様書を独立レビューし、6軸採点とDoD判定を行う。`reviewer`には生成担当と別の担当を書く。

```text
tanuki-spec-reviewer
対象仕様書:      # レビューする記入済み.mdのパス
トレーサビリティ: # 対応する traceability.yaml のパス
設計トレーサビリティ: # 設計工程のみ design-traceability.yaml のパス
モード: # requirements / basic_design / detailed_design / unit_test / integration_test / phase_integration
reviewer:        # 例: codex / claude-new-session。生成担当と別であること
```

## tanuki-task-planner

cc-sdd併用時は承認済みtanuki正本の橋渡しを確認する。cc-sddを使えない単独運用時だけ、トレーサビリティ正本から実装タスク、依存関係、完了条件を作る。

```text
tanuki-task-planner
対象機能:          # 例: レッスン予約機能
対象phase:         # phaseディレクトリのパス
対象リリース:      # MVP / Release 2 など
運用モード(任意):  # cc-sdd（既定） / standalone
```

## tanuki-spec-screen-mock

要件定義書とユーザーストーリーから画面定義を起こし、参考ソースのデザイントークンを当てて、ブラウザで開くだけの単一HTML画面モックを生成する。

```text
tanuki-spec-screen-mock
要件定義書(必須): docs/spec/phase-1_公開サイト・予約/func-予約/01_要件定義書.md, docs/spec/phase-1_公開サイト・予約/func-認証/01_要件定義書.md  # 複数funcを横断して指定
フェーズ(必須): docs/spec/phase-1_公開サイト・予約
参考ソース(任意): tailwind.config.ts / ./ref/top.png / https://example.com
対象アクター(任意): 生徒, 講師
モード(任意): create
```
