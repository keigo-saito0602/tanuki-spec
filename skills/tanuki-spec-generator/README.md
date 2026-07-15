# tanuki-spec-generator

Claude CodeとCodexで共通利用する、根拠付き仕様書ドラフト作成・生成側検証スキルです。手順の正本は[SKILL.md](./SKILL.md)です。独立レビューは`tanuki-spec-reviewer`が担当します。

要件定義書を入力に設計書を作成する、既存コードを調査して設計する、または要件変更へ設計を追従させる場合は、設計特化の`tanuki-spec-design`を推奨します。本SKILLの既存設計工程は引き続き利用できます。

## 導入と確認

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
../tanuki-spec-all/.venv/bin/python evaluation/run_harness.py
```

Claude Codeではスキルの配置先からこのディレクトリを読み込ませ、Codexではリポジトリの`AGENTS.md`から`SKILL.md`を参照させます。両環境で次を1回ずつ実行し、`evals/cases.yaml`の発火ケースも各3回評価してください。

```text
予約機能の要件定義書を、過去仕様も参照して作りたい
```

## 日常の検証

```bash
.venv/bin/python evaluation/coverage.py path/to/spec.md --strict
.venv/bin/python evaluation/traceability_gate.py path/to/traceability.yaml
.venv/bin/python evaluation/render_traceability_docs.py path/to/traceability.yaml --output-dir path/to/output
.venv/bin/python evaluation/spec_gate.py path/to/spec.md --traceability path/to/traceability.yaml
```

`spec-items.yaml`の`approval_status`が`pending_owner_approval`の間は、作成物をドラフトとして扱い、実装へ渡す前にユーザの承認を得ます。
承認後は、根拠資料とマスター項目表を確認したうえで、`approval_status`を`approved`へ変更してください。
