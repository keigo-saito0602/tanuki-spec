---
name: tanuki-spec-generator
description: 案件着手時に、ユーザーストーリーから要件定義書・基本設計書・詳細設計書の根拠付きドラフトを作成し、抜け漏れと未確定事項を検証する。要件定義書作成、設計書のテンプレート記入、仕様の抜け漏れ確認、カバレッジ測定で使う。
---

# tanuki-spec-generator — 品質項目ベースの仕様書ジェネレーター

ざっくりしたユーザーストーリーを入力に、**品質項目マスター（SSOT）に基づく穴埋めテンプレート**へドラフトを生成し、
**カバレッジ評価**（項目の充足度）と出力ゲートを実行する。抜け漏れのない要件定義・設計のドラフトを用意するのが目的。

- 項目の正本: `spec-items.yaml`（要件定義26／基本設計22／詳細設計14。要件定義・基本設計では非機能35明細も個別評価、AI品質は別評価）
- 既存の `dev-workflow` / `kiro:spec-*` との棲み分け → 末尾「他スキルとの関係」参照
- 使い方の全体像（ユーザ/Claude/Codexの役割分担）→ [`../FLOW.md`](../FLOW.md)

---

## 起動時テンプレート（呼ばれたら、まずこれを出す）

このSKILLが呼び出されたら、**最初に次のテンプレートをそのまま提示し、ユーザーに埋めてもらう**。
`工程` と `ストーリー` が未記入のうちは生成を始めない（`参照仕様`・`モード` は空でよい）。

```
tanuki-spec-generator
工程:            # requirements（要件定義）/ basic_design（基本設計）/ detailed_design（詳細設計）
ストーリー:      # 誰が/何を/なぜ、のざっくりでOK
参照仕様:        # 参照したい過去仕様のパス（例: /Programming/soil-groove）。無ければ空欄
モード:          # full（既定・全項目＋評価）/ quick（必須のみ＋簡易）。空欄ならfull
```

埋まったら、下の「手順」①〜③を順に実行する。

---

## 入力パラメータ

| パラメータ | 必須 | 説明 |
| --- | --- | --- |
| ユーザーストーリー | ○ | 「誰が/何を/なぜ」レベルのざっくりした要望でよい |
| 対象工程 | ○ | `requirements`（要件定義）/ `basic_design`（基本設計）/ `detailed_design`（詳細設計） |
| 参照仕様（過去案件） | 任意 | **都度指定**。参照したい過去の仕様書リポジトリ/ファイルのパスを渡す（例: soil-groove の `codex-task-*`）。無指定なら参照なしで生成 |
| モード | 任意 | `full`（全項目・カバレッジ＋AI品質評価）/ `quick`（必須項目のみ・簡易チェック）。既定 `full` |

> 参照仕様は固定しない設計。案件ごとに参照元を指定して使う。

---

## 手順（この順で実行する）

### ①入力ゲート — ユーザーストーリーの INVEST チェック
INVESTの6軸（Independent/Negotiable/Valuable/Estimable/Small/Testable）をYES/NOで確認。
NOの軸は質問リストにして仕様書へ残す。ドラフト生成は止めないが、根拠がない項目を埋めてはいけない。

### ②穴埋め生成
1. `spec-items.yaml` の対象工程の項目と、`templates/<工程>-template.md` を読む。
   - テンプレは `python3 evaluation/generate_templates.py` でSSOTから再生成できる（手で編集せずSSOTを直す）。
2. 各項目の `<!-- FILL:START id -->` … `END` の間を、ユーザーストーリー（＋参照仕様）から記入する。
3. **根拠・不確実性ルール（必須）**:
   - 実際に記入した各FILLブロックの先頭に、`- **根拠**: [入力] ユーザーストーリー「<該当箇所>」` または `- **根拠**: [参照] <相対パス>#<見出し>` を書く。
   - 根拠が無い項目は勝手に埋めず、`[要確認: <確認したい質問>]` を残す。これは充足ではない。
   - 過去仕様は現案件の事実ではないため、採用する場合はユーザの承認を得る。
4. `required: conditional` の項目は、該当しない場合のみ `[対象外: <適用しない理由>]` と記入する。理由なしの対象外は許可しない。

### ③カバレッジ評価（決定論・自動）
```bash
python3 evaluation/coverage.py <記入済み仕様書.md> --strict
```
→ 必須充足率・全体充足率・欠落項目・`[要確認]`が出る。`--json` で機械可読サマリ。
続けて根拠まで含む出力ゲートを実行する。
```bash
python3 evaluation/spec_gate.py <記入済み仕様書.md>
```
必須の欠落または要確認があれば②へ戻る。絶対%は合否にせず「必須欠落ゼロ」と前回差分を見る。

③で出力ゲートを通過したら、レビューは別SKILL [`tanuki-spec-reviewer`](../tanuki-spec-reviewer/SKILL.md) に引き継ぐ。このSKILL自身では④⑤を実施しない。

`quick` モードでは、必須項目のみを生成・評価する。

---

## 出力

- 記入済みの `<工程>` 仕様書（Markdown）
- カバレッジ評価レポート（必須充足率／欠落リスト）

実例は `examples/sample-user-story/` を参照（サンプルストーリー1件のE2E成果物）。

---

## ファイル構成

```
tanuki-spec-generator/
├── SKILL.md                       ← このファイル（生成①〜③の正本）
├── spec-items.yaml                ← 共有コアへのsymlink
├── templates/                     ← 共有コアへのsymlink
├── evaluation/
│   ├── generate_templates.py      ← 共有コアへのsymlink
│   ├── coverage.py                ← 共有コアへのsymlink
│   ├── spec_gate.py               ← 根拠・未確定事項を含む出力ゲート
│   └── run_harness.py             ← 共有コア＋生成側の回帰テスト
├── evals/cases.yaml               ← モデルを使う評価シナリオ
├── tests/                         ← 決定論部分の回帰テスト
├── references/
│   └── README.md                  ← 参照仕様の渡し方・出典の考え方
└── examples/
    └── sample-user-story/         ← E2Eサンプル
```

---

## 他スキルとの関係（棲み分け）

| スキル | 役割 | 本SKILLとの関係 |
| --- | --- | --- |
| `tanuki-spec-reviewer` | ④⑤の独立レビューとDoD判定 | ③後に引き継ぐ |
| `dev-workflow`（3フェーズ） | 解析→設計→実装の交通整理 | 設計フェーズの前段として併用 |
| `kiro:spec-*`（cc-sdd） | 仕様駆動の実装フロー | 本SKILLの出力を入力として渡せる |

> cc-sdd（Kiro系列）は「次フェーズ前に矛盾・曖昧・欠落を分析する品質ゲート」を持つ。本SKILLの③はその `analyze` 相当を、業務システム品質項目に特化して実装したもの。

---

## Codex から使う場合

素のファイル構成（Markdown＋YAML＋Python）なので、Codexからも同じ手順で実行できる。
リポジトリのルート（`AGENTS.md`）がこのSKILL.mdを指しているので、Codexは `AGENTS.md` → 本手順に従う。
Python依存は `requirements.txt` のみ。初回は `python3 -m pip install -r requirements.txt` を実行する。
