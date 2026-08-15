# 複数機能例（phase-2）

func/phase再構成（2026-08-12設計）のサンプル。`func-予約`と`func-認証`の2機能が
1つのphaseに同居し、business_flows・AC・STがfuncをまたいで`system-traceability.yaml`へ
集約されている例。`system_traceability_gate.py`・`render_traceability_docs.py`・
`render_html_views.py`の動作確認に使う。
