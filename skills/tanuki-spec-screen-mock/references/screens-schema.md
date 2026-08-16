# screens.yaml の書き方

画面定義の正本。ここに書いた内容だけがモックHTMLと基本設計の画面一覧へ反映される。
使える部品とレイアウトは [`component-catalog.yaml`](./component-catalog.yaml) が共通カタログの正本であり、本ファイルでは再掲しない。案件固有の部品は、共通カタログを残したプロジェクト側の拡張版を用意し、`screens_gate.py --catalog <拡張版>`で検証する。既存ゲートは完全なカタログを受け取るため、追加差分だけのファイルではなく、共通定義と追加定義を含む解決済みファイルを渡す。

## meta

| キー | 必須 | 内容 |
| --- | --- | --- |
| `phase` | 必須 | フェーズ名。モックのタイトルになる |
| `source_spec` | 必須 | 根拠にした要件定義書のファイル名 |
| `generated_at` | 必須 | 生成日（YYYY-MM-DD） |
| `entry_screens` | 必須 | 入口となる画面IDの配列。ここから辿れない画面はエラーになる |

## screens[]

| キー | 必須 | 内容 |
| --- | --- | --- |
| `id` | 必須 | `SC-001` 形式。エラー画面は `SC-E01`、認証は `SC-L01`。重複不可 |
| `name` | 必須 | 画面名。基本設計の画面一覧にそのまま載る |
| `purpose` | 必須 | この画面でユーザが達成すること。1文 |
| `actor` | 必須 | 操作する役割 |
| `layout` | 必須 | カタログのレイアウト名 |
| `trace` | 必須 | 対応する要件ID（BR/FR/NFR）の配列。空配列（`[]`）は注意どまり。`trace:` と値を省くとNoneになりエラー |
| `design_question` | 必須 | この画面モックでレビューして決めたい問い |
| `hypothesis` | 必須 | 現時点で置く利用者・業務上の仮説 |
| `risk` | 必須 | 判断を誤ったときの影響と不確実性。`low` / `medium` / `high` |
| `validation_task` | 必須 | モックのレビュー参加者が行う具体的な操作・確認課題 |
| `rationale` | 必須 | 画面構成・導線・既存UIとの差分を採用した根拠 |
| `exploration_mode` | 必須 | `compare`（案を比較）または`inherit`（既存パターンを根拠付きで継承） |
| `inherited_from` | `inherit`時必須 | 継承元の画面、デザインシステム、業務パターンなど、確認できる参照先 |
| `alternatives` | 必須 | `compare`は2〜3案、`inherit`は採用案1件。いずれも採否理由を書く |
| `blocks` | 必須 | 上から順の部品。カタログの `type` のみ |
| `states` | 必須 | 5状態すべて。下記参照 |
| `state_strategy` | 必須 | リスクに応じて重点的にレビューする状態と、その理由 |
| `transitions` | 条件付き必須 | 遷移先がある画面は必須。`terminal: true` なら空でよい |
| `terminal` | 任意 | 意図的な終端画面なら `true`。行き止まり検出の例外になる |
| `notes` | 任意 | `[要確認: 質問]` を含む補足 |

## デザイン探索フィールド

画面は部品の充足だけで確定させず、`references/design-exploration.md`に従って利用者・業務・既存UI・ブランドを調査する。次の5項目は画面ごとに必須で、空欄や「未定」のような埋め草はゲートで弾く。

```yaml
design_question: "初回利用者が候補を比較して予約へ進めるか"
hypothesis: "日付を先に選ぶと候補を比較しやすい"
risk: medium
validation_task: "明日の午後の候補を探し、最初に押す場所を説明してください"
rationale: "既存予約画面の日付フィルタと用語を踏襲し、比較対象を先に絞る"
exploration_mode: compare
alternatives:
  - id: alt-filter-first
    name: "条件を先に絞る"
    summary: "日付と講師を先頭に置く"
    decision: adopted
    reason: "候補数を減らしやすく既存画面とも一致するため"
  - id: alt-calendar
    name: "カレンダー中心"
    summary: "月間カレンダーから日付を選ぶ"
    decision: rejected
    reason: "週単位の比較では情報密度が高くなるため"
```

判断を誤った影響や不確実性が高い画面は`exploration_mode: compare`とし、`alternatives`へ2〜3案を置く。`risk: high`ではこのモードが必須になる。

既存画面やデザインシステムに、今回も妥当なパターンがある低・中リスク画面は`exploration_mode: inherit`を選べる。この場合は案の数を増やさず、`inherited_from`に確認できる継承元を書き、`alternatives`は採用案1件だけにする。継承元があること自体ではなく、利用者・業務・制約が今回も同じであることを`rationale`で説明する。

```yaml
exploration_mode: inherit
inherited_from: "生徒ポータルの予約一覧 SC-010"
alternatives:
  - id: alt-existing-list
    name: "既存の一覧パターンを継承"
    summary: "同じ絞り込み順とカード構造を使う"
    decision: adopted
    reason: "利用者・対象データ・操作頻度が既存画面と同じため"
```

`decision`は`adopted`または`rejected`、採用案は常にちょうど1件とする。`summary`と`reason`は各案に必須で、案の名前だけの列挙は認めない。

## リスクに応じた状態設計

5状態（`normal` / `empty` / `loading` / `error` / `forbidden`）は最低限の比較軸として必ず残す。ただし、全状態を同じ厚さで深掘りする必要はない。`state_strategy.priority_states`にこの画面で重点的にレビューする状態を1件以上挙げ、`state_strategy.rationale`にリスクとの関係を書く。

```yaml
state_strategy:
  priority_states: [normal, error, forbidden]
  rationale: "予約確定の失敗と権限切れで、二重予約ややり直しが起きるため"
```

期限切れ、下書き、二重送信、承認待ちなど、案件固有の追加状態を共通の5状態へ機械的に追加しない。追加状態の表示・復旧方法は`notes`または`state_strategy.rationale`へ書く。追加状態が複数案件で共通化されると確認できた場合だけ、カタログやスキーマへの昇格を検討する。

## states

`normal` / `empty` / `loading` / `error` / `forbidden` の5キーをすべて書く。
該当しない状態は空にせず `該当なし: 理由` の形で理由まで書く。理由がないとエラーになる。

`states` で該当ありとした状態（`normal` を除く）ごとに、その状態を表す部品を
`blocks` に置く。部品がないとエラーになる（下記 `blocks[].state` 参照）。

## blocks[].state

`component-catalog.yaml` の `state_required`（`empty-state` / `alert` / `loading`）に
挙がる部品では `state` が必須。それ以外の部品では `state` を書くとエラーになる。

```yaml
blocks:
  - type: empty-state
    state: empty                    # 状態表現部品では必須。許可値は5状態
    message: 条件に合う枠がありません。日付を広げてください
```

許可値は `normal` / `empty` / `loading` / `error` / `forbidden` の5つだが、
部品ごとに使える値は `state_components` で決まる（`empty-state` は `empty` のみ、
`loading` は `loading` のみ、`alert` は `error` と `forbidden` の両方が使える）。

## blocks の入力項目

`filter-bar` と `form-section` は `fields` を持つ。各項目に次を書く。

| キー | 必須 | 内容 |
| --- | --- | --- |
| `label` | 必須 | 項目名 |
| `control` | 必須 | 入力方法（`text` / `date` / `select` / `number` など） |
| `required` | 必須 | `true` または `false` |
| `constraint` | `required: true` のとき推奨 | 入力制限。無いと `[要確認]` が立つ |
| `error` | `required: true` のとき推奨 | エラー文言。無いと `[要確認]` が立つ |

## transitions

| キー | 必須 | 内容 |
| --- | --- | --- |
| `action` | 必須 | 操作名（ボタンの文言）。`on` は YAML 1.1 で真偽値に解釈されるため使わない |
| `to` | 必須 | 遷移先の画面ID。存在しないIDはエラー |
| `kind` | 必須 | `forward` / `back` / `cancel` |

## 検証

```bash
python3 scripts/screens_gate.py <phase>/screens.yaml
```

エラーがあれば非0で終了する。`注意:` で始まる行は `[要確認]` として残してよいが、
`reports/01_差分・未決事項.md` へ転記する。
