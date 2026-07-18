---
template: requirements
spec_items_version: "1.0.0"
status: draft
example: DJ教室レッスン予約機能
---

# 要件定義書（サンプル: DJ教室レッスン予約機能）

> 旧評価器で作成したドラフト例。非機能の個別明細と項目ごとの根拠が不足しているため、**出力ゲートは不通過**であり、実装へ引き渡してはいけない。

## 業務要件

### [必須] システム化の目的・背景（経営戦略との紐づけ）  <!-- spec-item: req-purpose -->
<!-- FILL:START req-purpose -->
- **根拠**: [入力] ユーザーストーリー「予約漏れや二重予約が起きる」
DM手動受付による予約漏れ・二重予約・講師の手間を解消し、予約体験の改善で受講継続率を高める。
<!-- FILL:END req-purpose -->

### [必須] システム化対象業務・スコープ定義（対象/対象外/範囲）  <!-- spec-item: req-scope -->
<!-- FILL:START req-scope -->
- **根拠**: [入力] ユーザーストーリー「空き枠を見て予約・キャンセルできる」
- 対象: 生徒によるレッスン枠の閲覧・予約・キャンセル・予約確認、確定通知
- 対象外: オンライン決済、講師シフトの自動最適化、キャンセル待ちの自動繰上げ（次フェーズ）
<!-- FILL:END req-scope -->

### [必須] ステークホルダー・関係者体制（役割・権限・組織）  <!-- spec-item: req-stakeholder -->
<!-- FILL:START req-stakeholder -->
生徒（予約する利用者）／講師・ユーザ（予約枠の登録・運営）／システム管理者（ユーザ兼務）。
<!-- FILL:END req-stakeholder -->

### [必須] 業務フロー（As-Is／To-Be、インパクト分析）  <!-- spec-item: req-bizflow -->
<!-- FILL:START req-bizflow -->
- As-Is: 生徒がDM送信 → 講師が台帳へ手記入 → 返信。二重予約・記入漏れが発生。
- To-Be: 生徒がアプリで空き枠を選択 → 即時確定 → 自動通知。台帳記入が不要になる。
<!-- FILL:END req-bizflow -->

### [必須] ユーザーストーリー／利用シーン  <!-- spec-item: req-userstory -->
<!-- FILL:START req-userstory -->
- **根拠**: [入力] ユーザーストーリー本文
生徒として、空いているレッスン枠をスマホから予約・キャンセルしたい。理由: 電話やDMをせず好きな時間に手続きしたいから。
<!-- FILL:END req-userstory -->

## 機能要件

### [必須] 機能要件一覧・詳細（P5W2Hで整理）  <!-- spec-item: req-func-list -->
<!-- FILL:START req-func-list -->
- F1 空き枠一覧表示（Who:生徒 / When:随時 / What:日時・講師・残席 / Why:選択のため）
- F2 枠予約（確定・確定通知送信）
- F3 予約キャンセル（When: レッスン前日まで）
- F4 予約履歴確認
- F5 満席枠は予約不可（残席0で締切）
<!-- FILL:END req-func-list -->

### [必須] 要件の優先順位方針（分類・優先度基準）  <!-- spec-item: req-priority -->
<!-- FILL:START req-priority -->
必須: F1/F2/F3/F5（予約が成立し二重予約が起きない最小構成）。次点: F4履歴。将来: キャンセル待ち。
<!-- FILL:END req-priority -->

## データ要件

### [必須] データ要件・データモデル（ERD/DFD、CRUD分析）  <!-- spec-item: req-datamodel -->
<!-- FILL:START req-datamodel -->
エンティティ: 生徒 / レッスン枠 / 予約。予約は「生徒 N:1 レッスン枠」。
枠は残席を持ち、予約確定でデクリメント（競合制御が必要→非機能・詳細設計へ）。
<!-- FILL:END req-datamodel -->

### [任意] コード設計・コード体系  <!-- spec-item: req-code -->
<!-- FILL:START req-code -->
予約ステータスコード（reserved / cancelled）と枠状態（open / full / closed）を定義する。
<!-- FILL:END req-code -->

### [必須] 入出力（画面・帳票）要件・UI標準  <!-- spec-item: req-io -->
<!-- FILL:START req-io -->
画面: 空き枠一覧 / 予約確認 / 予約履歴。UI標準: 既存 soil-groove のデザイントークンに準拠。
<!-- FILL:END req-io -->

### [必須] 他システム連携・外部インターフェース要件  <!-- spec-item: req-interface -->
<!-- FILL:START req-interface -->
確定/キャンセル通知はメール（＋将来LINE）。カレンダー連携は将来スコープ。
<!-- FILL:END req-interface -->

## システム基盤・処理方式

### [必須] 処理方式・システム構成要件（どのやり方で処理するか＝オンライン/バッチ等の選定）  <!-- spec-item: req-processing -->
<!-- FILL:START req-processing -->
オンライン中心（予約はリアルタイム確定）。バッチ: レッスン前日のリマインド通知（日次）。
基盤: 既存 soil-groove の Nuxt + Firebase 上に実装。
<!-- FILL:END req-processing -->

### [条件付] 業務パッケージ(PKG)導入時のFIT&GAP分析  <!-- spec-item: req-pkg-fitgap -->
<!-- FILL:START req-pkg-fitgap -->
対象外: 外部予約SaaS（STORES予約等）は採用せず、既存基盤に内製するため条件に該当しない。
<!-- FILL:END req-pkg-fitgap -->

## 非機能要件

### [必須] 非機能要件の観点別ブレークダウン  <!-- spec-item: req-nfr-breakdown -->
<!-- FILL:START req-nfr-breakdown -->
- 可用性（必須）: 平日夜の予約ピークに耐える。計画停止は生徒に事前告知。
- 性能・拡張性（必須）: 空き枠一覧の表示を1秒以内目標。生徒数増に耐える枠クエリ設計。
- 運用・保守性（必須）: 講師が枠を登録/締切できる管理画面。障害時は手動受付にフォールバック。
- 移行性（任意）: 既存台帳（スプレッドシート）から初期枠・生徒を投入。
- セキュリティ（必須）: 生徒はログイン必須。自分の予約のみ操作可（認可）。個人情報は最小限保持。
- システム環境・エコロジー（任意）: 対象外（既存基盤に相乗り）。
<!-- FILL:END req-nfr-breakdown -->

### [必須] 業務系非機能要件（業務運用視点の可用性・保守性・移行性等）  <!-- spec-item: req-nfr-business -->
<!-- FILL:START req-nfr-business -->
二重予約の禁止（残席の排他制御が業務規制）。講師都合の休講時に該当枠の予約を一斉キャンセルし通知する運用。
<!-- FILL:END req-nfr-business -->

## 品質・受け入れ

### [必須] 受け入れ条件・検収基準  <!-- spec-item: req-acceptance -->
<!-- FILL:START req-acceptance -->
- 生徒が空き枠を予約でき、確定通知が届く。
- レッスン前日までキャンセルでき、枠が空きに戻る。
- 満席（残席0）の枠は予約できない。
- 同一枠への二重予約が発生しない。
<!-- FILL:END req-acceptance -->

### [必須] カットオーバークライテリア（サービス開始判定基準）  <!-- spec-item: req-cutover-criteria -->
<!-- FILL:START req-cutover-criteria -->
主要動線（予約/キャンセル/一覧）のE2E通過、二重予約が発生しないことの負荷確認、既存生徒データ移行完了、講師が枠登録の操作に習熟済み。
<!-- FILL:END req-cutover-criteria -->

### [必須] 試験支援要件（試験環境・データ・シナリオ抽出可能性）  <!-- spec-item: req-test-support -->
<!-- FILL:START req-test-support -->
試験用のダミー生徒アカウントと枠データを用意。予約競合（同時に最後の1枠を予約）のテストシナリオを含める。
<!-- FILL:END req-test-support -->

## 移行・運用

### [必須] 移行要件・移行計画（方式・切り戻し・リハーサル・PoNR）  <!-- spec-item: req-migration-plan -->
<!-- FILL:START req-migration-plan -->
既存の手動予約台帳を初期データとして投入（一括移行）。切り戻し: 問題発生時は台帳運用に戻す。移行前に1週間の並行運用でリハーサル。
<!-- FILL:END req-migration-plan -->

### [必須] 運用要件（通常/障害時/保守運用の作業分担）  <!-- spec-item: req-operation -->
<!-- FILL:START req-operation -->
通常: 講師が月次で枠を登録。障害時: 手動予約受付にフォールバックし後で台帳反映。保守: 枠テンプレの更新はユーザ。
<!-- FILL:END req-operation -->

### [任意] 業務改善効果・KPI測定項目  <!-- spec-item: req-kpi -->
<!-- FILL:START req-kpi -->
（未記入）
<!-- FILL:END req-kpi -->

## プロジェクト管理・ドキュメント

### [必須] 制約・前提条件  <!-- spec-item: req-constraints -->
<!-- FILL:START req-constraints -->
予算・期間は小規模。既存 soil-groove（Nuxt/Firebase）上に実装。設計=Claude、実装=Codexの分業。
<!-- FILL:END req-constraints -->

### [必須] 課題管理・検討経緯記録（不採用案・廃案理由を含む）  <!-- spec-item: req-issue-log -->
<!-- FILL:START req-issue-log -->
- 決済連携は今回スコープ外（理由: 手数料と要件複雑化）。
- キャンセル待ち自動繰上げは次フェーズ（理由: まず予約成立の最小構成を優先）。
<!-- FILL:END req-issue-log -->

### [必須] 開発体制・スキル要件（要員計画）  <!-- spec-item: req-team -->
<!-- FILL:START req-team -->
ユーザ（設計判断・運営）／Claude（設計・レビュー）／Codex（実装）。
<!-- FILL:END req-team -->

### [必須] 法規制・コンプライアンス対応要件  <!-- spec-item: req-compliance -->
<!-- FILL:START req-compliance -->
氏名・連絡先を取得するためプライバシーポリシーに準拠し、保持は予約運用に必要な最小限とする。
<!-- FILL:END req-compliance -->

### [任意] ドキュメント体系・成果物一覧・用語統一  <!-- spec-item: req-doc-system -->
<!-- FILL:START req-doc-system -->
既存 soil-groove のドキュメント体系・用語（枠=slot, 予約=reservation）に合わせる。
<!-- FILL:END req-doc-system -->
