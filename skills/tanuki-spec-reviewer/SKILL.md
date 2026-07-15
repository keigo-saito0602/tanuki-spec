---
name: tanuki-spec-reviewer
description: Use when independently reviewing a generated requirements or design specification before implementation, including AI quality review and DoD judgment.
---

# tanuki-spec-reviewer

## 起動テンプレート

```text
tanuki-spec-reviewer
対象仕様書:      # レビューする記入済み.mdのパス
reviewer:        # 例: codex / claude-new-session。生成担当と別であること
```

## 手順

1. 対象仕様書を独立した目で読み、生成側の意図・根拠欄を鵜呑みにせず検証する。
2. `evaluation/ai-quality-rubric.md §2④`の6軸を`PASS`、`要改善`、`判断不可`で判定する。
3. `python3 evaluation/coverage.py <対象仕様書> --json`を実行し、`required_coverage`、`overall_coverage`、`todo_flags`を控える。値は出力JSONの`required_coverage`、`coverage`、`confirmation_needed`からそれぞれ転記する。
4. `review.schema.json`に沿って、`date`、`target`、`reviewer`、`generated_spec_sha256`、`coverage`、`rubric`、`dod_passed`を持つYAMLを作る。SHA-256は`shasum -a 256 <対象仕様書>`で算出する。
5. `python3 evaluation/validate_review.py <review.yaml> --spec <対象仕様書>`を実行し、記録の整合性を確認する。
6. DoD判定と、要改善・判断不可が残った軸をユーザに報告する。

## 出力

- 検証済みの`ai_quality_review` YAML
- 人間可読な採点サマリ
