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
- 各画面にはデザイン探索カードを表示し、`design_question`・`hypothesis`・`risk`・`validation_task`・`rationale`・重点状態・代替案の採否理由をレビューできること

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

## 状態表現部品のマーク契約（data-state）

`component-catalog.yaml` の `state_required`（`empty-state` / `alert` / `loading`）に
挙がる部品は、`screens.yaml` の `blocks[].state` の値を `data-state` 属性として
そのままHTMLへ出力する。それ以外の部品には `data-state` を付けない。

| 項目 | 内容 |
| --- | --- |
| 属性名 | `data-state` |
| 許可値 | `normal` / `empty` / `loading` / `error` / `forbidden`（実際に出るのは部品ごとに`state_components`で決まる値のみ） |
| 付与対象 | `blocks[].state` を持つ要素（`empty-state` / `loading` / `alert` の外枠 `.blk`） |

`data-state` を付けるだけでは色覚以外の手掛かりとして不十分なため、部品ごとに次の
非色覚の手掛かりを併せて出力する。

| 部品 | 非色覚の手掛かり |
| --- | --- |
| `empty-state` | 見出し文言（「データがありません」固定）＋ `message` の説明文 ＋ `aria-hidden="true"` を付けた記号アイコン |
| `alert` | 左端の境界線（`state`ごとに太さ・線種を変える。`error`は太い二重線、`forbidden`は破線）＋ `aria-hidden="true"` の記号アイコン ＋ 種別文言（`error`→「エラー」、`forbidden`→「権限がありません」） |
| `loading` | 視覚的には隠すがスクリーンリーダーには読ませる `aria-live="polite"` 領域に「読み込み中」の文言を置く。スピナー等のアニメーション表現だけに頼らない |

現時点ではこれらの非色覚手掛かりをHTML構造とインラインスタイルで表現している
（共有CSS `assets/screen-mock.html` は今回変更していない）。これはT-20時点の実装範囲による
現状であり、共有CSS側へ寄せる変更を妨げるものではない。

## 動作の前提

画面切替とモード切替はCSSだけで行う。`:target` と `:has()` を使うため、
Chrome 105以降・Safari 15.4以降・Firefox 121以降で開く。

## 完了条件

1. `python3 scripts/validate_screen_mock.py <出力HTML>` が成功する
2. デスクトップ幅・320px幅・印刷プレビューで目視確認する
3. 外部依存なしでHTMLを直接開ける
4. すべての遷移ボタンが対応する画面へ移動する
