# tanuki-task-planner

`system-traceability.yaml`（phase直下）を入力に、実装タスク・依存関係・完了条件・検証方法を作成するスキルです。

```bash
../../tanuki-spec-all/.venv/bin/python evaluation/task_plan_gate.py path/to/task-plan.yaml --system-traceability path/to/system-traceability.yaml
../../tanuki-spec-all/.venv/bin/python evaluation/render_task_plan.py path/to/task-plan.yaml --output path/to/implementation-task-plan.md
../../tanuki-spec-all/.venv/bin/python evaluation/run_harness.py
```

タスク計画の正本は `templates/task-plan-template.yaml` をコピーして作成します。要件・受入試験・システムテストのいずれかがタスクから孤立すると、ゲートは不通過になります。
