# ドライラン観察ログ

実施日: 2026-08-09
入力: `templates/screens-template.yaml` と `templates/design-tokens-template.json`

実行環境の制約: 本ドライランはGUI（ディスプレイ）を持たないエージェント環境で実施した。
`open`コマンド自体は終了コード0で完了したが、実際にブラウザ画面が開いて描画されたかどうかは
目視できない。そのため「ブラウザでの目視確認」欄は、生成されたHTMLファイルをReadツールで
読み、HTML/CSSのロジックを実際にたどって確認した結果を記録している（ブリーフの指示どおり、
目視確認の代替として採用）。

## 実行結果

| コマンド | 終了コード | 出力の要点 |
| --- | --- | --- |
| `screens_gate.py` | 0 | `検証を通過しました。注意は0件です。` |
| `render_screen_mock.py` | 0 | `画面モックを書き出しました: /tmp/dryrun/views/画面モック.html`（生成HTMLは150行、11176バイト） |
| `validate_screen_mock.py` | 0 | `出力契約を満たしています。` |
| `render_screen_docs.py` | 0 | 画面一覧の表をMarkdownで標準出力。`SC-001 → SC-002`、`SC-002 → SC-001`の2行（テンプレートのプレースホルダ文言のまま） |

4コマンドとも一度も失敗せず、テンプレートの値をそのまま流すだけでエラーなくパイプライン全体が通った。

## ブラウザでの目視確認（HTML/CSSのコード確認による代替）

| 確認項目 | 結果 |
| --- | --- |
| 初期表示で SC-001 が見える | 確認できた。`.screen:target{display:block}`に加え、`body:not(:has(.screen:target)) .screen:first-of-type{display:block}`があり、URLフラグメントが無い初期状態ではSC-001（最初の`.screen`）が表示される実装になっている。`:has()`セレクタに依存するため対応ブラウザに下限があるが、これは`references/mock-html-contract.md`の「動作の前提」（Chrome 105以降・Safari 15.4以降・Firefox 121以降）に既に明記済みであることを確認した |
| 遷移ボタンで SC-002 へ移動する | コード上は妥当。SC-001内の`<a class="btn" href="#SC-002">`をクリックするとURLフラグメントが`#SC-002`になり、`.screen:target`でSC-002側が`display:block`に、SC-001側は`:target`が外れ`:first-of-type`条件も`:has(.screen:target)`が真になるため非表示になる。実ブラウザでのクリック操作そのものは未実施 |
| ワイヤー／デザインの切替が効く | コード上は妥当。`#fid-wire`と`#fid-design`のradioは`.app`と兄弟要素で、`#fid-wire:checked ~ .app`でCSS変数（`--color-primary`等）をワイヤー用配色に上書きする仕組みになっている。実クリックでの見た目切り替えは未確認 |
| PC／スマホの切替が効く | コード上は妥当。`#dev-sp:checked ~ .app .canvas{max-width:390px}`でスマホ選択時にキャンバス幅が縮む。実クリックでの見た目切り替えは未確認 |
| 320px幅で横スクロールが出ない | コード確認の範囲では横スクロールの要因は見当たらない。`* { box-sizing: border-box }`、`img,svg{max-width:100%}`、`.grid`の列最小幅は11rem（176px）で320px幅の1カラム表示に収まり、表は`.tbl-wrap{overflow-x:auto}`で個別に横スクロールする設計。ただし実際のビューポート幅320pxでのレンダリングは未確認のため、レイアウト崩れが無いとまでは断定できない |
| 印刷プレビューで全画面が出る | コード上は妥当。`@media print`で`.controls`と`.sidebar`を非表示にし、`.screen{display:block}`で`:target`の状態に関わらず全画面（SC-001・SC-002）を強制表示する実装になっている。実際の印刷プレビュー画面は未確認 |

## 気づいた不足

- テンプレートをそのまま流した場合、`render_screen_docs.py`の出力は`<画面名>`や`<操作名>`のプレースホルダのままになる。これはテンプレート自体の仕様であり実案件では記入済みの`screens.yaml`を使うため、スクリプト側の不足ではない。
- 初期表示の仕組みが`:has()`セレクタに依存している点は、`references/mock-html-contract.md`の「動作の前提」に対応ブラウザ（Chrome 105以降・Safari 15.4以降・Firefox 121以降）としてすでに明記されていることを確認した。参照資料・SKILL.mdとも追記の必要はない。
- 320px幅・実クリック操作・印刷プレビューの3項目は、GUI環境がないため実際のレンダリングでの確認はできなかった。実機（人手）での目視レビューが別途必要。
- `python3 -m unittest discover -s scripts -v`を併せて実行したところ、既存88件のテストはすべて成功した（AGENTS.mdに記載のテストコマンドが実際に機能することを確認）。
- 部品カタログ自体の過不足は感じなかった。
