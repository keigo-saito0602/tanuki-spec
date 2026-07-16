# Web調査の根拠

取得日: 2026-07-14

- [Anthropic: Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): SKILLの説明を具体化し、少なくとも3つの評価ケース、SSOTと生成物の検証を持つ方針の根拠。
- [Anthropic: Skills for enterprise](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise): 発火精度・共存・出力品質を分けて評価し、スキル作者と評価者を分離する方針の根拠。
- [OpenAI: Using skills](https://openai.com/academy/skills/): `SKILL.md`と補助リソースで再利用可能なワークフローを構成する、Codex側との共通構成の根拠。

本スキルでは、上記を「モデルに依存する評価は`evals/cases.yaml`で反復実行」「決定論的な検査はPythonで自動化」「品質レビューは生成担当と別担当で行う」として採用した。

---

## 認知科学に基づく資料構成（取得日: 2026-07-16）

[`../references/cognitive-doc-principles.md`](../references/cognitive-doc-principles.md) の11原則の一次情報。番号は同ファイルの原則番号に対応する。

1. **認知負荷理論**: [Cognitive load](https://en.wikipedia.org/wiki/Cognitive_load) ／ [Cognitive Load Theory and Instructional Design](https://www.uky.edu/~gmswan3/544/Cognitive_Load_&_ID.pdf): ワーキングメモリの負荷をintrinsic/extraneous/germaneに分け、見せ方由来の無駄な負荷（extraneous）を削る根拠。
2. **段階的開示**: [Progressive Disclosure (NN/g)](https://www.nngroup.com/articles/progressive-disclosure/) ／ [Progressive Disclosure (IxDF)](https://ixdf.org/literature/topics/progressive-disclosure): 最重要を先に見せ詳細は必要時に取りに行かせる、サマリ→本論→付録の3層の根拠。
3. **結論ファースト**: [Minto Pyramid Principle](https://untools.co/minto-pyramid/) ／ [Minto Pyramid 解説](https://www.betterup.com/blog/minto-pyramid): 答え（結論）を先頭に置き根拠・データを後続させる構造の根拠。BLUF・逆ピラミッドも同型。
4. **スキャン読み**: [F-Shaped Pattern (NN/g)](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/) ／ [Text Scanning Patterns (NN/g)](https://www.nngroup.com/articles/text-scanning-patterns-eyetracking/): 人は読まずスキャンする（layer-cake読み等）ため、見出しと行頭に情報を凝縮する根拠。
5. **合図・強調**: [Signaling/Cueing Principle (Cambridge Handbook of Multimedia Learning)](https://www.cambridge.org/core/books/abs/cambridge-handbook-of-multimedia-learning/signaling-or-cueing-principle-in-multimedia-learning/3972D4ACC628D5B53F7B2B4785DB2B06) ／ [Principles for reducing extraneous processing](https://www.researchgate.net/publication/262915119): 見出し・強調で構造の手がかりを与えると理解が深まる根拠。Von Restorff効果・Gestalt（近接/類似）も併用。
6. **チャンク化**: [Miller's Law](https://lawsofux.com/millers-law/) ／ [The Magical Number Seven, Plus or Minus Two](https://en.wikipedia.org/wiki/The_Magical_Number_Seven,_Plus_or_Minus_Two): 即時記憶は約7±2チャンクで、意味のまとまりに束ねると処理しやすい根拠。
7. **チェックリスト**: [The Checklist Manifesto（要約・PMC）](https://pmc.ncbi.nlm.nih.gov/articles/PMC4953332/): エラーは無知より「知っているのに実行し忘れる」が多く、最小限のチェックリストで見落としが激減する根拠。
8. **Perspective-Based Reading**: [PBRが要件インスペクションを改善する (Basili他)](https://www.cs.umd.edu/~basili/publications/journals/J79.pdf) ／ [PBR実証研究](https://www.cs.umd.edu/~mvz/handouts/emp_pbr.pdf): 役割視点別に読むとad-hoc/チェックリスト読みより欠陥検出率が上がる根拠。
9. **トレーサビリティ**: [Requirements Traceability Matrix](https://www.guru99.com/traceability-matrix.html) ／ [RTM解説](https://www.softwaretestinghelp.com/requirements-traceability-matrix/): 要件↔設計↔テストの対応表で抜けと変更影響を可視化する根拠。
10. **ADR**: [Architecture Decision Records](https://adr.github.io/) ／ [AWS: ADR process](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html): 決定・代替案・帰結を1判断1レコードで軽量に記録する根拠。
11. **Plain Language**: [Plain Language Principles (digital.gov)](https://digital.gov/guides/plain-language/principles): 読者に合わせ専門用語を避け、短文・能動態・具体語・箇条書きで書く根拠。

本設計では、上記を「読み手モデルを書類ごとに分ける（要件＝非技術者／設計＝第三者技術者）」「サマリ層を冒頭に必須化」「著者メタを本文から隔離」「カテゴリ単位の節末チェックリスト」として採用した。
