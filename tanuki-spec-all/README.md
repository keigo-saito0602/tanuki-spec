# tanuki-spec-all

このディレクトリは`tanuki-spec-generator`と`tanuki-spec-reviewer`が参照する共有コアです。単独のSKILLとしては起動しません。

## 導入と検証

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python evaluation/run_harness.py
```

`spec-items.yaml`が品質項目の唯一の正本です。テンプレートは手編集せず、`evaluation/generate_templates.py`で再生成します。

利用する書類と作成順は、[templates/README.md](./templates/README.md)を参照してください。開発初期のプロダクトバックログとトレーサビリティ正本はコピーして記入し、要件定義書・設計書・試験項目書は正本から生成・検証します。

`design-traceability-template.yaml`、`design_traceability_gate.py`、`render_design_traceability_docs.py`は、既存の要件トレーサビリティを変更せずにBR/FR/NFRとBD/DDの対応を管理する共有基盤です。
