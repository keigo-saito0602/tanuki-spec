---
name: tanuki-spec-generator
description: 案件着手時に、ユーザーストーリーから要件定義書・基本設計書・詳細設計書の根拠付きドラフトを作成し、抜け漏れと未確定事項を検証する。要件定義書作成、設計書のテンプレート記入、仕様の抜け漏れ確認、カバレッジ測定で使う。
---

# tanuki-spec-generator — 品質項目ベースの仕様書ジェネレーター

> 🚀 **30秒でわかる**: やりたいことをざっくり話すだけで、抜け漏れを点検した「要件定義書・設計書のたたき台」が返ってくる。案件の最初、土台づくりの一手。

> 📖 わからない用語は [用語集（GLOSSARY.md）](../../GLOSSARY.md) を参照。

ざっくりしたユーザーストーリーを入力に、**品質項目マスター（SSOT）に基づく穴埋めテンプレート**へドラフトを生成し、
**カバレッジ評価**（項目の充足度）と出力ゲートを実行する。抜け漏れのない要件定義・設計のドラフトを用意するのが目的。

- 項目の正本: `spec-items.yaml`（要件定義30／基本設計27／詳細設計18。要件定義・基本設計では非機能35明細も個別評価、AI品質は別評価）
- 既存の `dev-workflow` / `kiro:spec-*` との棲み分け → 末尾「他スキルとの関係」参照
- 使い方の全体像（ユーザ/Claude/Codexの役割分担）→ [`../../FLOW.md`](../../FLOW.md)

---

## 起動時テンプレート（呼ばれたら、まずこれを出す）

このSKILLが呼び出されたら、**最初に次のテンプレートをそのまま提示し、ユーザーに埋めてもらう**。

```
tanuki-spec-generator
工程:            # requirements（要件定義）/ basic_design（基本設計）/ detailed_design（詳細設計）
対象func:        # phase内の機能名（例: 予約）。出力先 <phase>/func-<名前>/ の <名前> になる
ストーリー:      # 誰が/いつ/何を/なぜ、のユーザーストーリー群
参照仕様:        # 過去仕様から今回使う内容の抜粋。無ければ空欄
モード:          # full（既定・全項目＋評価）/ quick（必須のみ＋簡易）。空欄ならfull
```

`工程`・`対象func`・`ストーリー` が未記入のうちは生成を始めない（`参照仕様`・`モード` は空でよい）。

埋まったら、下の「手順」①〜③を順に実行する。

---

## 入力パラメータ

| パラメータ | 必須 | 説明 |
| --- | --- | --- |
| ユーザーストーリー | ○ | 「誰が/いつ/何を/なぜ」レベルの要望。複数ある場合は分けて列挙する |
| 対象工程 | ○ | `requirements`（要件定義）/ `basic_design`（基本設計）/ `detailed_design`（詳細設計） |
| 対象func | ○ | phase内の機能名。出力先 `<phase>/func-<名前>/` の `<名前>` になる |
| 参照仕様（過去案件） | 任意 | **都度指定**。今回採用したい仕様本文・画面説明・制約・判断理由の抜粋を渡す。原本のパス・ファイル名は渡さない |
| モード | 任意 | `full`（全項目・カバレッジ＋AI品質評価）/ `quick`（必須項目のみ・簡易チェック）。既定 `full` |

> 参照仕様は固定しない設計。案件ごとに必要な内容だけを指定して使う。

---

## 手順（この順で実行する）

0. 入力として渡された`<phase>`から`docs/spec/system-baseline/`を解決する
   （カレントディレクトリ基準ではなく、`<phase>`の親を辿って解決する）。存在する場合は
   `システム構成・共通基盤.md`・`非機能ベースライン.md`を読み、記載と矛盾しない内容にする。
   共通用語は`GLOSSARY.md`を正とする。存在しない場合はこのステップを省略する
   （初回フェーズ等でまだ作られていないことがある）。
   参照した場合は、`reports/01_差分・未決事項.md`に「参照したベースライン文書」を記録する。

### ①入力ゲート — ユーザーストーリーの INVEST チェック
INVESTの6軸（Independent/Negotiable/Valuable/Estimable/Small/Testable）をYES/NOで確認。
NOの軸は質問リストにして仕様書へ残す。ドラフト生成は止めないが、根拠がない項目を埋めてはいけない。

ユーザーの要望が一文にまとまっている場合は、利用者・したいこと・得たい価値・通常/例外時の流れを質問し、独立した `US-xxx` へ分割してから②へ進む。
開発初期は、`templates/product-backlog-template.md` を使ってUS・優先度・リリース単位を整理してから開始する。

**振る舞いの洗い出し（BDD発見・軽量）**: 各USについて正常系・異常系・境界値の振る舞いを洗い出す。「ルール→具体例→疑問」（Example Mapping風）で広げ、ビジネス/開発/QA の3視点（疑似Three Amigos）で「本当にこれで正しいか」を自問する。洗い出した振る舞いは②でGherkinの受入試験(AC)になる。

### ②穴埋め生成
1. `spec-items.yaml` の対象工程の項目と、`templates/<工程>-template.md` を読む。
   - **各項目の記入ガイド・出典・品質観点は、テンプレート末尾の「付録: 項目の根拠一覧」に表として集約されている**。読み手の認知負荷を下げるため本文から外しているだけで、記入に必要な情報はすべてそこにある。**記入前に必ず付録の該当ID行を読み、ガイドと記入形式に沿って記入する**。
   - テンプレは `python3 evaluation/generate_templates.py` でSSOTから再生成できる（手で編集せずSSOTを直す）。
2. `templates/traceability-template.yaml` をコピーして `traceability.yaml` を作る。ユーザーストーリーと業務フロー手順に `US-xxx` / `BF-xxx-Sxx` を付け、次をすべて洗い出す。
   - 業務要件・機能要件・非機能要件は `BR-xxx` / `FR-xxx` / `NFR-xxx` とし、各要件に `user_story_ids` と `flow_step_ids` を必ず指定する。
   - 受入試験は `AC-xxx` とし、対象US・要件・業務フロー手順を指定し、`scenario`（name/given/when/then、任意でexamples）にGherkinで振る舞いを書く。書き方は共有コアの `references/ears-gherkin-guidelines.md` に従う（1シナリオ1振る舞い・Thenは観測可能・プレースホルダ禁止）。
   - システムテストは `ST-xxx` とし、対象要件・受入試験・テスト種別・前提条件・操作・期待結果を指定する。
3. 各項目の `<!-- FILL:START id -->` … `END` の間を、ユーザーストーリー（＋参照仕様）から記入する。対応する `US-xxx` / `BR-xxx` 等を本文にも記載する。
4. **根拠・不確実性ルール（必須）**:
   - 実際に記入した各FILLブロックの先頭に、`- **根拠**: [入力] ユーザーストーリー US-xxx「<該当箇所>」` または `- **根拠**: [参照] 提供内容「<見出しまたは要点>」` を書く。
   - 根拠が無い項目は勝手に埋めず、`[要確認: <確認したい質問>]` を残す。これは充足ではない。
   - 過去仕様は現案件の事実ではないため、採用する場合はユーザの承認を得る。
5. `required: conditional` の項目は、該当しない場合のみ `[対象外: <適用しない理由>]` と記入する。理由なしの対象外は許可しない。

### ③カバレッジ評価（決定論・自動）
```bash
python3 evaluation/coverage.py <記入済み仕様書.md> --strict
```
→ 必須充足率・全体充足率・欠落項目・`[要確認]`が出る。`--json` で機械可読サマリ。
続けてトレーサビリティを検証し、受入試験項目書・システムテスト項目書を生成する。phase確定後は、業務フロー・AC・STを束ねる`system-traceability.yaml`（phase直下）側で一括生成する運用に変わる。
```bash
python3 evaluation/traceability_gate.py <traceability.yaml>
python3 evaluation/render_traceability_docs.py <phase>/system-traceability.yaml --output-dir <phase>/tests
python3 evaluation/render_feature_files.py <phase>/system-traceability.yaml --output-dir <phase>/features
```
最後に根拠とトレーサビリティを含む出力ゲートを実行する。
```bash
python3 evaluation/spec_gate.py <記入済み仕様書.md> --traceability <traceability.yaml>
```
必須の欠落、要確認、または孤立したUS・業務フロー手順・要件・試験項目があれば②へ戻る。絶対%は合否にせず「必須欠落ゼロ」と前回差分を見る。

③で出力ゲートを通過したら、レビューは別SKILL [`tanuki-spec-reviewer`](../tanuki-spec-reviewer/SKILL.md) に引き継ぐ。このSKILL自身では④⑤を実施しない。

`quick` モードでは、必須項目のみを生成・評価する。

### サマリ層を書く

出力ゲートを通過したら、人が普段読む `00_サマリ.md` を書く。

1. `spec-items.yaml` の `summary_view` を読み、節と順序を確認する。
2. `item_id` を持つ節は、記入済み仕様書の該当FILLブロックを**凝縮して書き直す**。本文をコピーしない。
3. `source: traceability` の節は `traceability.yaml` から表を起こす。`implementation_status` と `gap_severity` があれば列に含める。**1つの要件IDは状態を持つ表に1回だけ載せる**（`view_gate.py` は最初に見つけた表行で状態一致を判定するため、同じIDを複数の表行に書くと検査が曖昧になる）。
4. `- **根拠**:` は書かない。根拠は本論層（`01_要件定義書.md`）の責務。
5. 表の1セルは1行に収める。長くなるものは `note` へ逃がす。
6. 全体で100行程度に収める。超えたら節を減らすのではなく表へ畳む。
7. 文章は `tanuki-japanese-tech-writing` に従う。

書き終えたら整合を検証する。

```bash
python3 evaluation/view_gate.py <phase>/func-<名前>/00_サマリ.md --traceability <phase>/func-<名前>/traceability.yaml --system-traceability <phase>/system-traceability.yaml
python3 evaluation/render_html_views.py <phase>
python3 evaluation/render_html_views.py <phase> --check
```

`--system-traceability` は任意。サマリが業務フロー・受入試験・システムテストのIDにも言及する場合は指定する（省略するとAC/BF/STのID検証はスキップされる）。

**このゲートが見るのはIDの実在性・網羅性・状態一致の3つだけで、文章表現は一切検査しない。**書きぶり・言い回し・凝縮の仕方はAIの裁量に委ね、正本とのズレだけを機械が担保する設計（美しさはAI、網羅性は機械）。通過は文章品質の保証ではない。

**サマリ層はDoDの条件に含めない。**DoDの判定対象は本論層（`01_要件定義書.md`）のままであり、[`../../FLOW.md`](../../FLOW.md) ⑥のチェックリストに `view_gate.py` は加えない。層2だけ読んで層1が形骸化するのを防ぐため。

不通過なら、サマリではなく**正本のどちらが正しいかを判断してから**直す。サマリだけ辻褄を合わせない。

---

## 文章の点検（出力前）

サマリ層と本論層の散文を出力する前に、[`references/cognitive-doc-principles.md`](./references/cognitive-doc-principles.md) の「症状を二つに分ける」「文レベルの規範」「語彙の規範」「想起を組み込む規範」で自己点検する。

要件定義書の読み手は非技術者である。未決事項をなめらかな断定で埋めず、`[要確認]`として残す。判断が必要な箇所は、選択肢と判断基準を示して読み手の決定に残す。

---

## 出力

> 置き場所・命名は [`../../docs/spec-directory-standard.md`](../../docs/spec-directory-standard.md) に従う（フェーズ別レイアウト）。

- `<phase>/func-<名前>/00_サマリ.md`（サマリ層。人が普段読む100行程度。要件定義書のぶんだけ作る）
- `<phase>/func-<名前>/01_要件定義書.md`（記入済み要件定義書）
- `<phase>/func-<名前>/traceability.yaml`（US → BR/FR/NFR → AC → ST の正本）
- `<phase>/tests/requirements-traceability.md`、`<phase>/tests/system-test-cases.md`
- `<phase>/features/*.feature`（受入試験はGherkinの `.feature` として標準で生成。将来E2E（Cucumber/playwright-bdd）へ直接投入できる）
- `<phase>/views/00_サマリ.html`、`01_要件定義書.html`（全funcをphase単位で統合した、人向けの閲覧用HTML。正本ではなく再生成する派生物）
- `<phase>/func-<名前>/reports/01_差分・未決事項.md`（カバレッジ評価レポート：必須充足率／欠落リスト）

実例は `examples/sample-user-story/` を参照（サンプルストーリー1件のE2E成果物）。

---

## ファイル構成

```
tanuki-spec-generator/
├── SKILL.md                       ← このファイル（生成①〜③の正本）
├── spec-items.yaml                ← 共有コアへのsymlink
├── templates/                     ← 共有コアへのsymlink
├── evaluation/
│   ├── generate_templates.py      ← 共有コアへのsymlink
│   ├── coverage.py                ← 共有コアへのsymlink
│   ├── traceability_gate.py        ← US〜試験の孤立・リンク切れ検査
│   ├── render_traceability_docs.py ← 要件対応表・試験項目書の生成
│   ├── render_feature_files.py     ← 受入試験のGherkinから .feature を生成
│   ├── render_html_views.py        ← フェーズ内の文書から閲覧用HTMLを生成・検査
│   ├── spec_gate.py               ← 根拠・未確定事項を含む出力ゲート
│   └── run_harness.py             ← 共有コア＋生成側の回帰テスト
├── evals/cases.yaml               ← モデルを使う評価シナリオ
├── tests/                         ← 決定論部分の回帰テスト
├── references/
│   └── README.md                  ← 参照仕様の渡し方・出典の考え方
└── examples/
    └── sample-user-story/         ← E2Eサンプル
```

---

## 他スキルとの関係（棲み分け）

| スキル | 役割 | 本SKILLとの関係 |
| --- | --- | --- |
| `tanuki-spec-reviewer` | ④⑤の独立レビューとDoD判定 | ③後に引き継ぐ |
| `tanuki-spec-design` | 要件定義書起点の設計生成・設計変更追従 | 設計特化フローが必要な場合はこちらを推奨。既存の設計工程は維持する |
| `dev-workflow`（3フェーズ） | 解析→設計→実装の交通整理 | 設計フェーズの前段として併用 |
| `kiro:spec-*`（cc-sdd） | 仕様駆動の実装フロー | 本SKILLの出力を入力として渡せる |

> cc-sdd（Kiro系列）は「次フェーズ前に矛盾・曖昧・欠落を分析する品質ゲート」を持つ。本SKILLの③はその `analyze` 相当を、業務システム品質項目に特化して実装したもの。

---

## Codex から使う場合

素のファイル構成（Markdown＋YAML＋Python）なので、Codexからも同じ手順で実行できる。
リポジトリのルート（`AGENTS.md`）がこのSKILL.mdを指しているので、Codexは `AGENTS.md` → 本手順に従う。
Python依存は `requirements.txt` のみ。初回は `python3 -m pip install -r requirements.txt` を実行する。
