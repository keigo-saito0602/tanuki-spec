# Web調査の根拠

取得日: 2026-07-14

- [Anthropic: Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): SKILLの説明を具体化し、少なくとも3つの評価ケース、SSOTと生成物の検証を持つ方針の根拠。
- [Anthropic: Skills for enterprise](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise): 発火精度・共存・出力品質を分けて評価し、スキル作者と評価者を分離する方針の根拠。
- [OpenAI: Using skills](https://openai.com/academy/skills/): `SKILL.md`と補助リソースで再利用可能なワークフローを構成する、Codex側との共通構成の根拠。

本スキルでは、上記を「モデルに依存する評価は`evals/cases.yaml`で反復実行」「決定論的な検査はPythonで自動化」「品質レビューは生成担当と別担当で行う」として採用した。
