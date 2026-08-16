# tanuki-spec と cc-sdd の併用方針

## 配布方式と互換性

- cc-sdd本体はtanuki-specへコピーせず、公式npmパッケージを外部依存として利用する。
- 検証済みバージョン、導入フラグ、配置ルート、必須Skill・テンプレート・補助ファイル一覧は`integrations/cc-sdd/compatibility.json`を正本とする。
- プリフライトは`@latest`を使わず、互換性台帳に固定した版だけを新規導入する。版を上げるときは台帳、テスト、隔離環境での実CLI試験を同じ変更で更新する。
- 既に導入済みで版の記録がない環境は、必須Skillの構造互換だけを確認する。自動更新や自動ダウングレードは行わない。
- アダプターで吸収できない破壊的変更、必要な拡張点の不足、または固定版の再現不能が確認された場合に限り、MITライセンス表示と上流追従手順を伴うsource内包を再検討する。

## 正本と担当

- `docs/spec/`（tanuki-spec）が要件・設計・テストの唯一の正本。仕様変更はここへ戻す。
- `.kiro/`（cc-sdd）は実装運用の領域。tanuki-spec は原則として配下を編集しない。唯一の例外として、承認済み正本をcc-sddへ渡す共通ブリッジが`spec.json`・`requirements.md`・`design.md`の3つを自動生成する。
- cc-sdd 側の `requirements.md` / `design.md` は、`docs/spec/` への参照カードまたは自動生成要約として扱い、手編集しない。
- cc-sdd の tasks/実装・検証は、承認済みの tanuki-spec 成果物から進める。

## cc-sddタスク生成への橋渡し

cc-sddの`kiro-spec-tasks`は、承認済み`spec.json`と数値要件IDを持つ`requirements.md`・`design.md`を必要とする。tanukiの`BR-xxx` / `FR-xxx` / `NFR-xxx`を手作業で複製せず、次のブリッジで薄い参照カードへ変換する。

```bash
python3 evaluation/cc_sdd_bridge.py render <project-root> \
  --phase <docs/spec/phase-N_名前> --func <func-名前> --spec <cc-sdd-spec名>
python3 evaluation/cc_sdd_bridge.py check <project-root> \
  --phase <docs/spec/phase-N_名前> --func <func-名前> --spec <cc-sdd-spec名>
```

- 要件IDは`traceability.yaml`の`in_scope` / `draft`順に`Requirement 1..N`へ決定論的に対応させ、対応表へtanuki IDを残す。
- `deferred` / `out_of_scope`は数値要件へ昇格せず、理由だけを対象外表へ残す。
- 設計要素は`design-traceability.yaml`から変換し、要件・基本設計・詳細設計の正本へ相対リンクする。本文は複製しない。
- 参照カードには`kiro-spec-tasks`がタスク生成前に全文を読む正本一覧を明記する。カードの短い要点だけでタスクを生成しない。
- 生成物には`tanuki-spec-cc-sdd-bridge-v1`所有マーカーを付ける。手書きspec、symlink、既存`tasks.md`があるディレクトリは上書きしない。
- 初回は未承認で生成する。tanukiのDoDとユーザー承認を終え、`draft`要件がゼロになった後だけ`render ... --approve`を実行する。
- 承認後は`kiro-spec-tasks <spec名>`を実行する。ブリッジ生成物を手編集せず、仕様変更は`docs/spec/`へ戻してタスク生成前に再生成する。

## 導入の安全条件

- v3 の Agent Skills（Codex: `.agents/skills/kiro-*/`、Claude: `.claude/skills/kiro-*/`）と、検証済み版が必要とする`.kiro/settings/`・Skill内rules/templates・エージェント別補助ファイルが全て揃った状態を現行形式とする。
- 状態は Codex/Claude 別に `modern` / `legacy` / `partial` / `missing` で判定する。
- 状態が `missing` のときだけ、互換性台帳で検証済みの公式コマンド（現在はCodex: `npx --yes cc-sdd@3.0.2 --codex-skills --lang ja`、Claude: `npx --yes cc-sdd@3.0.2 --claude-skills --lang ja`）を `--dry-run` → 本導入の順で実行する。
- `partial` / `legacy` は自動上書き・自動移行せず、中止して手動確認する。
- 既存の `AGENTS.md` / `CLAUDE.md` / `.kiro/` はプロジェクト資産として保護する。cc-sddのデフォルト`prompt`を使い、非TTYでは既存ファイルを保持して新規だけを追加する。cc-sdd側の`--yes`や`--overwrite force`は使わない。
- `--overwrite skip`も使わない。版によってはカテゴリ単位で新規Skillsまで省略し、不完全導入になるためである。
- プリフライトおよび導入コマンドは `shell=False` の引数配列で実行し、文字列シェル展開を行わない。
- dry-run前から存在する`AGENTS.md`・`CLAUDE.md`・`.agents/`・`.codex/`・`.claude/`・`.kiro/`のファイルはハッシュで保護し、変更・削除を検出したら成功扱いにしない。保護領域内のsymlinkはプロジェクト外への書き込みを避けるため自動導入を拒否する。
