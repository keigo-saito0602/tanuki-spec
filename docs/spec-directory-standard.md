# 仕様書ディレクトリ標準（正本）

tanuki スキル群が生成する仕様書・設計書・テスト・トレーサビリティを、**フェーズ単位・機能（func）単位**で一貫した場所・命名に置くための標準。
各スキルの「出力」節と `FLOW.md` は、この標準に従う。

作成: 2026-07-18 ／ 状態: ドラフト（KEIGO レビュー待ち）／ ブランチ: `feat/spec-dir-layout`

---

## 1. レイアウト

```text
docs/spec/
├── phase-1_公開サイト・予約/
│   ├── README.md                       # 機能一覧・状態・導線
│   ├── system-traceability.yaml        # 業務フロー・AC(受入試験)・STの正本
│   ├── screens.yaml / design-tokens.json   # 画面がある案件のみ。phase単位に集約
│   ├── task-plan.yaml                  # cc-sddを使わない単独運用時だけ作るタスク正本
│   ├── implementation-task-plan.md     # 単独運用時の着手可能一覧・WBS・依存グラフ
│   ├── features/*.feature              # Gherkin。★phase単位に集約（func単位では作らない）
│   ├── tests/
│   │   ├── system-test-cases.md        # ST（system-traceability.yamlから生成）
│   │   └── requirements-traceability.md    # 全func横断の要件・業務フロー・AC対応表
│   ├── views/                          # 人向けHTML。phase単位で5種類以下に集約（§6参照）
│   │   ├── 00_サマリ.html              # 全funcのサマリ
│   │   ├── 01_要件定義書.html          # 全funcの要件
│   │   ├── 02_設計書.html              # 基本・詳細、シーケンス、ER、物理設計を一枚に統合
│   │   ├── 03_テストケース.html        # 全funcのUT/ITとphaseのST
│   │   └── 画面モック.html              # 画面がある場合のみscreen-mockが生成
│   ├── func-予約/
│   │   ├── README.md
│   │   ├── 00_サマリ.md
│   │   ├── 01_要件定義書.md
│   │   ├── 02_基本設計書.md
│   │   ├── 03_詳細設計書.md
│   │   ├── traceability.yaml           # user_stories と requirements のみに縮小
│   │   │                                # requirements の flow_step_ids は残す（§3）
│   │   ├── design-traceability.yaml    # BD/DD（このfuncのrequirementsに紐づく）
│   │   ├── test-traceability.yaml      # UT/IT。system_traceability フィールドを追加（§3）
│   │   ├── tests/04_テスト項目書.md     # UT/IT・V字カバレッジ（AC/ST列はsystem-traceability参照）
│   │   └── reports/01_差分・未決事項.md  # 参照したbaseline文書もここへ記録（§5）
│   └── func-認証/
│       └── （同じ骨格）
└── system-baseline/                    # 変更なし（フェーズ非依存の共通書類）
    ├── README.md
    ├── システム構成・共通基盤.md
    ├── 非機能ベースライン.md
    └── 共通用語.md
```

実装上は、`func-<名前>/tests/` には `04_テスト項目書.md` に加えて `design-traceability.md`（`render_design_traceability_docs.py`が`design-traceability.yaml`から生成する対応表）も置かれる。上のツリーは代表的な構成のみを示す（詳細は§3の対応表を参照）。

## 2. 命名規則

- サマリ層は `00_サマリ.md`。連番の先頭に置き、「まずこれを読む」を名前で示す。要件定義書のぶんだけ作る（設計書は読み手が第三者技術者のため、フル文書を読ませる）。`func-<名前>/00_サマリ.md`としてfunc単位に置く。
- フェーズフォルダ: `phase-<番号>_<日本語名>`（番号は着手順）。
- `func-<名前>/`: フェーズ配下の機能単位フォルダ。プレフィックス `func-` は固定表記（英数字とハイフンのみ）。`<名前>` 部分（機能名）は日本語可（例: `func-予約`、`func-認証`）。US・要件・基本/詳細設計（BD/DD）・UT/ITはこの単位に閉じるため func 配下に置く。業務フロー・AC（受入試験）・ST・画面定義・タスク計画は機能をまたぐことが多いため func 配下ではなく phase 直下に置く（理由は§3の対応表を参照）。
- 人が読む主要文書は連番付き: `01_要件定義書` → `02_基本設計書` → `03_詳細設計書` → `04_テスト項目書`。読む順＝番号順。いずれも `func-<名前>/` 直下に置く（`04_テスト項目書` のみ `func-<名前>/tests/`）。各文書は、案件の理解順で書く「読者向け本文」と、FILLブロック・根拠を置く「付録: 監査用項目」を分ける。テンプレートの項目順を読者向けの章立てにしない。
- func単位の正本 YAML は内容を表す固定名で `func-<名前>/` 直下に置く: `traceability.yaml`（US・要件のみ。`business_flows`/`acceptance_tests`/`system_tests`は含まない）／`design-traceability.yaml`／`test-traceability.yaml`（`system_traceability`フィールドで `../system-traceability.yaml` を参照する）。
- phase単位の正本 YAML はフェーズ直下に置く: `system-traceability.yaml`（業務フロー・AC・ST・`func_traceability`索引の正本）／`screens.yaml`／`design-tokens.json`。`task-plan.yaml`はcc-sddを使わない単独運用時だけ置く。cc-sdd併用時のタスク正本は`.kiro/specs/<spec>/tasks.md`とし、両方を作らない。
- レンダラが出す派生 Markdown（表・テスト項目）は固定名のまま `tests/` に置く。func単位の派生物（`04_テスト項目書.md`・`design-traceability.md`）は `func-<名前>/tests/`、phase横断の派生物（`requirements-traceability.md`・`system-test-cases.md`）は phase直下 `tests/`。
- 閲覧用HTMLは`views/`直下へphase単位で置く。func別フォルダ、system別フォルダ、索引、README、トレーサビリティ単独HTMLは作らない。HTML用のCSS・JavaScript・画像フォルダも作らない。
- `features/` の `.feature` はレンダラが付ける名前のまま。phase単位に集約し、func単位では作らない。

## 3. どのスキルの生成物がどこへ行くか（対応表）

| 生成物（スキル） | 置き場所・名前 |
| --- | --- |
| サマリ層（generator） | `func-<名前>/00_サマリ.md` |
| 記入済み要件定義書（generator） | `func-<名前>/01_要件定義書.md` |
| 基本設計書 / 詳細設計書（design） | `func-<名前>/02_基本設計書.md` / `func-<名前>/03_詳細設計書.md` |
| `traceability.yaml`（generator。`user_stories`・`requirements`のみに縮小） | `func-<名前>/`直下 |
| `design-traceability.yaml`（design） | `func-<名前>/`直下 |
| `test-traceability.yaml`（test-item。`system_traceability: ../system-traceability.yaml`を明記） | `func-<名前>/`直下 |
| `system-traceability.yaml`（generator。業務フロー・AC・ST・`func_traceability`索引の正本） | phase直下 |
| `screens.yaml`・`design-tokens.json`（screen-mock。複数funcを横断して洗い出す） | phase直下 |
| `task-plan.yaml`・`implementation-task-plan.md`（task-planner） | cc-sddを使わない単独運用時のみphase直下 |
| `design-traceability.md`（design。`design-traceability.yaml`から生成） | `func-<名前>/tests/` |
| UT/IT/V字カバレッジ（test-item） | **`func-<名前>/tests/04_テスト項目書.md` に1本統合**（下記§4） |
| `requirements-traceability.md`・`system-test-cases.md`（generator。`system-traceability.yaml`をfunc横断で集約して生成） | phase直下 `tests/` |
| `*.feature`（generator。`system-traceability.yaml`の`acceptance_tests`から生成） | phase直下 `features/`（★func単位では作らない） |
| 閲覧用HTML（generator） | `views/00_サマリ.html`、`views/01_要件定義書.html` |
| 閲覧用HTML（design） | `views/02_設計書.html`（全funcの基本・詳細設計を統合） |
| 閲覧用HTML（test-item） | `views/03_テストケース.html`（全funcのUT/ITとphaseのSTを統合） |
| 画面モックHTML（screen-mock） | `views/画面モック.html`（正本ではない。`render_screen_mock.py`が生成し、共有レンダラは触らない。phase直下） |
| 要確認・未決事項・差分影響・レビュー要約（参照したsystem-baseline文書も含む） | `func-<名前>/reports/01_差分・未決事項.md` |
| `phase_integration_review`（reviewer。業務フロー・AC・ST・共有画面・タスク計画のphase単位レビュー記録） | `<phase>/reports/`直下 |
| （新規・各スキルが追記） | `func-<名前>/README.md`（機能の索引）／phase直下`README.md`（機能一覧・状態・導線） |

## 4. テスト項目書の統合（04_テスト項目書.md）

test-item の単体・結合・V字カバレッジは、**1本の `func-<名前>/tests/04_テスト項目書.md`** にまとめる。見出しで分ける:

```markdown
# テスト項目書
## 単体テスト（UT）
## 結合テスト（IT）
## V字モデルカバレッジ
```

※ `system-test-cases.md`（ST）は性質が違う（システム全体の受入寄り）うえ、機能をまたぐためfunc単位に閉じない。統合せず phase直下の `tests/` に別置きする（`04_テスト項目書.md`は`func-<名前>/tests/`に置く）。

## 5. レンダラ呼び出し規約

func単位の正本 YAML は `func-<名前>/` 直下、phase単位の正本 YAML は phase 直下に置き、出力先はサブフォルダを `--output-dir` で指定する。

```bash
# generator（要件）: funcごとのUS/requirements孤立検出（形式検証のみ。flow_step_idsの実在確認等はsystem_traceability_gate側）
python3 evaluation/traceability_gate.py <phase>/func-<名前>/traceability.yaml

# generator（業務フロー・AC・ST）: phase単位で全funcを横断し、ID一意性・参照整合・カバレッジを検証
python3 evaluation/system_traceability_gate.py <phase>/system-traceability.yaml

# generator（要件対応表・システムテスト項目書）: system-traceability.yaml から phase直下 tests/ へ
python3 evaluation/render_traceability_docs.py <phase>/system-traceability.yaml --output-dir <phase>/tests

# generator（.feature）: system-traceability.yaml から phase直下 features/ へ（func単位では生成しない）
python3 evaluation/render_feature_files.py <phase>/system-traceability.yaml --output-dir <phase>/features

# design（設計対応表）: func内で完結するため入出力とも変更なし。func直下 tests/ へ
python3 evaluation/render_design_traceability_docs.py <phase>/func-<名前>/design-traceability.yaml --output-dir <phase>/func-<名前>/tests

# test-item（テスト項目書）: test-traceability.yaml の system_traceability フィールド経由でAC/STを解決し、func直下 tests/ へ
python3 evaluation/render_test_item_docs.py <phase>/func-<名前>/test-traceability.yaml --output-dir <phase>/func-<名前>/tests

# task-planner: phase横断のrequirements/AC/ST索引を検証してからタスク計画を出力
python3 evaluation/task_plan_gate.py <phase>/task-plan.yaml --system-traceability <phase>/system-traceability.yaml
python3 evaluation/render_task_plan.py <phase>/task-plan.yaml --output <phase>/implementation-task-plan.md

# 共通（閲覧用HTML）: phase配下の各func-*/とphase共通テストを走査し、4つのHTMLへ統合
python3 evaluation/render_html_views.py <phase>
python3 evaluation/render_html_views.py <phase> --check
```

通常実行は `views/` を生成・更新する。`--check` はファイルを書き換えず、生成対象の欠落・正本との差分・不要な旧派生物・未記入の読者向け本文があれば非0で終了し、それらを表示する。まだ作られていない工程の文書はエラーにせずスキップするが、スキップ対象自体は表示しない。

## 6. HTMLビューの位置づけと閲覧方法

`views/` は人が読みやすく確認するための派生物であり、**正本はMarkdown/YAMLのまま**とする。HTMLを手編集せず、正本の読者向け本文を直して再生成する。品質ゲートは正本の監査用付録とYAMLを検証し、レンダラは監査用付録をHTMLへ出さない。

- `00_サマリ.html`は全funcの目的・決定・未決・リスクをまとめ、最初に読む入口にする。
- `01_要件定義書.html`は全funcの読者向け要件本文をまとめる。記入ガイド、FILLマーカー、監査用項目、根拠付録は表示しない。
- `02_設計書.html`は基本・詳細設計を一枚へまとめる。シーケンス、ER、RDBのDDLまたはNoSQLのコレクション・インデックス・ルール設計へ直接移動できるようにする。
- `03_テストケース.html`は全funcのUT/ITとphase共通のSTをまとめる。
- `画面モック.html`は画面がある場合だけscreen-mockが生成する。共有HTMLレンダラは変更・削除しない。
- 監査用の要件・設計トレーサビリティは正本YAMLと派生Markdownで確認する。内容を再掲した単独HTMLは作らない。
- 各HTMLは外部CDN、外部フォント、追跡コード、ネットワーク通信に依存しない単一ファイルとする。
- 入力中のraw HTML、`script`、イベント属性、危険なURLは実行可能な形で出力しない。

Obsidianではデスクトップ版に [Local HTML Embed](https://obsidian.md/plugins?id=local-html-embed) を導入し、Vaultルートからの相対パスを `html-embed` コードブロックへ1行で指定する。

````markdown
```html-embed
docs/spec/phase-1_公開サイト・予約/views/00_サマリ.html
```
````

このプラグインは埋め込んだHTML内のスクリプト実行を許すため、**自分で生成した信頼済みHTMLだけ**を開く。現時点ではデスクトップ限定であり、モバイルでは正本Markdownを読む。プラグインを導入しない場合は `views/00_サマリ.html` を通常のブラウザで開く。

## 7. `.feature` の位置づけ

**標準で生成し phase直下の `features/` に置く**（KEIGO 決定）。将来 Cucumber / playwright-bdd で自動テスト（E2E）を回す前提。
`.feature` は `system-traceability.yaml`（phase直下）の受入試験（AC）から自動生成される派生物であり、手で保守しない（正本は YAML）。業務フロー・受入試験は機能をまたぐことが多いため、func単位では生成しない（§3参照）。

## 8. system-baseline（フェーズ横断の共通書類）

特定フェーズに属さない、システム全体で共通の土台を置く:

- `システム構成・共通基盤.md` … 全フェーズ共通の構成・基盤方針
- `非機能ベースライン.md` … 全フェーズ共通の非機能の基準値（可用性・性能・セキュリティ等の下限）
- `共通用語.md` … 共通の開発用語は `GLOSSARY.md` を正とし、ここはプロジェクト共通語の導線

## 9. なぜ「同じ内容」が複数ファイルに出るのか（設計意図の記録）

`.feature`・`system-test-cases.md`・`requirements-traceability.md` は、いずれも `system-traceability.yaml`（正本、phase直下。全funcの`traceability.yaml`を`func_traceability`で束ねて横断参照する）から生成する機械・監査向け成果物である。人向け`views/`では同じ対応表を単独HTMLにせず、判断に必要なサマリ・要件・設計・テストへ統合する。

| ビュー | 読み手・道具 |
| --- | --- |
| `func-<名前>/traceability.yaml` | 正本（機械）。US・要件 |
| `system-traceability.yaml` | 正本（機械）。業務フロー・AC・ST |
| `01_要件定義書.md` | ステークホルダー（物語） |
| `features/*.feature` | テスト自動化ツール（実行用） |
| `tests/system-test-cases.md` | テスト担当者（手順書） |
| `tests/requirements-traceability.md` | 監査（抜け漏れ・影響のマトリクス） |
| `views/00〜03_*.html` | 人がブラウザまたはObsidianデスクトップで読む、phase単位に統合した派生ビュー |
