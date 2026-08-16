# tanuki-spec

要件定義〜設計〜レビュー〜タスク分解までのSPEC駆動開発を、Claude CodeとCodexの両方で行うためのスキル集です。Markdown・YAML・スクリプトだけのツール非依存構成を採用しています。

[`gotalab/cc-sdd`](https://github.com/gotalab/cc-sdd)との併用を標準とする。cc-sddはDiscovery・仕様境界・実装タスク・実装検証を担当し、tanuki-specは業務理解・要件の深掘り・設計判断・テスト設計・画面モック・人向け資料を担当する。決定論的なゲートは品質の下限であり、テンプレート充足を最終目的にしない。

cc-sddと併用する場合は次を前提にする。`docs/spec/`がtanukiの唯一の正本であり、
`.kiro/specs/`はcc-sddの実装運用領域として扱う。tanukiは原則として編集せず、共通ブリッジだけが3つの参照カードを自動生成する。
cc-sdd側の`requirements.md`・`design.md`は共通ブリッジが`docs/spec/`正本への参照カードとして
自動生成し、手編集しない。仕様変更は`.kiro`側ではなく`docs/spec/`へ差し戻し、
tanukiのゲート通過後に橋渡し情報を更新する。

cc-sdd本体は複製せず、検証済みの公式npmパッケージを外部依存として利用する。生成・設計・タスク引き渡しの開始時は、対象エージェントの現行Skills版が完全に未導入なら、互換性台帳で固定した版を公式インストーラーで追加する。レビュー・テスト・画面モックは環境を変更せず状態を確認し、未導入なら生成工程のプリフライトへ戻す。旧版または部分導入を検出した場合は、既存の`AGENTS.md`・`.kiro/settings/`を自動上書きせず、状態と移行方法を報告する。詳細は[`tanuki-spec-all/references/cc-sdd-integration.md`](./tanuki-spec-all/references/cc-sdd-integration.md)を参照する。

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
│   └── integrations/cc-sdd/       # cc-sdd外部依存の互換性台帳
├── skills/
│   ├── tanuki-spec-generator/     # ①②③: 仕様書の生成と出力ゲート
│   ├── tanuki-spec-design/        # 要件定義書起点の設計生成・追従更新
│   ├── tanuki-spec-test-item/     # 設計起点のUT/ITテスト項目書生成・V字カバレッジ
│   ├── tanuki-spec-reviewer/      # ⑤⑥: 独立レビュー・評価レポート・DoD判定
│   ├── tanuki-task-planner/       # ⑦: cc-sddを使えない単独運用時の代替タスク計画
│   └── tanuki-spec-screen-mock/   # ③.5: 要件定義書から画面モックHTMLを生成
│
├── docs/                         # 設計書・実装計画（生成物はphase配下の`func-<名前>/`単位。詳細はdocs/spec-directory-standard.md参照）
└── tests/                        # ドキュメント同期テスト
```

各スキルの役割と実装状態は[SKILLS.md](./SKILLS.md)、呼び出すときの入力書式は[TEMPLATES.md](./TEMPLATES.md)を参照してください。

## 使い方

1. cc-sddの`kiro-discovery`で、直接実装・単一仕様・複数仕様のどれにするかと責任境界を決める。
2. `tanuki-spec-generator`でプロジェクト文脈を読み、重要度に応じて要件を深掘りする。
3. `tanuki-spec-design`で既存実装を調査し、代替案・採用理由・トレードオフを伴う設計へ進める。
4. 画面を伴う案件では`tanuki-spec-screen-mock`で高リスクな判断は複数案を比較し、通常画面は既存パターンの適合性を確認してから実装前にレビューする。
5. `tanuki-spec-test-item`で重要な業務シナリオ・失敗・復旧を中心にテストを設計する。
6. `tanuki-spec-reviewer`で機械ゲートと、人間による案件適合・深さ・読みやすさの判断ゲートを分けて確認する。
7. DoD通過後、`cc_sdd_bridge.py`でtanuki IDをcc-sddの数値IDへ対応付け、`kiro-spec-tasks`で実装タスクを作って`kiro-impl`へ渡す。`tanuki-task-planner`は橋渡し確認、またはcc-sddを使えない単独運用時だけ使う。

generator / design / test-item は各工程の成果物を作った後、共有の`render_html_views.py`で、phaseごとにサマリ・要件・一枚設計・テストケースの4つだけを`views/`へ生成します。画面があるphaseではscreen-mockが`画面モック.html`を加えます。HTMLは派生物であり、正本はMarkdown/YAMLです。生成コマンドと配置は[仕様書ディレクトリ標準](./docs/spec-directory-standard.md)を参照してください。

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
