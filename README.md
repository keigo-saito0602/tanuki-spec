# tanuki-spec

要件定義〜設計〜レビュー〜タスク分解までのSPEC駆動開発を、Claude CodeとCodexの両方で行うためのスキル集です。Markdown・YAML・スクリプトだけのツール非依存構成を採用しています。

[`gotalab/cc-sdd`](https://github.com/gotalab/cc-sdd)の仕様駆動開発の考え方を参考にしつつ、決定論的なゲート（機械検証）を軸にした独自の路線を取っています。

cc-sddと併用する場合は次を前提にする。`docs/spec/`がtanukiの唯一の正本であり、
`.kiro/specs/`はcc-sddの実装運用領域として扱う（tanukiは`.kiro/`配下を生成・編集しない）。
cc-sdd側の`requirements.md`・`design.md`を使う場合は`docs/spec/`正本への参照カードまたは
自動生成した要約にとどめ、手編集しない。仕様変更は`.kiro`側ではなく`docs/spec/`へ差し戻し、
tanukiのゲート通過後に橋渡し情報を更新する。

## インストール

### Claude Code Plugin

```text
/plugin marketplace add keigo-saito0602/tanuki-spec
/plugin install tanuki-spec
```

### Codex

Plugin機構はないため、このリポジトリを対象プロジェクトへクローンして使います。
Codexはルートの[AGENTS.md](./AGENTS.md) → 各スキルの`SKILL.md`の順に自動で読み込み、
該当スキルを選びます。

```bash
git clone https://github.com/keigo-saito0602/tanuki-spec.git
cd tanuki-spec/skills/<使うスキル名> && python3 -m pip install -r requirements.txt
```

詳細は[FLOW.md](./FLOW.md)の「Codexで動かすとき」を参照してください。

## 構成

```text
tanuki-spec/
├── README.md                     # このファイル
├── SKILLS.md                     # スキル一覧と実装状態
├── TEMPLATES.md                  # 各スキルの起動テンプレート集
├── AGENTS.md                     # Codex等のエージェント向け入口
├── FLOW.md                       # 工程の流れと役割分担
├── GLOSSARY.md                   # SPEC関連の用語集
│
├── tanuki-spec-all                # SSOT・評価器・共有HTMLレンダラ（共有コア。SKILL.mdを持たないためスキル一覧の対象外）
├── skills/
│   ├── tanuki-spec-generator/     # ①②③: 仕様書の生成と出力ゲート
│   ├── tanuki-spec-design/        # 要件定義書起点の設計生成・追従更新
│   ├── tanuki-spec-test-item/     # 設計起点のUT/ITテスト項目書生成・V字カバレッジ
│   ├── tanuki-spec-reviewer/      # ⑤⑥: 独立レビュー・評価レポート・DoD判定
│   ├── tanuki-task-planner/       # ⑦: 実装タスク・依存関係・完了条件の作成
│   └── tanuki-spec-screen-mock/   # ③.5: 要件定義書から画面モックHTMLを生成
│
├── docs/                         # 設計書・実装計画（生成物はphase配下の`func-<名前>/`単位。詳細はdocs/spec-directory-standard.md参照）
└── tests/                        # ドキュメント同期テスト
```

各スキルの役割と実装状態は[SKILLS.md](./SKILLS.md)、呼び出すときの入力書式は[TEMPLATES.md](./TEMPLATES.md)を参照してください。

## 使い方

1. `tanuki-spec-generator`で仕様書を生成し、③の出力ゲートまで実行する。
2. 要件定義書から設計を起こす、または要件変更に設計を追従させる場合は`tanuki-spec-design`を使う。
3. 画面を伴う案件では`tanuki-spec-screen-mock`で画面モックを生成し、実装前にレビューする。
4. 設計工程を経た案件でUT/ITのテスト項目書とV字カバレッジが必要な場合は`tanuki-spec-test-item`を使う。
5. 対象仕様書を`tanuki-spec-reviewer`へ渡し、生成担当と別の担当が⑤の独立レビューを行う。
6. [FLOW.md](./FLOW.md)のDoD（⑥）を満たした仕様書だけを実装へ渡す。
7. `tanuki-task-planner`で実装タスクへ分解する。

generator / design は各工程の成果物を作った後、共有の`render_html_views.py`で`views/`に閲覧用HTMLを生成します。HTMLは派生物であり、正本はMarkdown/YAMLです。生成コマンド、ファイル配置、Obsidianデスクトップでの開き方は[仕様書ディレクトリ標準](./docs/spec-directory-standard.md)を参照してください。

## 検証

共有コアと各スキルの決定論チェックは、スキルごとのハーネスで実行します。

```bash
cd tanuki-spec-all && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python evaluation/run_harness.py
```

ドキュメントとスキル実体の同期は、リポジトリ直下で検証します。

```bash
python3 -m unittest discover -s tests -v
```

## エージェントからの利用

Codexはルートの[AGENTS.md](./AGENTS.md)から該当スキルを選びます。Claude CodeでPlugin経由ではなく手動で認識させる場合は、`skills/`配下の各スキルディレクトリを`~/.claude/skills/`へsymlinkします。

スキルを追加・変更・削除したときは、[AGENTS.md](./AGENTS.md)の「ドキュメント同期」に従い、関連ドキュメントを同じコミットで更新してください。

## 由来

別のスキル集リポジトリからSPEC開発系スキルを`git filter-repo`で履歴ごと抽出した独立リポジトリです。
