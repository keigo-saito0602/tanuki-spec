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

---

## テンプレート本文の可読性（取得日: 2026-07-17）

上記11原則の適用後も、テンプレート本文の49〜56%の行がAI向けマーカーで占められていた（実測）。
マーカーを本文から付録へ移す判断の根拠を、次の一次情報に求めた。番号は上の11原則と独立している。

12. **段階的開示の適用範囲**: [Progressive Disclosure (NN/g)](https://www.nngroup.com/articles/progressive-disclosure/) ／ [Progressive Disclosure (NN/g 動画)](https://www.nngroup.com/videos/progressive-disclosure/): 初期表示と二次表示の分割は「頻繁に必要なものを前に、まれにしか使わないものを後ろへ」で決める。カード分類で重要度を順位づけ、低優先の項目を二次表示の候補にする。テンプレートでは、記入ガイド・出典・品質観点（記入時とレビュー時にしか要らない）を付録へ、決定内容（常に読む）を本文へ置く根拠。
13. **フォームの認知負荷**: [Placeholders in Form Fields Are Harmful (NN/g)](https://www.nngroup.com/articles/form-design-placeholders/) ／ [4 Principles to Reduce Cognitive Load in Forms (NN/g)](https://www.nngroup.com/articles/4-principles-reduce-cognitive-load/): フィールド内に消えるヒントを置くと記憶負荷が増え、エラーと所要時間が増える。ラベルは常時可視にし、ヒントは書式の補助に限る。テンプレートは実質「記入フォーム」であり、記入ガイドを表として常時可視の付録に置き、本文の見出し（＝ラベル）を残す根拠。
14. **Markdownソースの可読性**: [Google Markdown style guide](https://google.github.io/styleguide/docguide/style.html) ／ [Semantic Line Breaks](https://github.com/bobheadxi/readable): 1行に1つの意味単位を置くと、横方向の視線移動が減り、差分も1行に収まる。レンダリング結果とソースの見え方は別物として扱う。FILLブロックを1行へ畳み、項目1つを「見出し＋1行」に収めた根拠。

これらを「本文＝見出しとFILLブロックのみ」「根拠＝末尾の付録表」「節内は必須→条件付→任意の順」として採用した。
`spec-item` マーカーは、どのコードも読まない死んだ出力だったため削除した。

---

## 初見者向け説明HTML（取得日: 2026-07-29）

`tanuki-doc-html-generator`が、PDF・Excel・Markdownを人向けの説明HTMLへ再構成するときの追加根拠。

15. **利用者の目的から構成する**: [Understand content design (GOV.UK)](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/plan-manage-content/understand-content-design/): 読者が知りたいこと・実行したいことを先に定義し、量と形式を目的に合わせて選ぶ根拠。
16. **専門語を初出で説明する**: [Use clear language (GOV.UK)](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/): 専門家向けでも内容が分かる平易な説明を用意し、専門語は初出時に説明する根拠。
17. **意味のあるページ構造**: [Page Structure (W3C WAI)](https://www.w3.org/WAI/tutorials/page-structure/sections/): `header`、`nav`、`main`、`section`などを意味に沿って使い、見出しとランドマークで移動可能にする根拠。
18. **データ表の構造**: [Tables Tutorial (W3C WAI)](https://www.w3.org/WAI/tutorials/tables/): 表はレイアウトではなくデータ関係にだけ使い、`caption`、`th`、`td`、`scope`で見出しと値の関係を示す根拠。
19. **320 CSSピクセルでリフローする**: [Understanding Reflow (W3C WAI)](https://www.w3.org/WAI/WCAG22/Understanding/reflow): 情報や機能を失わず、原則として縦横2方向のスクロールを要求しないスマホ表示の根拠。
20. **図へ同等のテキストを付ける**: [Understanding Non-text Content (W3C WAI)](https://www.w3.org/WAI/WCAG21/Understanding/non-text-content): グラフ・フロー・図の目的と同等情報を、短い説明または詳細説明で提供する根拠。

本スキルでは、上記を「30秒要約→背景・前提→全体像→本論→例→注意→出典」「表・フロー・グラフは関係を理解しやすくする場合だけ使う」「320px、印刷、キーボード、読み上げを検証する」として採用する。

---

## 説明HTMLの配色（取得日: 2026-07-29）

`tanuki-doc-html-generator/references/color-design.md`の根拠。

21. **Zenn型の読み物配色**: [Zennの記事表示例](https://zenn.dev/nogu66/articles/claude-code-think-abount-skills-and-subagent): 淡い青灰色のページ背景、白い本文面、濃い灰色の本文、青いアクセント、濃紺のコード面を、長文説明HTMLの基本配色として採用する根拠。実表示のcomputed styleも確認した。
22. **3色と使用比率**: [プレゼン資料における配色の基本 (Cone)](https://cone-c-slide.com/see-sla/blog/document-color-usage/): 色をメイン・サブ・アクセントへ絞り、約75:20:5で使い、濃淡で展開する根拠。
23. **文字コントラスト**: [WCAG 2.2 Contrast Minimum](https://www.w3.org/TR/WCAG22/#contrast-minimum): 通常文字4.5:1以上、大きな文字3:1以上を最低条件にする根拠。
24. **色以外の識別手段**: [Understanding Use of Color (W3C WAI)](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html): 色だけで意味・状態・操作を伝えず、文字・形・境界線などを併用する根拠。
25. **明度差で配色を選ぶ**: [Using color (USWDS)](https://designsystem.digital.gov/design-tokens/color/overview/): 色相名ではなく相対輝度とコントラストを基準に組み合わせを検証する根拠。
26. **多様な色覚で識別する**: [カラーユニバーサルデザイン推奨配色セット](https://jfly.uni-koeln.de/colorset/) ／ [CUDOの説明](https://cudo.jp/?page_id=1565): グラフや状態表示で、比較的小面積でも見分けやすいアクセント色と、広い面積向けの低彩度色を使い分ける根拠。

本スキルでは、Zennの明るい青`#3ea8ff`を大きな図形・補助面へ限定し、白背景の通常文字にはコントラストを確保した濃い青`#0068b7`を使う。背景・本文・リンク・状態・コードを役割トークン化し、ライト・ダーク・印刷の各モードで検証する。
