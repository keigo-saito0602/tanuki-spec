# sample-user-story

レッスン予約・キャンセルのユーザーストーリーから生成したサンプルです。
従来のフラット配置は回帰テストとの互換性のため残し、HTMLビューは標準フェーズ構成の
[`phase-1_レッスン予約/views/index.html`](./phase-1_レッスン予約/views/index.html)
から確認できます。

HTMLビューを再生成・検証する場合は、リポジトリルートで次を実行します。

```bash
python3 tanuki-spec-all/evaluation/render_html_views.py \
  "tanuki-spec-generator/examples/sample-user-story/phase-1_レッスン予約"
python3 tanuki-spec-all/evaluation/render_html_views.py \
  "tanuki-spec-generator/examples/sample-user-story/phase-1_レッスン予約" --check
```
