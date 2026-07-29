# tanuki-spec-all

このディレクトリは`tanuki-spec-generator`、`tanuki-spec-design`、`tanuki-spec-test-item`、`tanuki-spec-reviewer`が参照する共有コアです。単独のSKILLとしては起動しません。

## 導入と検証

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python evaluation/run_harness.py
```

`spec-items.yaml`が品質項目の唯一の正本です。テンプレートは手編集せず、`evaluation/generate_templates.py`で再生成します。

利用する書類と作成順は、[templates/README.md](./templates/README.md)を参照してください。開発初期のプロダクトバックログとトレーサビリティ正本はコピーして記入し、要件定義書・設計書・試験項目書は正本から生成・検証します。

`design-traceability-template.yaml`、`design_traceability_gate.py`、`render_design_traceability_docs.py`は、既存の要件トレーサビリティを変更せずにBR/FR/NFRとBD/DDの対応を管理する共有基盤です。

`evaluation/render_html_views.py`は、フェーズ内に存在するMarkdownを `views/` の自己完結HTMLへ変換する共有レンダラです。Markdown/YAMLを正本のまま保ち、各スキルはsymlinkで同じ実装を呼び出します。

```bash
# 生成・更新
python3 evaluation/render_html_views.py <phase>

# 書き換えず、欠落・正本との差分を検査
python3 evaluation/render_html_views.py <phase> --check
```

未着手工程の文書はエラーにせずスキップします。HTMLは派生物のため手編集せず、正本を更新して再生成してください。出力構成とObsidianでの閲覧方法は [`../docs/spec-directory-standard.md`](../docs/spec-directory-standard.md) を参照してください。
