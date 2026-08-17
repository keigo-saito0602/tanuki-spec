# sample-user-story

レッスン予約・キャンセルのユーザーストーリーから生成したサンプルです。
func/phase再構成（2026-08-12設計）に対応済みで、要件・トレーサビリティ正本は
[`phase-1_レッスン予約/func-予約/traceability.yaml`](./phase-1_レッスン予約/func-予約/traceability.yaml)、
業務フロー・AC・STは
[`phase-1_レッスン予約/system-traceability.yaml`](./phase-1_レッスン予約/system-traceability.yaml)
にあります。root直下の`traceability.yaml`は`spec_gate`等の既存テストのために残した
func正本へのsymlinkです。HTMLビューは
[`phase-1_レッスン予約/views/01_要件定義書.html`](./phase-1_レッスン予約/views/01_要件定義書.html)
から確認できます（未着手工程のビューは生成されません）。

複数funcの構成例は[`phase-2_複数機能例/`](./phase-2_複数機能例/README.md)を参照してください。

HTMLビューを再生成・検証する場合は、リポジトリルートで次を実行します。

```bash
python3 tanuki-spec-all/evaluation/render_html_views.py \
  "tanuki-spec-generator/examples/sample-user-story/phase-1_レッスン予約"
python3 tanuki-spec-all/evaluation/render_html_views.py \
  "tanuki-spec-generator/examples/sample-user-story/phase-1_レッスン予約" --check
```
