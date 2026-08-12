# tanuki-spec フロー（ユーザ / Claude / Codex の役割分担）

スキルを誰が・どの順で・何のために使うかをまとめた運用図。スキルの一覧は[SKILLS.md](./SKILLS.md)、起動テンプレートは[TEMPLATES.md](./TEMPLATES.md)にある。
生成物の置き場所・命名は[`docs/spec-directory-standard.md`](./docs/spec-directory-standard.md)に従う（フェーズ別`docs/spec/phase-<N>_.../`）。

要件定義書を入力に設計書を新規作成または追従更新する案件では、`tanuki-spec-design`をgeneratorと併存して使う。既存コード調査、確認質問、`design-traceability.yaml`の生成を担い、generatorの設計工程は変更しない。

DoDを通過した仕様書を実装タスクへ分解する案件では、`tanuki-task-planner`を⑦の前段に置く。`traceability.yaml`を入力に`task-plan.yaml`と実装タスク計画を作る。

UT/IT のテスト項目書と V 字カバレッジについては、設計工程の後に`tanuki-spec-test-item`を使う。既存の AC（受入試験）・ST（システムテスト）は`traceability.yaml`が正本のまま再定義しない。

---

## 全体像（1行）

> **ユーザが要望を出す → Claudeが品質項目に沿って仕様書を生成し決定論チェック → 別担当が品質採点 → ユーザがDoD判定 → Codexが実装する**

---

## スイムレーン（誰が何をするか）

| # | ステージ | ユーザ | Claude（設計/レビュー・生成側） | Codex（実装・採点側） |
|---|---|---|---|---|
| 0 | 起動 | 起動テンプレを埋める（工程・ストーリー・参照仕様・モード） | テンプレを提示。工程/ストーリーが埋まるまで生成しない | — |
| ① | 入力ゲート(INVEST) | Testable等の不足を補足 | INVEST 6軸をYES/NO判定。NOの軸は質問リスト化して仕様書に残す（生成は止めないが根拠なき記入はしない） | — |
| ② | 穴埋め生成 | 過去仕様の採用可否を承認 | `spec-items.yaml`＋テンプレを読み、各FILLに**根拠明記**で記入。根拠なし→`[要確認]`、条件外→`[対象外:理由]` | — |
| ③ | カバレッジ評価 | 結果を見る | `coverage.py --strict` → `spec_gate.py`。**必須欠落/要確認があれば②へ戻る** | — |
| ③.5 | 画面モック | **モックを確認し修正を依頼**（画面のある案件のみ） | `tanuki-spec-screen-mock`で`screens.yaml`・`design-tokens.json`・モックHTMLを生成 | — |
| ④ | 設計派生 | 設計に必要な未確定事項へ回答する | 必要に応じて`tanuki-spec-design`で設計書と`design-traceability.yaml`を生成する | — |
| ④.5 | テスト項目書 | テスト観点で必要な前提を回答する | `tanuki-spec-test-item`でUT/IT・`test-traceability.yaml`・V字カバレッジを生成する（設計工程を経た案件のみ） | — |
| ⑤ | AI品質採点 | — | （自己採点しない＝バイアス回避） | **別担当として6軸採点**＋`validate_review.py`で記録検証（または新しいClaudeセッションが採点） |
| ⑥ | 出力ゲート(DoD) | **最終判定**（下記条件） | 差し戻しがあれば該当ステージへ | — |
| ⑦ | 実装引き渡し | 進捗を見る | `tanuki-task-planner`でタスク分解 | **DoD通過の仕様書を入力に実装（TDD）** |

**⑤の採点は「生成した本人以外」が原則**（自己採点の甘さを防ぐ）。ユーザの分業では
**Codexに採点も兼ねさせる**（実装前の仕様レビューにもなる）か、**新しいClaudeチャットで採点**が手軽。

---

## ステップ詳細（コマンド付き）

### 0. 起動（ユーザ → Claude）
SKILLを呼ぶとClaudeが起動テンプレを出す。ユーザが埋める:
```
tanuki-spec-generator
工程: requirements
ストーリー: 生徒が空きレッスン枠をスマホから予約・キャンセルできるようにしたい
参照仕様:            # 今回使う内容の抜粋。無ければ空欄
モード: full
```

他スキルのテンプレートは[TEMPLATES.md](./TEMPLATES.md)にまとまっている。

### ①〜③ 生成と決定論チェック（tanuki-spec-generator）
```bash
# テンプレを最新化（SSOTを直した時のみ）
python3 evaluation/generate_templates.py

# 穴埋め後：カバレッジ評価 → トレーサビリティ検証 → 出力ゲート
python3 evaluation/coverage.py <記入済み.md> --strict
python3 evaluation/traceability_gate.py <traceability.yaml>
python3 evaluation/render_traceability_docs.py <traceability.yaml> --output-dir <phase>/tests
python3 evaluation/render_feature_files.py <traceability.yaml> --output-dir <phase>/features
python3 evaluation/spec_gate.py <記入済み.md> --traceability <traceability.yaml>
python3 evaluation/view_gate.py <phase>/00_サマリ.md --traceability <phase>/traceability.yaml
python3 evaluation/render_html_views.py <phase>
python3 evaluation/render_html_views.py <phase> --check
```
→ 必須欠落・`[要確認]`が残れば②に戻って埋め直す。

### ③.5 画面モック（tanuki-spec-screen-mock）
ユーザが操作する画面を伴う案件のみ実行する。要件の誤りを設計・実装へ持ち込む前に、画面構成・遷移・配色をブラウザで確認する。コマンドは`skills/tanuki-spec-screen-mock/`を起点に実行する:
```bash
python3 scripts/screens_gate.py <phase>/screens.yaml
python3 scripts/render_screen_mock.py <phase>/screens.yaml <phase>/design-tokens.json --output <phase>/views/画面モック.html
python3 scripts/validate_screen_mock.py <phase>/views/画面モック.html
python3 scripts/render_screen_docs.py <phase>/screens.yaml
```
最後のコマンドが出す画面一覧・遷移表を`02_基本設計書.md`の「画面一覧・画面遷移設計」へ貼る。ファイルは作らず、正本は`screens.yaml`のままにする。

### ④ 設計派生（tanuki-spec-design）
要件定義書から設計を起こす場合のみ実行する。基本設計・詳細設計と、要件↔設計の対応を作る:
```bash
python3 evaluation/coverage.py <基本設計書.md> --phase basic_design --strict
python3 evaluation/coverage.py <詳細設計書.md> --phase detailed_design --strict
python3 evaluation/design_traceability_gate.py <design-traceability.yaml>
python3 evaluation/render_design_traceability_docs.py <design-traceability.yaml> --output-dir <phase>/tests
python3 evaluation/render_html_views.py <phase>
python3 evaluation/render_html_views.py <phase> --check
```

### ④.5 テスト項目書（tanuki-spec-test-item）
設計工程（④）を経た案件で、UT/ITとV字カバレッジが必要な場合に実行する。コマンドは`skills/tanuki-spec-test-item/`を起点に実行する:
```bash
python3 evaluation/test_traceability_gate.py <test-traceability.yaml>
python3 evaluation/render_test_item_docs.py <test-traceability.yaml> --output-dir <phase>/tests
python3 evaluation/render_html_views.py <phase>
python3 evaluation/render_html_views.py <phase> --check
```
既存のAC（受入試験・UAT）・ST（システムテスト）は`traceability.yaml`が正本であり、`04_テスト項目書.md`のV字モデルカバレッジ節は参照表示するだけで再定義しない。

### 閲覧用HTMLビュー（各生成工程の完了時）

`render_html_views.py`は共有コアに1つだけ置き、generator / design / test-item がsymlink経由で呼び出す。通常実行はフェーズ内に存在する文書だけを`views/`へ生成し、`--check`は書き換えずに欠落・正本との差分を検出する。

HTMLは人が読むための派生物であり、正本はMarkdown/YAMLのまま変わらない。HTMLに修正が必要な場合も正本を直して再生成する。`views/index.html`はブラウザで直接開けるほか、ObsidianデスクトップではLocal HTML Embedを使って表示できる。構成、`html-embed`記法、安全上の注意は[`docs/spec-directory-standard.md`](./docs/spec-directory-standard.md)を参照する。

### ⑤ AI品質採点（tanuki-spec-reviewer／別担当）
`evaluation/ai-quality-rubric.md`の6軸（完全性/曖昧性/整合性/トレーサビリティ/実装可能性/根拠）を
PASS・要改善・判断不可で採点し、記録を検証:
```bash
python3 evaluation/validate_review.py <review.yaml> --spec <記入済み.md> --traceability <traceability.yaml>
```
設計工程では`--design-traceability <design-traceability.yaml>`も付ける。

**評価レポートを出す場合**（任意）。スクリプトは採点せず、雛形の`status`・`evidence`・`reason`・`recommended_action`は独立したレビュー担当が記入する:
```bash
python3 evaluation/evaluate_review_items.py --emit-skeleton <review.yaml> --context <review-context.yaml> --rules templates/review-rules.yaml --in-place
# レビュー担当が item_results を採点する
python3 evaluation/evaluate_review_items.py --aggregate <review.yaml> --context <review-context.yaml> --rules templates/review-rules.yaml --traceability <traceability.yaml> --design-traceability <design-traceability.yaml> --in-place
python3 evaluation/render_quality_evaluation.py <review.yaml> --out <quality-evaluation.md>
python3 evaluation/evaluate_review_items.py --write-report-hash <review.yaml> --report <quality-evaluation.md> --in-place
```
`quality-evaluation.md`は手編集せず再生成する。

**人間レビューを併用する場合**は[`skills/tanuki-spec-reviewer/references/human-review-guide.md`](./skills/tanuki-spec-reviewer/references/human-review-guide.md)の「2パス読み＋PBR＋節別チェック」に従う。非技術者（要件）または第三者技術者（設計）が、Pythonを実行せずに網羅性を確認できる。

### ⑥ 出力ゲート（DoD／ユーザ最終判定）
次を**すべて満たせば実装へ引き渡してよい**:
- [ ] 必須充足率100％（欠落ゼロ）
- [ ] `[要確認]`が残っていない
- [ ] `spec_gate.py` 通過
- [ ] `traceability_gate.py` 通過（US・業務フロー手順・要件・受入試験・システムテストに孤立がない）
- [ ] 設計工程では `design_traceability_gate.py` 通過（対象要件がBD/DDで被覆されている）
- [ ] テスト項目書を作る案件では `test_traceability_gate.py` 通過（BD/DDがUT/ITで被覆されている）
- [ ] `validate_review.py` 通過（レビュー記録が整合）
- [ ] 6軸に「要改善」なし
- [ ] 受入基準がテスト可能
- [ ] 受入基準がGherkin（Given/When/Then）で書かれ、`.feature` が生成できる

### ⑦ タスク分解と実装（tanuki-task-planner → Codex）
DoD通過後、実装タスクへ分解する:
```bash
python3 evaluation/task_plan_gate.py <task-plan.yaml> --traceability <traceability.yaml>
python3 evaluation/render_task_plan.py <task-plan.yaml> --output <implementation-task-plan.md>
```
Codexは`implementation-task-plan.md`と仕様書を入力に実装する。指示書の形に落とす工程は、このリポジトリの範囲外（別のリポジトリ側のスキル）で扱う。

---

## モード早見

| モード | 中身 | いつ |
|---|---|---|
| `full`（既定） | 全項目＋③⑤⑥フル | 新機能・重要案件 |
| `quick` | 必須項目のみ＋⑤は「完全性・根拠」2軸だけ | 小さな追加・下書き |

---

## Codexで動かすとき

リポジトリ直下の[`AGENTS.md`](./AGENTS.md) → 各スキルの`SKILL.md`の順に読む。
依存は各スキルの`requirements.txt`（初回`python3 -m pip install -r requirements.txt`）。
コマンドは各スキルディレクトリを起点に実行する。
中身はMarkdown＋YAML＋Pythonの素の構成なので、Claude Codeと同じ手順で動く。
