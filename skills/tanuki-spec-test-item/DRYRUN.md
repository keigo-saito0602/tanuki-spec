# ドライラン観察ログ

## RED

- ケース: `trigger-positive`
- 観察: SKILL なしだと、UT/IT まで `traceability.yaml` に混ぜる、または AC/ST を重複生成するぶれが出やすい。
- 見落とし: テスト工程に `coverage.py` を流用しようとして、既存契約と衝突する可能性がある。

## GREEN

- ケース: `trigger-positive`
- 解消した問題: 「下半分だけ新規」「AC/ST は再利用」「coverage 非適用」を固定したので、既存チェーンを壊さずに範囲を切り出せる。
- 残った問題: 要件外だが試験上必要な観点を、どこまで v1 で許すかは曖昧になりやすい。

## REFACTOR

- 失敗パターン: `ST` の `test_type: integration` を V字モデルの `IT` と混同する。
- 追加した規則: SKILL 本文と `edge-case` に、system test 内の種別値と設計レベルの結合試験は別物だと明記した。
- 再実行結果: IT の新規領域が `BD-xxx` 起点であることが判断しやすくなった。

## 非発火・曖昧ケース

- ケース: `trigger-negative`
- 発火判定: false
- コメント: 既存レビュー記録の採点だけをしたい依頼は `tanuki-spec-reviewer` の担当。

- ケース: `ambiguous-case`
- 発火判定: true
- コメント: 設計書が未完成でも起動可能だが、欠けた設計要素は `[要確認: 質問]` として残す。

## 完了判定

- 実行日: 2026-07-16
- モデル: Codex
- ケース数: 4
- 結果: 新SKILLの責務境界は明確。実運用では update モードの差分判定事例を追加で観察したい。
- 次回確認日: 初回実運用後
