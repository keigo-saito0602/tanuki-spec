# 仕様書ディレクトリ標準（正本）

tanuki スキル群が生成する仕様書・設計書・テスト・トレーサビリティを、**フェーズ単位**で一貫した場所・命名に置くための標準。
各スキルの「出力」節と `FLOW.md` は、この標準に従う。

作成: 2026-07-18 ／ 状態: ドラフト（KEIGO レビュー待ち）／ ブランチ: `feat/spec-dir-layout`

---

## 1. レイアウト

```text
docs/spec/
├── phase-<N>_<フェーズ名>/            # 例: phase-1_公開サイト・予約
│   ├── README.md                     # フェーズの索引（目的・成果物リンク・状態）
│   ├── 00_サマリ.md                   # サマリ層（generator・要件定義のみ）
│   ├── 01_要件定義書.md               # generator（要件定義）
│   ├── 02_基本設計書.md               # design（基本設計）
│   ├── 03_詳細設計書.md               # design（詳細設計）
│   ├── traceability.yaml              # 要件の正本（US→BR/FR/NFR→AC→ST）
│   ├── screens.yaml                   # 画面定義の正本（screen-mock・画面のある案件のみ）
│   ├── design-tokens.json             # デザイントークンの正本（screen-mock）
│   ├── design-traceability.yaml       # 設計の正本（要件↔BD/DD）
│   ├── test-traceability.yaml         # テストの正本（UT/IT↔設計・要件）
│   ├── features/
│   │   └── <feature名>.feature        # Gherkin（自動テスト用・標準で生成）
│   ├── tests/
│   │   ├── 04_テスト項目書.md          # UT/IT/V字カバレッジを1本に統合
│   │   ├── system-test-cases.md       # ST（システムテスト項目）
│   │   ├── requirements-traceability.md
│   │   └── design-traceability.md
│   ├── views/                         # 閲覧用HTML（派生物、浅い1階層）
│   │   ├── index.html                 # 読む順番と正本への入口
│   │   ├── README.md                  # 閲覧・再生成・安全上の注意
│   │   ├── 00_サマリ.html             # 対応するMarkdownがある場合だけ生成
│   │   ├── 01_要件定義書.html
│   │   ├── 画面モック.html             # screen-mockが生成（対応するMarkdownを持たない）
│   │   ├── 02_基本設計書.html
│   │   ├── 03_詳細設計書.html
│   │   ├── 04_テスト項目書.html
│   │   ├── requirements-traceability.html
│   │   ├── design-traceability.html
│   │   └── system-test-cases.html
│   └── reports/
│       └── 01_差分・未決事項.md        # 未決事項・要確認・差分追従の影響範囲・レビュー要約
└── system-baseline/                   # フェーズに依らない共通書類
    ├── README.md
    ├── システム構成・共通基盤.md
    ├── 非機能ベースライン.md
    └── 共通用語.md                     # 共通用語は GLOSSARY.md を正とし、ここは導線
```

## 2. 命名規則

- サマリ層は `00_サマリ.md`。連番の先頭に置き、「まずこれを読む」を名前で示す。要件定義書のぶんだけ作る（設計書は読み手が第三者技術者のため、フル文書を読ませる）。
- フェーズフォルダ: `phase-<番号>_<日本語名>`（番号は着手順）。
- 人が読む主要文書は連番付き: `01_要件定義書` → `02_基本設計書` → `03_詳細設計書` → `04_テスト項目書`。読む順＝番号順。
- 正本 YAML は内容を表す固定名: `traceability.yaml` / `design-traceability.yaml` / `test-traceability.yaml`（フェーズ直下）。
- レンダラが出す派生 Markdown（表・テスト項目）は固定名のまま `tests/` に置く。
- 閲覧用HTMLは正本Markdownと派生Markdownに対応する名前で `views/` 直下に置く。HTML用のCSS・JavaScript・画像フォルダは作らない。
- `features/` の `.feature` はレンダラが付ける名前のまま。

## 3. どのスキルの生成物がどこへ行くか（対応表）

| 生成物（スキル） | 置き場所・名前 |
| --- | --- |
| サマリ層（generator） | `00_サマリ.md` |
| 記入済み要件定義書（generator） | `01_要件定義書.md` |
| 基本設計書 / 詳細設計書（design） | `02_基本設計書.md` / `03_詳細設計書.md` |
| `traceability.yaml`（generator） | フェーズ直下 |
| `design-traceability.yaml`（design） | フェーズ直下 |
| `test-traceability.yaml`（test-item） | フェーズ直下 |
| `screens.yaml`・`design-tokens.json`（screen-mock） | フェーズ直下 |
| `requirements-traceability.md`・`system-test-cases.md`（generator） | `tests/` |
| `design-traceability.md`（design） | `tests/` |
| UT/IT/V字カバレッジ（test-item） | **`tests/04_テスト項目書.md` に1本統合**（下記§4） |
| `*.feature`（generator） | `features/`（標準で生成） |
| 閲覧用HTML（generator / design / test-item） | `views/`（正本ではない。対応する文書があるものだけ生成） |
| 画面モックHTML（screen-mock） | `views/画面モック.html`（正本ではない。`render_screen_mock.py`が生成し、共有レンダラは触らない） |
| 要確認・未決事項・差分影響・レビュー要約 | `reports/01_差分・未決事項.md` |
| （新規・各スキルが追記） | `README.md`（フェーズ索引） |

## 4. テスト項目書の統合（04_テスト項目書.md）

test-item の単体・結合・V字カバレッジは、**1本の `04_テスト項目書.md`** にまとめる。見出しで分ける:

```markdown
# テスト項目書
## 単体テスト（UT）
## 結合テスト（IT）
## V字モデルカバレッジ
```

※ `system-test-cases.md`（ST）は性質が違う（システム全体の受入寄り）ため、統合せず `tests/` に別置き。
※ test-item スキルは現在「設計のみ」。この統合形は**実装時の出力仕様**として定義しておく（今はレンダラ未実装）。

## 5. レンダラ呼び出し規約

入力の正本 YAML はフェーズ直下、出力先はサブフォルダを `--output-dir` で指定する。

```bash
# generator（要件）: 対応表とテスト項目書ビューは tests/、feature は features/ へ
python3 evaluation/render_traceability_docs.py  <phase>/traceability.yaml --output-dir <phase>/tests
python3 evaluation/render_feature_files.py      <phase>/traceability.yaml --output-dir <phase>/features

# design（設計）: 設計対応表は tests/ へ
python3 evaluation/render_design_traceability_docs.py <phase>/design-traceability.yaml --output-dir <phase>/tests

# 共通（閲覧用HTML）: フェーズ内に存在する文書だけを views/ へ生成
python3 evaluation/render_html_views.py <phase>
python3 evaluation/render_html_views.py <phase> --check
```

通常実行は `views/` を生成・更新する。`--check` はファイルを書き換えず、欠落または正本とのずれがあれば非0で終了する。まだ作られていない工程の文書はエラーにせずスキップし、生成・スキップ対象を表示する。

## 6. HTMLビューの位置づけと閲覧方法

`views/` は人が読みやすく確認するための派生物であり、**正本はMarkdown/YAMLのまま**とする。HTMLを手編集せず、正本を直して再生成する。品質ゲートとトレーサビリティも従来どおりMarkdown/YAMLを検証する。

- `views/index.html` は「サマリ → 要件 → 設計 → テスト・対応表」の読む順番、各文書の役割、正本へのリンク、未決事項への導線を示す。
- `views/README.md` はHTMLとの対応、再生成コマンド、Obsidianとブラウザの閲覧手順を示す。
- 各HTMLは外部CDN、外部フォント、追跡コード、ネットワーク通信に依存しない単一ファイルとする。
- 入力中のraw HTML、`script`、イベント属性、危険なURLは実行可能な形で出力しない。

Obsidianではデスクトップ版に [Local HTML Embed](https://obsidian.md/plugins?id=local-html-embed) を導入し、Vaultルートからの相対パスを `html-embed` コードブロックへ1行で指定する。

````markdown
```html-embed
docs/spec/phase-1_公開サイト・予約/views/index.html
```
````

このプラグインは埋め込んだHTML内のスクリプト実行を許すため、**自分で生成した信頼済みHTMLだけ**を開く。現時点ではデスクトップ限定であり、モバイルでは正本Markdownを読む。プラグインを導入しない場合は `views/index.html` を通常のブラウザで開く。

## 7. `.feature` の位置づけ

**標準で生成し `features/` に置く**（KEIGO 決定）。将来 Cucumber / playwright-bdd で自動テスト（E2E）を回す前提。
`.feature` は `traceability.yaml` の受入試験（AC）から自動生成される派生物であり、手で保守しない（正本は YAML）。

## 8. system-baseline（フェーズ横断の共通書類）

特定フェーズに属さない、システム全体で共通の土台を置く:

- `システム構成・共通基盤.md` … 全フェーズ共通の構成・基盤方針
- `非機能ベースライン.md` … 全フェーズ共通の非機能の基準値（可用性・性能・セキュリティ等の下限）
- `共通用語.md` … 共通の開発用語は `GLOSSARY.md` を正とし、ここはプロジェクト共通語の導線

## 9. なぜ「同じ内容」が複数ファイルに出るのか（設計意図の記録）

`.feature`・`system-test-cases.md`・`requirements-traceability.md` は、いずれも `traceability.yaml`（正本）から**自動生成した別ビュー**であり、手で二重に書いていない。読み手・道具ごとに最適な見せ方をしているだけで、正本を1か所直せば全ビューが追従する。

| ビュー | 読み手・道具 |
| --- | --- |
| `traceability.yaml` | 正本（機械） |
| `01_要件定義書.md` | ステークホルダー（物語） |
| `features/*.feature` | テスト自動化ツール（実行用） |
| `tests/system-test-cases.md` | テスト担当者（手順書） |
| `tests/requirements-traceability.md` | 監査（抜け漏れ・影響のマトリクス） |
| `views/*.html` | 人がブラウザまたはObsidianデスクトップで読む派生ビュー |
