---
template: basic_design
spec_items_version: "1.1.0"
status: draft
---

# 基本設計書テンプレート

> **ゴール**: 外部から見える仕様（画面/API/帳票/外部IF/データ/非機能方針）を確定する
> 各項目の `<!-- FILL:START ... -->` と `END` の間に内容を記入する。
> 「（未記入）」のまま残っている項目はカバレッジ評価で未充足として数えられる。

## 基本設計項目

### [必須] 業務体系・業務処理概要  <!-- spec-item: bd-biz-system -->
- **記入ガイド**: 仕様変更に強い業務分割・処理形態を明確化する
- **出典**: 設計品質観点(機能性) ／ **品質観点**: 機能性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-biz-system -->
（未記入）
<!-- FILL:END bd-biz-system -->

### [必須] 処理起動条件一覧  <!-- spec-item: bd-trigger -->
- **記入ガイド**: バッチ/オンライン/センタカットの起動条件を運用設計・試験の基礎にする
- **出典**: 設計品質観点(機能性) ／ **品質観点**: 機能性、運用性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-trigger -->
（未記入）
<!-- FILL:END bd-trigger -->

### [必須] 業務規制条件・処理内容の明確化  <!-- spec-item: bd-biz-rule -->
- **記入ガイド**: 規制すべきエラー種別・更新編集方法を明確化し詳細設計の土台にする
- **出典**: 設計品質観点(機能性) ／ **品質観点**: 機能性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-biz-rule -->
（未記入）
<!-- FILL:END bd-biz-rule -->

### [必須] 画面一覧・画面遷移設計  <!-- spec-item: bd-screen -->
- **記入ガイド**: 触れる画面と遷移を確定し漏れ・重複のないUI仕様にする
- **出典**: 設計品質観点(機能性) ／ **品質観点**: 操作性、機能性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-screen -->
（未記入）
<!-- FILL:END bd-screen -->

### [必須] 帳票一覧・帳票仕様  <!-- spec-item: bd-report -->
- **記入ガイド**: 出力帳票の種類・様式・条件を明確化する
- **出典**: 設計品質観点(機能性) ／ **品質観点**: 機能性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-report -->
（未記入）
<!-- FILL:END bd-report -->

### [必須] 入出力項目定義（データ項目・CRUD整理）  <!-- spec-item: bd-io-item -->
- **記入ガイド**: 桁数・精度・編集書式を統一し漏れ・重複を防ぐ
- **出典**: 設計品質観点(機能性) ／ **品質観点**: 機能性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-io-item -->
（未記入）
<!-- FILL:END bd-io-item -->

### [必須] メッセージ一覧・エラーメッセージ仕様  <!-- spec-item: bd-message -->
- **記入ガイド**: 通知・警告・エラーの内容と形式を統一する
- **出典**: 設計品質観点(機能性) ／ **品質観点**: 操作性、機能性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-message -->
（未記入）
<!-- FILL:END bd-message -->

### [任意] コマンド・メニュー体系設計  <!-- spec-item: bd-menu -->
- **記入ガイド**: 名称体系・操作方法を統一し操作ミスを防止する
- **出典**: 設計品質観点(機能性) ／ **品質観点**: 操作性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-menu -->
（未記入）
<!-- FILL:END bd-menu -->

### [必須] 外部インターフェース仕様（他システム連携）  <!-- spec-item: bd-ext-if -->
- **記入ガイド**: 電文構造・送受手順を明確化し連携整合性を保証する
- **出典**: 設計品質観点(機能性) ／ **品質観点**: 機能性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-ext-if -->
（未記入）
<!-- FILL:END bd-ext-if -->

### [条件付] API仕様（エンドポイント/リクエスト・レスポンス/認証/エラー）  <!-- spec-item: bd-api -->
- **記入ガイド**: Web/アプリ案件で内外のAPI契約を確定し実装・結合の齟齬を防ぐ（現代案件向け追補）
- **適用条件**: WebAPI/RESTやモバイル連携を持つ場合
- **出典**: 叩き台(API)を外部IF仕様として具体化 ／ **品質観点**: 機能性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-api -->
（未記入）
<!-- FILL:END bd-api -->

### [必須] ER図・DB論理設計  <!-- spec-item: bd-erd -->
- **記入ガイド**: テーブル間リレーションとデータ構造を明確化する
- **出典**: 設計品質観点(機能性) ／ **品質観点**: 機能性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-erd -->
（未記入）
<!-- FILL:END bd-erd -->

### [必須] データファイル仕様・DB拡張計画  <!-- spec-item: bd-datafile -->
- **記入ガイド**: 拡張性・容量見積りを明確化し将来の業務拡大に備える
- **出典**: 設計品質観点(拡張性) ／ **品質観点**: 拡張性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-datafile -->
（未記入）
<!-- FILL:END bd-datafile -->

### [必須] コード設計（コード体系）  <!-- spec-item: bd-code -->
- **記入ガイド**: コード体系化・標準採用・外部接続先との整合を取る
- **出典**: 設計品質観点(機能性) ／ **品質観点**: 機能性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-code -->
（未記入）
<!-- FILL:END bd-code -->

### [必須] 機能一覧・機能仕様（入力/処理/出力定義）  <!-- spec-item: bd-func-spec -->
- **記入ガイド**: INPUT/PROCESS/OUTPUT単位で外部仕様を確定する
- **出典**: 設計観点 S16 ／ **品質観点**: 機能性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-func-spec -->
（未記入）
<!-- FILL:END bd-func-spec -->

### [必須] 処理方式の選定・確認  <!-- spec-item: bd-processing -->
- **記入ガイド**: 処理方式を選定し非機能要件と整合させる
- **出典**: 設計観点 S13 ／ **品質観点**: 性能
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-processing -->
（未記入）
<!-- FILL:END bd-processing -->

### [必須] 非機能要件方針（可用性/性能拡張性/保守性/業務運用性/移行性/セキュリティ/環境）  <!-- spec-item: bd-nfr-policy -->
- **記入ガイド**: 横断で揃える非機能レベルを基本設計段階で方針化する
- **出典**: 設計観点 S50／非機能観点 ／ **品質観点**: 信頼性、性能、拡張性、運用性、保守性、移行性、セキュリティ、システム環境エコロジー
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy -->
（未記入）

#### 非機能要件の個別明細

##### [必須] 可用性 / 継続性  <!-- spec-item: bd-nfr-policy--nf-availability--01 -->
- **確認指標**: 運用時間/稼働率/RTO/RPO
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-availability--01 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-availability--01 -->

##### [必須] 可用性 / 耐障害性  <!-- spec-item: bd-nfr-policy--nf-availability--02 -->
- **確認指標**: 機器/コンポーネント/ディスクの冗長化レベル
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-availability--02 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-availability--02 -->

##### [必須] 可用性 / 災害対策  <!-- spec-item: bd-nfr-policy--nf-availability--03 -->
- **確認指標**: DRサイト/データ外部保管/再開目標日数
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-availability--03 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-availability--03 -->

##### [必須] 可用性 / 回復性  <!-- spec-item: bd-nfr-policy--nf-availability--04 -->
- **確認指標**: 復旧作業の自動化/代替業務運用範囲
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-availability--04 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-availability--04 -->

##### [必須] 性能・拡張性 / 業務処理量  <!-- spec-item: bd-nfr-policy--nf-performance--01 -->
- **確認指標**: ユーザ数/同時数/データ量/処理件数
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-performance--01 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-performance--01 -->

##### [必須] 性能・拡張性 / 性能目標値  <!-- spec-item: bd-nfr-policy--nf-performance--02 -->
- **確認指標**: レスポンス順守率/スループット/帳票印刷能力
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-performance--02 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-performance--02 -->

##### [必須] 性能・拡張性 / リソース拡張性  <!-- spec-item: bd-nfr-policy--nf-performance--03 -->
- **確認指標**: 利用率上限/拡張倍率/スケールアップ・アウト
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-performance--03 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-performance--03 -->

##### [必須] 性能・拡張性 / 性能品質保証  <!-- spec-item: bd-nfr-policy--nf-performance--04 -->
- **確認指標**: 帯域保証/性能テスト頻度/スパイク対応
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-performance--04 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-performance--04 -->

##### [必須] 運用・保守性 / 通常運用  <!-- spec-item: bd-nfr-policy--nf-operation--01 -->
- **確認指標**: 運用時間/バックアップ方式/監視レベル
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-operation--01 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-operation--01 -->

##### [必須] 運用・保守性 / 保守運用  <!-- spec-item: bd-nfr-policy--nf-operation--02 -->
- **確認指標**: 計画停止頻度/パッチ適用方針/保守自動化率
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-operation--02 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-operation--02 -->

##### [必須] 運用・保守性 / 障害時運用  <!-- spec-item: bd-nfr-policy--nf-operation--03 -->
- **確認指標**: 復旧自動化/駆けつけ時間/交換部材
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-operation--03 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-operation--03 -->

##### [必須] 運用・保守性 / 運用環境  <!-- spec-item: bd-nfr-policy--nf-operation--04 -->
- **確認指標**: 開発試験環境/マニュアル/リモート操作
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-operation--04 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-operation--04 -->

##### [必須] 運用・保守性 / サポート体制  <!-- spec-item: bd-nfr-policy--nf-operation--05 -->
- **確認指標**: 保守契約範囲/ライフサイクル/対応時間帯
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-operation--05 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-operation--05 -->

##### [任意] 運用・保守性 / その他運用管理方針  <!-- spec-item: bd-nfr-policy--nf-operation--06 -->
- **確認指標**: インシデント/問題/構成/変更/リリース管理
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-operation--06 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-operation--06 -->

##### [任意] 移行性 / 移行時期  <!-- spec-item: bd-nfr-policy--nf-portability--01 -->
- **確認指標**: 移行期間/停止可能日数/並行稼働
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-portability--01 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-portability--01 -->

##### [任意] 移行性 / 移行方式  <!-- spec-item: bd-nfr-policy--nf-portability--02 -->
- **確認指標**: 拠点・業務展開ステップ数
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-portability--02 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-portability--02 -->

##### [任意] 移行性 / 移行対象(機器)  <!-- spec-item: bd-nfr-policy--nf-portability--03 -->
- **確認指標**: 設備入れ替え範囲
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-portability--03 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-portability--03 -->

##### [任意] 移行性 / 移行対象(データ)  <!-- spec-item: bd-nfr-policy--nf-portability--04 -->
- **確認指標**: 移行データ量/形式差異/変換ルール数
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-portability--04 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-portability--04 -->

##### [任意] 移行性 / 移行計画  <!-- spec-item: bd-nfr-policy--nf-portability--05 -->
- **確認指標**: 作業分担/リハーサル回数/トラブル対処規定
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-portability--05 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-portability--05 -->

##### [必須] セキュリティ / 前提条件・制約条件  <!-- spec-item: bd-nfr-policy--nf-security--01 -->
- **確認指標**: 準拠法令/資格認証/ガイドライン
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-security--01 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-security--01 -->

##### [必須] セキュリティ / セキュリティリスク分析  <!-- spec-item: bd-nfr-policy--nf-security--02 -->
- **確認指標**: リスク分析対象範囲
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-security--02 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-security--02 -->

##### [必須] セキュリティ / セキュリティ診断  <!-- spec-item: bd-nfr-policy--nf-security--03 -->
- **確認指標**: NW/Web/DB脆弱性診断の実施
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-security--03 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-security--03 -->

##### [必須] セキュリティ / セキュリティリスク管理  <!-- spec-item: bd-nfr-policy--nf-security--04 -->
- **確認指標**: リスク見直し頻度/パッチ適用方針
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-security--04 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-security--04 -->

##### [必須] セキュリティ / アクセス・利用制限  <!-- spec-item: bd-nfr-policy--nf-security--05 -->
- **確認指標**: 認証方式/操作制限/認証情報管理
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-security--05 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-security--05 -->

##### [必須] セキュリティ / データの秘匿  <!-- spec-item: bd-nfr-policy--nf-security--06 -->
- **確認指標**: 伝送/蓄積の暗号化/鍵管理
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-security--06 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-security--06 -->

##### [必須] セキュリティ / 不正追跡・監視  <!-- spec-item: bd-nfr-policy--nf-security--07 -->
- **確認指標**: ログ取得/保管期間/監視範囲
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-security--07 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-security--07 -->

##### [必須] セキュリティ / ネットワーク対策  <!-- spec-item: bd-nfr-policy--nf-security--08 -->
- **確認指標**: FW/IPS/DoS対策
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-security--08 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-security--08 -->

##### [必須] セキュリティ / マルウェア対策  <!-- spec-item: bd-nfr-policy--nf-security--09 -->
- **確認指標**: 対策範囲/スキャン頻度
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-security--09 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-security--09 -->

##### [必須] セキュリティ / Web対策  <!-- spec-item: bd-nfr-policy--nf-security--10 -->
- **確認指標**: セキュアコーディング/WAF
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-security--10 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-security--10 -->

##### [必須] セキュリティ / インシデント対応/復旧  <!-- spec-item: bd-nfr-policy--nf-security--11 -->
- **確認指標**: 対応体制の有無
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-security--11 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-security--11 -->

##### [任意] システム環境・エコロジー / システム制約/前提条件  <!-- spec-item: bd-nfr-policy--nf-environment--01 -->
- **確認指標**: 社内基準/法令/条例
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-environment--01 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-environment--01 -->

##### [任意] システム環境・エコロジー / システム特性  <!-- spec-item: bd-nfr-policy--nf-environment--02 -->
- **確認指標**: ユーザ数/拠点数/対応言語数
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-environment--02 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-environment--02 -->

##### [任意] システム環境・エコロジー / 適合規格  <!-- spec-item: bd-nfr-policy--nf-environment--03 -->
- **確認指標**: UL60950/RoHS/VCCI等
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-environment--03 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-environment--03 -->

##### [任意] システム環境・エコロジー / 機材設置環境条件  <!-- spec-item: bd-nfr-policy--nf-environment--04 -->
- **確認指標**: 耐震/床荷重/電源/温湿度/空調
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-environment--04 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-environment--04 -->

##### [任意] システム環境・エコロジー / 環境マネージメント  <!-- spec-item: bd-nfr-policy--nf-environment--05 -->
- **確認指標**: 省エネ/CO2/騒音値
<!-- 記入例: - 結論: <目標値・方式・対象外理由>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-nfr-policy--nf-environment--05 -->
（未記入）
<!-- FILL:END bd-nfr-policy--nf-environment--05 -->

<!-- FILL:END bd-nfr-policy -->

### [必須] 重点整理事項の識別  <!-- spec-item: bd-critical -->
- **記入ガイド**: クリティカルな処理を洗い出し優先して方針を固める
- **出典**: 設計観点 S79 ／ **品質観点**: 信頼性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-critical -->
（未記入）
<!-- FILL:END bd-critical -->

### [任意] 設計展開の軸・観点の設定  <!-- spec-item: bd-axis -->
- **記入ガイド**: 詳細設計への展開軸を仮検討し手戻りを防ぐ
- **出典**: 設計観点 S25 ／ **品質観点**: 保守性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-axis -->
（未記入）
<!-- FILL:END bd-axis -->

### [必須] セキュリティ方針（認証・アクセス制御の外部仕様）  <!-- spec-item: bd-security -->
- **記入ガイド**: 認証方式・権限レベルを外部仕様として定義する
- **出典**: 設計品質観点(セキュリティ) ／ **品質観点**: セキュリティ
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-security -->
（未記入）
<!-- FILL:END bd-security -->

### [任意] 移行方式・移行対象概要  <!-- spec-item: bd-migration -->
- **記入ガイド**: 一括/段階移行の方式・対象範囲を明確化する
- **出典**: 設計品質観点(移行性) ／ **品質観点**: 移行性
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-migration -->
（未記入）
<!-- FILL:END bd-migration -->

### [必須] 品質項目一覧の選択・設計方針への反映  <!-- spec-item: bd-quality-select -->
- **記入ガイド**: ISO25010系の観点を選択しプロジェクト特性に応じた設計方針として明文化する
- **出典**: 設計観点 S102 ／ **品質観点**: ドキュメンテーション
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-quality-select -->
（未記入）
<!-- FILL:END bd-quality-select -->

### [任意] ドキュメント体系・命名規則の規定  <!-- spec-item: bd-doc-rule -->
- **記入ガイド**: 管理番号体系・構成・改訂履歴ルールを定める
- **出典**: 設計品質観点(ドキュメンテーション) ／ **品質観点**: ドキュメンテーション
<!-- 記入例: - 結論: <決めた内容・数値・条件>\n- 根拠: [入力] ユーザーストーリー「<該当箇所>」 -->
<!-- FILL:START bd-doc-rule -->
（未記入）
<!-- FILL:END bd-doc-rule -->

