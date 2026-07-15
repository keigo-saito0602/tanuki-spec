# AGENTS.md — tanuki-task-planner

Codex等のエージェントは[SKILL.md](./SKILL.md)を読み、仕様から実装タスクを分解する。

1. `traceability.yaml` の対象要件・試験を読む。
2. `templates/task-plan-template.yaml` を正本としてタスクを記入する。
3. `evaluation/task_plan_gate.py` を通してから、実装へ引き渡す。
