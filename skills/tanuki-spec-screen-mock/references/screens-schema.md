# screens.yaml の書き方

画面定義の正本。ここに書いた内容だけがモックHTMLと基本設計の画面一覧へ反映される。
使える部品とレイアウトは [`component-catalog.yaml`](./component-catalog.yaml) が正本であり、本ファイルでは再掲しない。

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
| `blocks` | 必須 | 上から順の部品。カタログの `type` のみ |
| `states` | 必須 | 5状態すべて。下記参照 |
| `transitions` | 条件付き必須 | 遷移先がある画面は必須。`terminal: true` なら空でよい |
| `terminal` | 任意 | 意図的な終端画面なら `true`。行き止まり検出の例外になる |
| `notes` | 任意 | `[要確認: 質問]` を含む補足 |

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
