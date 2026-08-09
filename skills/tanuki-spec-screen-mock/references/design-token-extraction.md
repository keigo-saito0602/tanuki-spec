# 参考ソースからのデザイントークン抽出

`design-tokens.json` は、画面モックのデザインモードで使う色・書体・余白の正本。
**値そのものより、その値をどこから得たかの記録が重要**。確度を偽ると「参考サイトの色を反映した」と
言いながら実は推測、という事故になる。

## 優先順位

上ほど正確。複数ある場合は上を採る。

| 順 | 入力 | `source` | `confidence` | 取れるもの / 取れないもの |
| --- | --- | --- | --- | --- |
| 1 | 既存コード（`tailwind.config` / CSS変数 / `theme.ts`） | `code` | `confirmed` | hex値をそのまま使える |
| 2 | スクリーンショット画像 | `screenshot` | `estimated` | 色・余白・階層は読めるが hex は目視推定 |
| 3 | URL | `url` | — | 構造・ナビ・情報設計は読める。**色は読めない** |
| 4 | なし | `principles` | `proposed` | `uiux-principles.md` の既定トークンを提案する |

## URLを渡された場合の注意

`WebFetch` はページをMarkdownへ変換して返すため、実際の配色やCSS変数は取得できない。
URLからは情報設計・ナビゲーション構造・文言だけを採用し、色は値を書かずに
`screens.yaml` の `notes` へ `[要確認: 参考サイトの主要色を指定してください]` を残す。
推測した色を `confirmed` として書かない。

## 必須の役割トークン

`color.primary` / `color.surface` / `color.text` / `color.line` / `color.accent` の5つは必ず定義する。
`color.text` と `color.surface`、`color.accent` と `color.surface` はコントラスト4.5:1以上でなければ検証に落ちる。

## 検証

```bash
python3 -c "import json,sys; sys.path.insert(0,'scripts'); import tokens; \
  print(tokens.validate_tokens(json.load(open('<phase>/design-tokens.json'))))"
```

確度が `confirmed` でないトークンは、モックHTMLの「確定していないデザイントークン」表へ自動的に載る。
