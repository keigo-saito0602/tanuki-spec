# レッスン予約 HTMLビュー

この `views/` は閲覧用の派生成果物です。正本は機能ごとに `func-<名前>/` 配下、
またはphase直下（業務フロー・AC・ST等）にあるMarkdown/YAMLです。HTMLを直接編集せず、
正本を直してから再生成してください。各HTMLは外部通信やJavaScriptを使わない単一ファイルで、
ブラウザでも開けます。

## 閲覧

- 入口は [index.html](./index.html) です。
- Obsidianデスクトップでは Local HTML Embed コミュニティプラグインを利用できます。
  ノートに次のように、コードブロック本文の1行目へVaultルート相対パスを書きます。

````markdown
```html-embed
<Vault内のphaseパス>/views/index.html
```
````

- Local HTML Embedはデスクトップ限定です。スクリプトを許可できる設定には安全上のリスクが
  あるため、信頼済みの生成HTMLだけを表示してください（このレンダラのHTMLはスクリプトを含みません）。
- プラグインを導入しない場合は、OSのファイル操作から `index.html` をブラウザで開いてください。
- コミュニティプラグインとローカルHTMLは、信頼できるVault・生成物だけで利用してください。

## 正本との対応

| HTMLビュー | 正本 | 役割 |
| --- | --- | --- |
| [01_要件定義書.html](./func-予約/01_要件定義書.html) | [01_要件定義書.md](../func-予約/01_要件定義書.md) | 実現する目的と要件を確認 |
| [requirements-traceability.html](./system/requirements-traceability.html) | [tests/requirements-traceability.md](../tests/requirements-traceability.md) | 要件間の対応を確認 |
| [system-test-cases.html](./system/system-test-cases.html) | [tests/system-test-cases.md](../tests/system-test-cases.md) | 要件とシステムテストの対応を確認 |

## 再生成と検証

リポジトリルートから実行します。

```bash
python3 tanuki-spec-all/evaluation/render_html_views.py "<phase>"
python3 tanuki-spec-all/evaluation/render_html_views.py "<phase>" --check
```

`--check` は書き換えず、欠落・古い内容・不要になった既知HTMLを検出します。
