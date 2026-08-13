---
name: tanuki-spec-screen-mock
description: Use when 要件定義書から画面モックを作りたい、画面構成・画面遷移・配色を実装前にレビューしたい、参考サイトのデザインを反映した画面イメージが欲しいとき。
---

# 画面モック Generate

要件定義書とユーザーストーリーから画面定義を起こし、参考ソースのデザイントークンを当てて、
ブラウザで開くだけの単一HTML画面モックを生成する。

## 起動テンプレート

```text
tanuki-spec-screen-mock
要件定義書(必須): docs/spec/phase-1_公開サイト・予約/func-予約/01_要件定義書.md, docs/spec/phase-1_公開サイト・予約/func-認証/01_要件定義書.md  # 複数funcを横断して指定
フェーズ(必須): docs/spec/phase-1_公開サイト・予約
参考ソース(任意): tailwind.config.ts / ./ref/top.png / https://example.com
対象アクター(任意): 生徒, 講師
モード(任意): create
```

任意項目の動作:

| 項目 | 指定時 | 未指定時 |
| --- | --- | --- |
| 参考ソース | 優先順位（コード>スクショ>URL）でトークンを抽出し確度を記録する | `uiux-principles.md`から既定トークンを提案し`proposed`とする |
| 対象アクター | そのアクターが触る画面に絞る | 要件定義書に登場する全アクターを対象にする |
| モード | 指定に従う | `screens.yaml`があれば`update`、なければ`create` |

## 必ず読む

1. `references/uiux-principles.md`
2. `references/screens-schema.md` と `references/component-catalog.yaml`
3. 参考ソースがある場合は `references/design-token-extraction.md`
4. HTML生成の前に `references/mock-html-contract.md`
5. 画面名・目的・状態の説明を書く前に `references/cognitive-doc-principles.md`。共有コア`../../tanuki-spec-all/`へのsymlinkであり、認知設計の正本とする

## 実行条件

ユーザが操作する画面を伴う案件でのみ実行する。要件定義書の`req-io`（入出力・画面・帳票要件）に
画面の記載がなければ、モックを作らずその旨を報告する。

## 手順

0. 入力として渡された`<phase>`から`docs/spec/system-baseline/`を解決する
   （カレントディレクトリ基準ではなく、`<phase>`の親を辿って解決する）。存在する場合は
   `システム構成・共通基盤.md`・`非機能ベースライン.md`を読み、記載と矛盾しない内容にする。
   共通用語は`GLOSSARY.md`を正とする。存在しない場合はこのステップを省略する
   （初回フェーズ等でまだ作られていないことがある）。
   参照した場合は、`reports/01_差分・未決事項.md`に「参照したベースライン文書」を記録する。

### 1. 入力を確定する

- フェーズ配下の各`func-<名前>/01_要件定義書.md`を横断して読み、`req-io`と機能要件から画面が必要かを判断する。画面はfunc単位ではなくphase全体で洗い出す。
- フェーズディレクトリの存在と、`screens.yaml`の有無から`create`／`update`を決める。
- 参考ソースの種類（コード／画像／URL）を確認する。

### 2. 画面を洗い出す

`references/uiux-principles.md`に従い、要件から画面を起こす。

- 1画面1目的で分ける。目的が2つあるなら画面を分ける。
- 各画面に5状態（通常・空・読込中・エラー・権限なし）を必ず検討する。
- エラー画面と認証画面を忘れない。
- 各画面に対応する要件IDを`trace`へ書く。根拠がない画面は作らない。

### 3. screens.yaml を書く

`templates/screens-template.yaml`をコピーし、`references/screens-schema.md`に従って記入する。
部品とレイアウトは`references/component-catalog.yaml`にあるものだけを使う。
カタログにない表現が必要なら勝手に作らず、`notes`へ`[要確認: 質問]`を残して報告する。

```bash
python3 scripts/screens_gate.py <phase>/screens.yaml
```

エラーが出たら定義を直して再実行する。`注意:`の行は`[要確認]`として残してよい。

### 4. design-tokens.json を書く

`templates/design-tokens-template.json`をコピーし、`references/design-token-extraction.md`の
優先順位に従って値と確度を記入する。URLからは色を取得できないため、推測した色を`confirmed`にしない。

### 5. モックHTMLを生成する

```bash
python3 scripts/render_screen_mock.py <phase>/screens.yaml <phase>/design-tokens.json --output <phase>/views/画面モック.html
python3 scripts/validate_screen_mock.py <phase>/views/画面モック.html --screens <phase>/screens.yaml
```

モデルはHTMLとCSSを書かない。検証に失敗したら`screens.yaml`か`design-tokens.json`を直して再生成する。

`validate_screen_mock.py`は次の2段で検証する。
- 要素単位: `data-state`属性を持つ要素に、文字・境界線・アイコンのいずれかが併存しているか（色だけに頼った状態表現を防ぐ）
- 画面単位（`--screens`指定時）: `screens.yaml`の`blocks[].state`の集合と、HTMLの`section#<画面ID>`内の`data-state`の集合が一致しているか

`--screens`を省略すると画面単位の突き合わせは行われず、その旨が標準出力に表示される。

レイアウトの最終確認として、実ブラウザでの検査も実行できる（`playwright install chromium`が別途必要）。
320px幅での横スクロール、タップ対象の実寸（44px）、フォーカス表現（アウトラインの太さとコントラスト）を実測し、
axe-coreで一般的なアクセシビリティ違反（ランドマーク外の対話要素、キーボード操作不能なスクロール領域など）も検査する。
毎回の反復では必須にしないが、画面数が確定してレビューへ出す前には実行する。
色以外の手掛かりが「意味として」機能しているかの人手評価はT-22Cで別に行う。

```bash
python3 scripts/check_browser_contract.py <phase>/views/画面モック.html
```

### 6. レビューを依頼する

ユーザへ次を伝える。

- モックHTMLの保存先と、ブラウザで開く手順
- **まずワイヤーモードで構成と遷移を確認してほしいこと**
- 色はデザインモードへ切り替えて別に見てほしいこと
- 画面数、`[要確認]`の件数、確度が`confirmed`でないトークンの件数

キーボード操作・支援技術・色以外の手掛かりが意味として機能するかは機械検査では判定できない。
最終確定前に[`references/human-ux-review-guide.md`](./references/human-ux-review-guide.md)の手順で人手評価する。

### 7. 修正を反映する（updateモード）

指摘のあった画面だけ`screens.yaml`を直し、手順5を再実行する。無関係な画面を書き換えない。
変更した画面IDと変更内容を報告する。

### 8. 確定後に基本設計へ渡す

```bash
python3 scripts/render_screen_docs.py <phase>/screens.yaml
```

出力された表を`02_基本設計書.md`の「画面一覧・画面遷移設計」へ貼る。
`[要確認]`は`<phase>/reports/01_差分・未決事項.md`へ転記する。

## 出力

| 種別 | パス |
| --- | --- |
| 正本 | `<phase>/screens.yaml` |
| 正本 | `<phase>/design-tokens.json` |
| 派生 | `<phase>/views/画面モック.html` |
| 追記 | `<phase>/reports/01_差分・未決事項.md` |

HTMLは派生物であり手編集しない。直すのは`screens.yaml`か`design-tokens.json`。

## 文章の点検（出力前）

`references/cognitive-doc-principles.md`の「症状を二つに分ける」「文レベルの規範」「語彙の規範」「想起を組み込む規範」で、`purpose`・`states`・`notes`の文章を自己点検する。点検していない文章は`screens.yaml`へ入れない。

画面モックで人が読むのは、画面名・目的・5状態の説明・要確認事項の4つ。ここが曖昧だとレビューで指摘が出せない。

## 禁止

- HTMLやCSSを直接書く。
- カタログにない部品やレイアウトを勝手に増やす。
- URLから推測した色を`confirmed`として記録する。
- 5状態を「該当なし」だけで埋め、理由を書かない。
- 要件に根拠のない画面を作る。
- 生成HTMLに`<script>`やイベント属性を入れる。
- 読み手が楽に読めたことを、理解された証拠として扱う。
- 要約の追加や強調の増加を、理解を助ける手段として数える。
- 検証エラーを抑制して完了扱いにする。
- モックHTML全文を会話へ貼る。
