# 書類テンプレート一覧

案件では、次の順に使う。`requirements`、`basic_design`、`detailed_design` は `spec-items.yaml` から自動生成されるため、直接編集しない。

| 書類 | テンプレートまたは生成元 | 役割 | 編集方法 |
| --- | --- | --- | --- |
| 開発初期プロダクトバックログ | [product-backlog-template.md](./product-backlog-template.md) | 要望をユーザーストーリーと優先順位へ整理する | 人間工学構成を手編集で維持し、コピーして記入 |
| 要件定義書 | [requirements-template.md](./requirements-template.md) | 業務・機能・非機能・受入条件を定義する | `generate_templates.py` で再生成後にコピーして記入 |
| 基本設計書 | [basic-design-template.md](./basic-design-template.md) | 画面・API・データ・外部連携・方式を定義する | `generate_templates.py` で再生成後にコピーして記入 |
| 詳細設計書 | [detailed-design-template.md](./detailed-design-template.md) | 状態遷移・条件分岐・内部処理・例外を定義する | `generate_templates.py` で再生成後にコピーして記入 |
| トレーサビリティ正本 | [traceability-template.yaml](./traceability-template.yaml) | US、業務フロー、要件、受入試験、システムテストをIDで結ぶ | コピーして記入 |
| 設計トレーサビリティ正本 | [design-traceability-template.yaml](./design-traceability-template.yaml) | BR/FR/NFRと基本・詳細設計要素をIDで結ぶ | コピーして記入 |
| 設計対応表 | `render_design_traceability_docs.py` | 要件と設計要素の対応を見える化する | YAMLから自動生成。直接編集しない |
| 要件対応表 | `render_traceability_docs.py` | US・業務フロー手順とBR/FR/NFRの対応を見える化する | YAMLから自動生成。直接編集しない |
| 受入試験項目書 | `render_traceability_docs.py` | 利用者・業務視点での合格条件を確認する | YAMLから自動生成。直接編集しない |
| システムテスト項目書 | `render_traceability_docs.py` | 機能・連携・非機能の検証項目を確認する | YAMLから自動生成。直接編集しない |
| AI品質レビュー記録 | `tanuki-spec-reviewer/templates/ai-quality-review-template.yaml` | 独立レビューとDoDを記録する | コピーして記入 |

## 最短手順

1. `product-backlog-template.md` で要望をユーザーストーリーに分け、優先順位とリリース単位を決める。
2. `traceability-template.yaml` にUS・業務フロー・BR/FR/NFR・AC/STを記入する。
3. 要件定義書、基本設計書、詳細設計書を対象工程に応じて作成する。
4. `traceability_gate.py` を通してから、受入試験項目書とシステムテスト項目書を生成する。
5. 設計書を作る場合は `design-traceability-template.yaml` に要件とBD/DDを記入し、`design_traceability_gate.py` を通して設計対応表を生成する。
6. 別担当がAI品質レビュー記録を作成・検証する。

テンプレート内の`<...>`、`[要確認: ...]`、`TODO`は未記入であり、出力ゲートを通過できない。

## 自動生成テンプレートの構成

`requirements`、`basic_design`、`detailed_design` の3種は、本文と付録の2層でできている。

- **本文**: 見出しと、1行のFILLブロック（`<!-- FILL:START id -->（未記入）<!-- FILL:END id -->`）だけを置く。読み手が追うのは、各項目に何が書かれたかだけである。節の中は 必須 → 条件付 → 任意 の順に並ぶ。
- **非機能要件の個別明細（35項目）**: 大項目ごとの表にまとめる。列は 必須／項目／確認指標／記入。確認指標は記入の手がかりとして常時表示する。表のセルは1行しか持てないため、記入は「目標値 ／ 根拠: US-xxx」のように1行にまとめる。
- **一覧・マトリクス・テーブル系の項目**: 中身が本来は表になる項目（画面一覧・デシジョンテーブル・エラーコード一覧など）は、見出しの下に `> 📝 記入形式: ...` で推奨カラムを1行だけ示す。行数がプロジェクト依存で事前に確定できないため、骨組みはFILLの外に置き、FILLの中は空にする。記入者は推奨カラムに沿って実際の表をFILL内へ書く。推奨カラムは`spec-items.yaml`の`table_hint`が正本。
- **付録「項目の根拠一覧」**: 本文の各項目の記入ガイド・出典・品質観点を表にまとめる（非機能明細は確認指標が本文の表に載るため、付録には重ねない）。記入担当のAIはFILLを埋める前に該当ID行を読み、レビュー担当は項目の存在理由を疑うときだけ参照する。

FILLマーカーは`coverage.py`が本文を切り出す境界であり、削除も移動もできない。1行に畳んであるのは、`find_body`が正規表現でマーカーの内側だけを抜き、判定に影響しないためである。
