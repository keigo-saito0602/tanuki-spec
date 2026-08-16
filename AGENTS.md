# AGENTS.md — tanuki-spec

このリポジトリはSPEC駆動開発（要件定義〜設計〜レビュー〜タスク分解）のためのスキル集合です。目的に合うスキルの`SKILL.md`を読み、手順に従ってください。呼び出すときの入力書式は[TEMPLATES.md](./TEMPLATES.md)にまとまっています。

通常はcc-sddと併用する。cc-sddはDiscovery・境界・実装運用、tanuki-specは業務要件の深掘り・設計判断・テスト・画面・人向け資料を担当する。開始時の導入判定と正本の分担は[`tanuki-spec-all/references/cc-sdd-integration.md`](./tanuki-spec-all/references/cc-sdd-integration.md)、生成判断は[`tanuki-spec-all/references/spec-quality-principles.md`](./tanuki-spec-all/references/spec-quality-principles.md)に従う。

| スキル | 用途 | 手順書 | 状態 |
| --- | --- | --- | --- |
| `tanuki-spec-generator` | 仕様書ドラフト生成と③の出力ゲート | [`SKILL.md`](./skills/tanuki-spec-generator/SKILL.md) | 実装済み |
| `tanuki-spec-design` | 要件定義書から設計書を生成・追従更新し、要件↔設計を追跡する | [`SKILL.md`](./skills/tanuki-spec-design/SKILL.md) | 実装済み |
| `tanuki-spec-test-item` | 要件・設計からUT/ITのテスト項目書とV字カバレッジを生成・追従更新する | [`SKILL.md`](./skills/tanuki-spec-test-item/SKILL.md) | 実装済み |
| `tanuki-spec-reviewer` | ⑤⑥の独立レビュー、評価レポート、DoD判定 | [`SKILL.md`](./skills/tanuki-spec-reviewer/SKILL.md) | 実装済み |
| `tanuki-task-planner` | tanuki正本をcc-sddタスク生成へ橋渡しする。cc-sddを使えない単独運用では実装タスクへ分解する | [`SKILL.md`](./skills/tanuki-task-planner/SKILL.md) | 実装済み |
| `tanuki-spec-screen-mock` | 要件定義書から画面モックHTMLを生成し、画面構成・遷移・配色をレビュー可能にする | [`SKILL.md`](./skills/tanuki-spec-screen-mock/SKILL.md) | 実装済み |

`tanuki-spec-all`はSSOT・評価器・閲覧用HTMLレンダラの共有コアであり、直接呼び出さない。generator / design / test-item は正本Markdown/YAMLの生成後に共有レンダラで`views/`を更新する。

## 規約

- 生成物の文言は日本語にする。
- 根拠不明な項目は埋めず、`[要確認: 質問]`を残す。
- SSOTとテンプレートは共有コア（`tanuki-spec-all`）を唯一の正本とする。
- テンプレート項目の充足を目的にせず、読者向け本文と監査用付録を分ける。
- 要件・設計・テストの詳細度は、利用者影響・不確実性・結合・復旧難度に応じて変える。

## ドキュメント同期

スキルを追加、変更、削除したときは、同じコミットで次のドキュメントを更新する。後回しにすると、一覧と実体が食い違い、実行できないスキルを実行できるものとして案内することになる。

| 変更 | 更新するドキュメント |
| --- | --- |
| スキルの追加・削除・改名 | [`README.md`](./README.md)の構成、[`SKILLS.md`](./SKILLS.md)、この`AGENTS.md`、[`TEMPLATES.md`](./TEMPLATES.md) |
| 起動テンプレートの変更 | 該当`SKILL.md`と[`TEMPLATES.md`](./TEMPLATES.md)の両方を同じ内容にする |
| スクリプト・テンプレートの追加や削除 | 該当`SKILL.md`の手順、[`SKILLS.md`](./SKILLS.md)の状態欄 |
| 工程・番号・DoDの変更 | [`FLOW.md`](./FLOW.md)、[`SKILLS.md`](./SKILLS.md)、[`README.md`](./README.md)の工程番号 |
| 用途・役割の変更 | [`SKILLS.md`](./SKILLS.md)と、この`AGENTS.md`の用途欄 |

更新漏れは`tests/test_docs_sync.py`が検出する。コミット前に次を実行する。

```bash
python3 -m unittest discover -s tests -v
```

このテストは、スキル実体と一覧の一致、`SKILL.md`と`TEMPLATES.md`の起動テンプレートの一致、`実装済み`のスキルが参照するファイルの存在を検証する。テストが落ちたら、実体に合わせてドキュメントを直す。
