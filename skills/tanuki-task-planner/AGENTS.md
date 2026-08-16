# AGENTS.md — tanuki-task-planner

Codex等のエージェントは[SKILL.md](./SKILL.md)を読み、cc-sdd併用時は承認済み仕様の橋渡しを確認する。単独運用時だけ仕様から実装タスクを分解する。

1. `cc-sdd`（既定）か`standalone`かを確定する。
2. cc-sdd併用時は共通ブリッジを検証し、`kiro-spec-tasks`へ渡す。
3. 単独運用時だけ`traceability.yaml`からタスクを作り、`evaluation/task_plan_gate.py`を通す。
