# SKILLS 一覧

起動テンプレートは[TEMPLATES.md](./TEMPLATES.md)、工程の流れと役割分担は[FLOW.md](./FLOW.md)にまとめてある。

用語の意味は[用語集（GLOSSARY.md）](./GLOSSARY.md)にまとめてある。

状態欄は、スキルが実行できる状態かどうかを示す。`実装済み`は`SKILL.md`が指示するスクリプトとテンプレートが揃っている。`設計のみ`は手順が確定しているが実行資産がまだなく、そのままでは動かせない。

| スキル | 概要 | 用途 | 入口 | 状態 |
| --- | --- | --- | --- | --- |
| [`tanuki-spec-generator`](./skills/tanuki-spec-generator/) | 仕様書ドラフトを生成し、③の出力ゲートまで実行 | 要件定義・基本設計・詳細設計 | [SKILL.md](./skills/tanuki-spec-generator/SKILL.md) | 実装済み |
| [`tanuki-spec-design`](./skills/tanuki-spec-design/) | 要件定義書から設計書を生成し、設計変更を追従更新 | 基本設計・詳細設計・設計トレーサビリティ | [SKILL.md](./skills/tanuki-spec-design/SKILL.md) | 実装済み |
| [`tanuki-spec-test-item`](./skills/tanuki-spec-test-item/) | 要件・設計からUT/ITのテスト項目書とV字カバレッジを生成・追従更新 | テスト設計・テストトレーサビリティ | [SKILL.md](./skills/tanuki-spec-test-item/SKILL.md) | 実装済み |
| [`tanuki-spec-reviewer`](./skills/tanuki-spec-reviewer/) | 生成済み仕様書を独立レビューし、⑤⑥のDoDを判定 | 品質レビュー | [SKILL.md](./skills/tanuki-spec-reviewer/SKILL.md) | 実装済み |
| [`tanuki-task-planner`](./skills/tanuki-task-planner/) | cc-sdd単独利用不可時の代替タスク計画、またはcc-sddへの引き渡し確認 | 単独運用の実装計画・タスク分解 | [SKILL.md](./skills/tanuki-task-planner/SKILL.md) | 実装済み |
| [`tanuki-spec-screen-mock`](./skills/tanuki-spec-screen-mock/) | 要件定義書から画面定義とデザイントークンを起こし、単一HTMLの画面モックを生成 | 画面構成・画面遷移・配色の実装前レビュー | [SKILL.md](./skills/tanuki-spec-screen-mock/SKILL.md) | 実装済み |

すべてのスキルはClaude CodeとCodexの双方から利用できる。Claude CodeではPlugin経由でのインストールを推奨する（[README.md](./README.md)参照）。Codexはリポジトリ直下の[AGENTS.md](./AGENTS.md)から該当スキルを選ぶ。

## 共有コア

[`tanuki-spec-all`](./tanuki-spec-all/)は、SSOT（`spec-items.yaml`）、テンプレート、決定論的評価器、閲覧用HTMLの共有レンダラを持つ共有コアであり、直接呼び出さない。各スキルはsymlinkで参照する。HTMLはMarkdown/YAMLから再生成でき、phase単位のサマリ・要件・一枚設計・テストケースだけに集約する派生物である。

## 文章の読みやすさ（全スキル共通）

[`tanuki-spec-all/references/cognitive-doc-principles.md`](./tanuki-spec-all/references/cognitive-doc-principles.md)が、認知科学に基づく資料構成の正本である。人が読む文章を出力するスキルは、`references/cognitive-doc-principles.md`のsymlinkでこの1ファイルを参照し、出力前に自己点検する。

正本は「読む負荷を下げる原則（1〜26、35〜36）」と「理解と記憶を残す原則（27〜34）」を分けて持つ。案件適合・思考の深さ・リスク別の詳細度は[`tanuki-spec-all/references/spec-quality-principles.md`](./tanuki-spec-all/references/spec-quality-principles.md)を共通基準とする。対策の向きが異なるため、項目数や文章量だけで一括判定しない。一次情報は[`tanuki-spec-all/research/web-sources.md`](./tanuki-spec-all/research/web-sources.md)に番号対応で記録している。

文字数の上限は制約ではなく分布の目安である。長さを理由に情報を落とすほうが害が大きい。判定は正本の「長い文を許す条件」に置いた。

## 連携

cc-sddのDiscoveryで変更単位と境界を決め、`tanuki-spec-generator`で業務要件を深掘りし、`tanuki-spec-design`で設計判断とトレーサビリティを作る。generator / design / test-item は生成工程の完了時に共有レンダラで4つの人向けHTMLを更新する。監査用FILLブロック・根拠・トレーサビリティは正本の付録やYAMLへ残し、HTMLには読者向けに再編集した本文だけを載せる。レビューは機械ゲートと判断ゲートを分け、DoD通過後の計画をcc-sddのタスク・実装フローへ橋渡しする。導入判定とSSOT分担は[`cc-sdd-integration.md`](./tanuki-spec-all/references/cc-sdd-integration.md)に従う。

要件定義がカバレッジ評価を通過したら、画面を伴う案件では`tanuki-spec-screen-mock`で画面モックを生成し、実装前に画面構成と遷移をレビューする。確定した画面定義は`tanuki-spec-design`の画面一覧・画面遷移設計へ渡す。
