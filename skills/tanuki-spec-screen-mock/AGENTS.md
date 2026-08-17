# AGENTS.md — tanuki-spec-screen-mock

要件定義書から画面モックを生成するスキルです。手順は [`SKILL.md`](./SKILL.md) を読んでください。

## 依存

```bash
python3 -m pip install -r requirements.txt
```

PyYAML のみ。それ以外は標準ライブラリで動きます。

## コマンド

`tanuki-spec-screen-mock/` を起点に実行します。

```bash
python3 scripts/screens_gate.py <phase>/screens.yaml
python3 scripts/render_screen_mock.py <phase>/screens.yaml <phase>/design-tokens.json --output <phase>/views/画面モック.html
python3 scripts/validate_screen_mock.py <phase>/views/画面モック.html
python3 scripts/render_screen_docs.py <phase>/screens.yaml
```

## テスト

```bash
python3 -m unittest discover -s scripts -v
```

## 規約

- 生成物の文言は日本語にする。
- 根拠不明な項目は埋めず、`[要確認: 質問]` を残す。
- モデルは HTML と CSS を書かない。`screens.yaml` と `design-tokens.json` だけを書く。
- 部品とレイアウトは `references/component-catalog.yaml` を共通カタログの正本とする。案件固有の部品は共通定義を含むプロジェクト側の拡張版を作り、ゲートへ `--catalog` で渡す。
- 画面ごとにデザイン問い・仮説・リスク・検証タスク・根拠・探索方法・リスクに応じた重点状態を記録する。高リスクは2〜3案を比較し、低・中リスクで既存パターンを継承する場合は継承元と適合理由を記録する。5状態を機械的に同じ深さで増やさない。
