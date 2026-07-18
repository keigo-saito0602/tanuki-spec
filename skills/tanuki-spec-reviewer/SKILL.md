---
name: tanuki-spec-reviewer
description: Use when independently reviewing a generated requirements or design specification before implementation, including AI quality review and DoD judgment.
---

# tanuki-spec-reviewer

> 📖 わからない用語は [用語集（GLOSSARY.md）](../GLOSSARY.md) を参照。

## 起動テンプレート

```text
tanuki-spec-reviewer
対象仕様書:      # レビューする記入済み.mdのパス
トレーサビリティ: # 対応する traceability.yaml のパス
設計トレーサビリティ: # 設計工程のみ design-traceability.yaml のパス
reviewer:        # 例: codex / claude-new-session。生成担当と別であること
```

## 手順

1. 対象仕様書を独立した目で読み、生成側の意図・根拠欄を鵜呑みにせず検証する。
2. `python3 evaluation/traceability_gate.py <traceability.yaml>`を実行し、US・業務フロー手順・要件・受入試験・システムテストの孤立またはリンク切れがないことを確認する。`basic_design`／`detailed_design`では続けて`python3 evaluation/design_traceability_gate.py <design-traceability.yaml>`を実行し、対象要件が設計要素で被覆されていることを確認する。
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

## 出力

- 検証済みの`ai_quality_review` YAML
- 人間可読な採点サマリ
