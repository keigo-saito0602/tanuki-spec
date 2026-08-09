# 画面モックHTMLの出力契約

生成物は配布可能な単一の `.html` ファイルとする。
`scripts/validate_screen_mock.py` がこの契約を機械的に検証する。

## 生成方法

モデルはHTMLとCSSを書かない。`screens.yaml` と `design-tokens.json` だけを書き、
`scripts/render_screen_mock.py` が `assets/screen-mock.html` と合成する。
CSS・レスポンシブ設定・モード切替は再生成しない。

## 必須構造

- `<!doctype html>`、`<html lang="ja">`
- UTF-8、viewport、CSP、意味のある `title`
- `h1` は1件。見出しレベルを飛ばさない
- 各画面は `<section class="screen" id="SC-xxx">`。idが無いとアンカー遷移が動かない

## 自己完結と安全

- CSSはHTML内の `style` へ置く
- 外部CSS・外部フォント・外部JavaScript・外部画像・iframe・object・embed を使わない
- **JavaScriptは外部・インラインを問わず一切使わない。`<script>` 要素とイベント属性を出力しない**
- 画像が必要ならdata URIへ埋め込む。HTML/CSSで表現できる場合は画像を増やさない
- CSPの基本値:

```text
default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:; base-uri 'none'; form-action 'none'
```

- 入力由来の文字列はエスケープし、そのままDOMへ挿入しない
- モックのフォームは送信されない。`form-action 'none'` で担保する

## レスポンシブ

- 320 CSS px で本文を横スクロールなしに読める
- `box-sizing: border-box`、画像は `max-width: 100%`
- 表の横スクロールは表のコンテナ内だけに限定する
- モバイルでは複数カラムを1カラムにする
- タップ対象は44px以上

## 配色

- 通常文字は背景と4.5:1以上
- 状態は色だけでなく文字・境界線・形を併用する
- 印刷やグレースケールでも意味が残る

## 動作の前提

画面切替とモード切替はCSSだけで行う。`:target` と `:has()` を使うため、
Chrome 105以降・Safari 15.4以降・Firefox 121以降で開く。

## 完了条件

1. `python3 scripts/validate_screen_mock.py <出力HTML>` が成功する
2. デスクトップ幅・320px幅・印刷プレビューで目視確認する
3. 外部依存なしでHTMLを直接開ける
4. すべての遷移ボタンが対応する画面へ移動する
