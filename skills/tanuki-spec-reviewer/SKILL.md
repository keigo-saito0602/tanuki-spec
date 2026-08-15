---
name: tanuki-spec-reviewer
description: Use when independently reviewing a generated requirements or design specification before implementation, including AI quality review and DoD judgment.
---

# tanuki-spec-reviewer

> 🚀 **30秒でわかる**: できあがった仕様書を別の視点で点検し、抜けや矛盾を洗い出して「これで進めてよいか」を判定する。作り始める前の最終チェック役。

> 📖 わからない用語は [用語集（GLOSSARY.md）](../../GLOSSARY.md) を参照。

## 起動テンプレート

```text
tanuki-spec-reviewer
対象仕様書:      # レビューする記入済み.mdのパス
トレーサビリティ: # 対応する traceability.yaml のパス
設計トレーサビリティ: # 設計工程のみ design-traceability.yaml のパス
モード: # requirements / basic_design / detailed_design / unit_test / integration_test / phase_integration
reviewer:        # 例: codex / claude-new-session。生成担当と別であること
```

## 手順

1. 対象仕様書を独立した目で読み、生成側の意図・根拠欄を鵜呑みにせず検証する。
2. `python3 evaluation/traceability_gate.py <phase>/func-<名前>/traceability.yaml`を実行し、US・要件の孤立またはリンク切れがないことを確認する（業務フロー手順・受入試験・システムテストはphase単位のため、ここでは検証しない。`phase_integrationモード`の`system_traceability_gate.py`が担う）。`basic_design`／`detailed_design`では続けて`python3 evaluation/design_traceability_gate.py <design-traceability.yaml>`を実行し、対象要件が設計要素で被覆されていることを確認する。`<phase>/func-<名前>/00_サマリ.md`があれば`python3 evaluation/view_gate.py <phase>/func-<名前>/00_サマリ.md --traceability <phase>/func-<名前>/traceability.yaml --system-traceability <phase>/system-traceability.yaml`も実行し、サマリ層が正本からズレていないことを生成側とは独立に再確認する（IDの実在性・網羅性・状態一致のみ。文章表現は見ない）。
3. `evaluation/ai-quality-rubric.md §2④`の6軸を`PASS`、`要改善`、`判断不可`で判定する。
4. `python3 evaluation/coverage.py <対象仕様書> --json`を実行し、`required_coverage`、`overall_coverage`、`todo_flags`を控える。値は出力JSONの`required_coverage`、`coverage`、`confirmation_needed`からそれぞれ転記する。
5. `review.schema.json`に沿って、`date`、`target`、`reviewer`、`generated_spec_sha256`、`traceability_sha256`、`traceability_gate_passed`、`coverage`、`rubric`、`dod_passed`を持つYAMLを作る。設計工程では`design_traceability_sha256`と`design_traceability_gate_passed: true`も必須。各SHA-256は`shasum -a 256 <対象ファイル>`で算出する。
6. `python3 evaluation/validate_review.py <review.yaml> --spec <対象仕様書> --traceability <traceability.yaml>`を実行する。設計工程は`--design-traceability <design-traceability.yaml>`も付け、記録の整合性を確認する。
7. 評価レポートを作る場合は、`templates/review-context-template.yaml`を案件ディレクトリへコピーして特性を記入し、次を順に実行する。スクリプトは採点せず、独立したレビュー担当が雛形の`status`・`evidence`・`reason`・`recommended_action`を記入する。
   ```bash
   python3 evaluation/evaluate_review_items.py --emit-skeleton <review.yaml> --context <review-context.yaml> --rules templates/review-rules.yaml --in-place
   # 独立したレビュー担当が item_results を採点する
   python3 evaluation/evaluate_review_items.py --aggregate <review.yaml> --context <review-context.yaml> --rules templates/review-rules.yaml --traceability <traceability.yaml> --design-traceability <design-traceability.yaml> --in-place
   python3 evaluation/render_quality_evaluation.py <review.yaml> --out <quality-evaluation.md>
   python3 evaluation/evaluate_review_items.py --write-report-hash <review.yaml> --report <quality-evaluation.md> --in-place
   ```
   `quality-evaluation.md`は手編集せず再生成する。`report_sha256`、人間承認、`dod_passed`は本文へ出力しないため、ハッシュの循環を起こさない。
8. DoD判定と、要改善・判断不可が残った軸をユーザに報告する。
9. 機械判定に加えて人間レビューを行う場合は、[references/human-review-guide.md](./references/human-review-guide.md) の「2パス読み＋PBR＋節別チェック」に従う。非技術者（要件）または第三者技術者（設計）が、Pythonを実行せずに網羅性と品質を確認できる。
10. 対象文書の読みやすさを [`references/cognitive-doc-principles.md`](./references/cognitive-doc-principles.md) で採点する。「文レベルの規範」「語彙の規範」の違反箇所と、なめらかな断定で未決事項を埋めている箇所を指摘する。レビュー所見自体も同じ規範で点検して出力する。

## phase_integrationモード（phase単位の業務フロー・AC・ST・共有画面・タスク計画）

func単位のレビュー（要件・設計・UT/IT）とは別に、phase直下の構造化YAML成果物を対象にする。
対象は散文の仕様書ではないため、`coverage.py`と6軸ルーブリックは使わない。
次のコマンドはすべて`skills/tanuki-spec-reviewer/`を起点に実行する。

1. `python3 evaluation/system_traceability_gate.py <phase>/system-traceability.yaml`を実行し、
   通過を確認する。
2. `<phase>/task-plan.yaml`がある場合は
   `python3 ../tanuki-task-planner/evaluation/task_plan_gate.py <phase>/task-plan.yaml --system-traceability <phase>/system-traceability.yaml`
   を実行し、通過を確認する（`task_plan_gate.py`は`tanuki-task-planner`スキル固有のスクリプトで、
   reviewer側にはsymlinkしない）。
3. `<phase>/screens.yaml`がある場合は
   `python3 ../tanuki-spec-screen-mock/scripts/screens_gate.py <phase>/screens.yaml`を実行し、
   通過を確認する（同様に`tanuki-spec-screen-mock`固有のスクリプト）。
4. 次の記録を`<phase>/reports/`配下へ保存する。`coverage`・`rubric`は持たない。

```yaml
phase_integration_review:
  date: "YYYY-MM-DD"
  target_phase: "<phase>"
  reviewer: {role: reviewer, model: "モデル名", independent: true}
  system_traceability_sha256: "<system-traceability.yamlのSHA-256>"
  system_traceability_gate_passed: true
  task_plan_sha256: "<task-plan.yamlのSHA-256、無ければ省略>"
  task_plan_gate_passed: true
  screen_contract_passed: true   # screens.yamlが無い案件では省略
  notes: "<機械では判定できない所見。AC/STが機能をまたいで意味の通る検証になっているか等>"
```

各SHA-256は`shasum -a 256 <対象ファイル>`で算出する。

## 出力

> 置き場所・命名は [`../../docs/spec-directory-standard.md`](../../docs/spec-directory-standard.md) に従う（フェーズ別レイアウト）。

- func単位のレビュー（`requirements`／`basic_design`／`detailed_design`／`unit_test`／`integration_test`）: `<phase>/func-<名前>/reports/01_差分・未決事項.md`（検証済みの`ai_quality_review` YAML、レビュー要約、人間可読な採点サマリ）
- `phase_integration`モード: `<phase>/reports/`配下（`phase_integration_review`の記録。上記のfunc単位とは別ファイル）
