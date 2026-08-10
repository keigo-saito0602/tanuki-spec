# SKILLS 一覧

起動テンプレートは[TEMPLATES.md](./TEMPLATES.md)、工程の流れと役割分担は[FLOW.md](./FLOW.md)にまとめてある。

用語の意味は[用語集（GLOSSARY.md）](./GLOSSARY.md)にまとめてある。

状態欄は、スキルが実行できる状態かどうかを示す。`実装済み`は`SKILL.md`が指示するスクリプトとテンプレートが揃っている。`設計のみ`は手順が確定しているが実行資産がまだなく、そのままでは動かせない。

| スキル | 概要 | 用途 | 入口 | 状態 |
| --- | --- | --- | --- | --- |
| [`tanuki-spec-generator`](./skills/tanuki-spec-generator/) | 仕様書ドラフトを生成し、③の出力ゲートまで実行 | 要件定義・基本設計・詳細設計 | [SKILL.md](./skills/tanuki-spec-generator/SKILL.md) | 実装済み |
| [`tanuki-spec-design`](./skills/tanuki-spec-design/) | 要件定義書から設計書を生成し、設計変更を追従更新 | 基本設計・詳細設計・設計トレーサビリティ | [SKILL.md](./skills/tanuki-spec-design/SKILL.md) | 実装済み |
| [`tanuki-spec-test-item`](./skills/tanuki-spec-test-item/) | 要件・設計からUT/ITのテスト項目書とV字カバレッジを生成・追従更新 | テスト設計・テストトレーサビリティ | [SKILL.md](./skills/tanuki-spec-test-item/SKILL.md) | 設計のみ |
| [`tanuki-spec-reviewer`](./skills/tanuki-spec-reviewer/) | 生成済み仕様書を独立レビューし、⑤⑥のDoDを判定 | 品質レビュー | [SKILL.md](./skills/tanuki-spec-reviewer/SKILL.md) | 実装済み |
| [`tanuki-task-planner`](./skills/tanuki-task-planner/) | トレーサビリティ正本から実装タスク、依存関係、完了条件を作成・検証 | 実装計画・タスク分解 | [SKILL.md](./skills/tanuki-task-planner/SKILL.md) | 実装済み |
| [`tanuki-spec-screen-mock`](./skills/tanuki-spec-screen-mock/) | 要件定義書から画面定義とデザイントークンを起こし、単一HTMLの画面モックを生成 | 画面構成・画面遷移・配色の実装前レビュー | [SKILL.md](./skills/tanuki-spec-screen-mock/SKILL.md) | 実装済み |

すべてのスキルはClaude CodeとCodexの双方から利用できる。Claude CodeではPlugin経由でのインストールを推奨する（[README.md](./README.md)参照）。Codexはリポジトリ直下の[AGENTS.md](./AGENTS.md)から該当スキルを選ぶ。

## tanuki-spec-test-item の未実装部分

`SKILL.md`が実行を指示している`evaluation/test_traceability_gate.py`、`evaluation/render_test_item_docs.py`、`templates/test-traceability-template.yaml`はまだ存在しない。手順とドライラン観察ログは確定しているため、実行資産を実装すればそのまま`実装済み`へ移せる。それまでは、UT/ITの設計方針を読む資料として扱う。

## 共有コア

[`tanuki-spec-all`](./tanuki-spec-all/)は、SSOT（`spec-items.yaml`）、テンプレート、決定論的評価器、閲覧用HTMLの共有レンダラを持つ共有コアであり、直接呼び出さない。各スキルはsymlinkで参照する。HTMLはMarkdown/YAMLから再生成できる派生物であり、`tanuki-spec-test-item`へのHTML工程追加によって同スキル本体の状態が`設計のみ`から変わることはない。

## 文章の読みやすさ（全スキル共通）

[`tanuki-spec-all/references/cognitive-doc-principles.md`](./tanuki-spec-all/references/cognitive-doc-principles.md)が、認知科学に基づく資料構成の正本である。人が読む文章を出力するスキルは、`references/cognitive-doc-principles.md`のsymlinkでこの1ファイルを参照し、出力前に自己点検する。

正本は「読む負荷を下げる原則（1〜26、35〜36）」と「理解と記憶を残す原則（27〜34）」を分けて持つ。対策の向きが逆なので、症状を分けずに直すと打ち消し合う。一次情報は[`tanuki-spec-all/research/web-sources.md`](./tanuki-spec-all/research/web-sources.md)に番号対応で記録している。

文字数の上限は制約ではなく分布の目安である。長さを理由に情報を落とすほうが害が大きい。判定は正本の「長い文を許す条件」に置いた。

## 連携

`tanuki-spec-generator`で要件を整え、必要に応じて`tanuki-spec-design`で設計と設計トレーサビリティを作る。generator / design は生成工程の完了時に共有レンダラで`views/`を更新し、`tanuki-spec-test-item`は本体実装後に同じ工程へ合流する。レビューは対象成果物を`tanuki-spec-reviewer`へ渡し、生成担当と別の担当が独立採点する。DoDを満たしたら`tanuki-task-planner`で実装タスクへ分解する。

要件定義がカバレッジ評価を通過したら、画面を伴う案件では`tanuki-spec-screen-mock`で画面モックを生成し、実装前に画面構成と遷移をレビューする。確定した画面定義は`tanuki-spec-design`の画面一覧・画面遷移設計へ渡す。
