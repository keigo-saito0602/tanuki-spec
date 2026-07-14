# tanuki-spec-all

このディレクトリは`tanuki-spec-generator`と`tanuki-spec-reviewer`が参照する共有コアです。単独のSKILLとしては起動しません。

## 導入と検証

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python evaluation/run_harness.py
```

`spec-items.yaml`が品質項目の唯一の正本です。テンプレートは手編集せず、`evaluation/generate_templates.py`で再生成します。
