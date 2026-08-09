# tanuki-screen-mock

要件定義書とユーザーストーリーから画面定義を起こし、参考ソースのデザイントークンを当てて、ブラウザで開くだけの単一HTML画面モックを生成するスキルです。手順の正本は[SKILL.md](./SKILL.md)です。

## フローのどこで使うか（③.5）

`tanuki-spec-generator`で要件定義書を確定させた（③）あと、`tanuki-spec-design`で基本設計書を書き起こす（④）前に挟んで使います。要件定義書の`req-io`（入出力・画面・帳票要件）に画面の記載がある案件でのみ実行し、確定した画面一覧・画面遷移を基本設計書の「画面一覧・画面遷移設計」へ渡します。画面を伴わない案件では実行せず、その旨を報告します。

## 入力と出力

入力:

- 要件定義書（必須）
- フェーズディレクトリ（必須）
- 参考ソース（任意）: コード（tailwind.config.tsなど）／スクリーンショット／URL
- 対象アクター・モード（任意）

出力:

| 種別 | パス |
| --- | --- |
| 正本 | `<phase>/screens.yaml` |
| 正本 | `<phase>/design-tokens.json` |
| 派生 | `<phase>/views/画面モック.html` |
| 追記 | `<phase>/reports/01_差分・未決事項.md` |

生成HTMLは派生物であり手編集しません。修正は`screens.yaml`か`design-tokens.json`に対して行い、再生成します。

## 導入と確認

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s scripts -v
```

## コマンド一覧

`tanuki-screen-mock/`を起点に実行します。

```bash
python3 scripts/screens_gate.py <phase>/screens.yaml
python3 scripts/render_screen_mock.py <phase>/screens.yaml <phase>/design-tokens.json --output <phase>/views/画面モック.html
python3 scripts/validate_screen_mock.py <phase>/views/画面モック.html
python3 scripts/render_screen_docs.py <phase>/screens.yaml
```

## 推奨モデル

[要確認: docs/recommended-models.md 作成後に記入]
