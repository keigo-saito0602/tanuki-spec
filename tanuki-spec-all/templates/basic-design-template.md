---
template: basic_design
spec_items_version: "1.2.0"
status: draft
---

# 基本設計書テンプレート

> **ゴール**: 外部から見える仕様（画面/API/帳票/外部IF/データ/非機能方針）を確定する
> 👥 **読み手**: 第三者の技術者
> 🧭 **読み方**: 実装者/テスター/運用セキュリティの3視点で読み分ける（PBR）
> 🔤 **凡例**: **太字** = 決定事項 / ⚠️ = リスク / ❓ = 未決事項
> 🔎 **第三者レビュー視点（PBR）**:
> - 実装者視点で確認: I/F・データ型・例外は実装可能な粒度か
> - テスター視点で確認: 各仕様に検証可能な合否条件があるか
> - 運用/セキュリティ視点で確認: 認証・ログ・権限・障害時が定義されているか
> 📎 **記入方法**: 末尾の「付録: 項目の根拠一覧」を参照する。

## 読者向け本文

> **記入ガイド**: この領域は品質項目の並びを写さず、案件の読者が判断する順序へ再編集する。
> サマリではなく、この本文だけで要件・設計判断が完結する内容にする。低リスク部分は表へ畳み、高リスク部分を深掘りする。

<!-- HUMAN:START -->
[要確認: 案件と読者に合わせた本文を作成してください]
<!-- HUMAN:END -->

---

## 付録: 監査用項目

以下はカバレッジ・根拠・トレーサビリティを検査するための領域。閲覧用HTMLでは表示しない。本文を複製せず、根拠と本文見出し・IDへの参照を記録する。

## サマリ（最初に読む）

### [必須] 設計判断サマリ（ADR: 決定／代替案／トレードオフ）
<!-- FILL:START bd-adr-summary -->（未記入）<!-- FILL:END bd-adr-summary -->

### [条件付] 用語集
- **適用条件**: 本書に固有の専門用語がある場合。一般的な開発用語は共通用語集にあるため、ここには本書固有の用語のみ記載する。
> 📝 **記入形式**: `| 用語 | 定義 |`
<!-- FILL:START bd-glossary -->（未記入）<!-- FILL:END bd-glossary -->

## 業務・機能設計

### [必須] 業務体系・業務処理概要（業務の全体像と、何をどう処理するかのあらまし）
<!-- FILL:START bd-biz-system -->（未記入）<!-- FILL:END bd-biz-system -->

### [必須] 処理起動条件一覧
> 📝 **記入形式**: `| 処理 | 種別（バッチ／オンライン） | 起動条件・契機 |`
<!-- FILL:START bd-trigger -->（未記入）<!-- FILL:END bd-trigger -->

### [必須] 業務規制条件・処理内容の明確化
<!-- FILL:START bd-biz-rule -->（未記入）<!-- FILL:END bd-biz-rule -->

### [必須] 機能一覧・機能仕様（入力/処理/出力定義）
> 📝 **記入形式**: `| 機能ID | 機能名 | INPUT | PROCESS | OUTPUT |`
<!-- FILL:START bd-func-spec -->（未記入）<!-- FILL:END bd-func-spec -->

### [必須] 処理方式の選定・確認（どのやり方で処理するかを決めて確かめる）
<!-- FILL:START bd-processing -->（未記入）<!-- FILL:END bd-processing -->

> 🔍 **この節で確認すべきこと**
> - 業務の分割・処理形態は変更に強いか
> - 各機能のINPUT/PROCESS/OUTPUTが定義されているか
> - 処理起動条件（バッチ/オンライン）に漏れはないか

## 画面・帳票・インターフェース設計

### [必須] 画面一覧・画面遷移設計
> 📝 **記入形式**: `| 画面ID | 画面名 | 遷移元→遷移先 | 主な操作 |`
<!-- FILL:START bd-screen -->（未記入）<!-- FILL:END bd-screen -->

### [必須] 入出力項目定義（データ項目・CRUD整理）
> 📝 **記入形式**: `| 項目名 | 型・桁・精度 | 編集書式 | CRUD |`
<!-- FILL:START bd-io-item -->（未記入）<!-- FILL:END bd-io-item -->

### [必須] メッセージ一覧・エラーメッセージ仕様
> 📝 **記入形式**: `| メッセージID | 区分（通知／警告／エラー） | 文言 | 発生条件 |`
<!-- FILL:START bd-message -->（未記入）<!-- FILL:END bd-message -->

### [必須] 外部インターフェース仕様（他システム連携）
<!-- FILL:START bd-ext-if -->（未記入）<!-- FILL:END bd-ext-if -->

### [条件付] 帳票一覧・帳票仕様
- **適用条件**: 帳票・PDF等の出力機能がある場合
> 📝 **記入形式**: `| 帳票ID | 帳票名 | 出力条件 | 様式／媒体 |`
<!-- FILL:START bd-report -->（未記入）<!-- FILL:END bd-report -->

### [条件付] API仕様（エンドポイント/リクエスト・レスポンス/認証/エラー）
- **適用条件**: WebAPI/RESTやモバイル連携を持つ場合
<!-- FILL:START bd-api -->（未記入）<!-- FILL:END bd-api -->

### [任意] コマンド・メニュー体系設計
<!-- FILL:START bd-menu -->（未記入）<!-- FILL:END bd-menu -->

> 🔍 **この節で確認すべきこと**
> - 画面遷移に抜け・重複はないか／権限で見えない画面を考慮したか
> - API・外部IFの契約（要求/応答/エラー/認証）が定義されているか
> - メッセージ・エラー表示の体系が統一されているか

## データ設計

### [必須] ER図・DB論理設計
<!-- FILL:START bd-erd -->（未記入）<!-- FILL:END bd-erd -->

### [必須] データファイル仕様・DB拡張計画
<!-- FILL:START bd-datafile -->（未記入）<!-- FILL:END bd-datafile -->

### [条件付] コード設計（コード体系）
- **適用条件**: 業務コード体系・採番規則を定義する場合
> 📝 **記入形式**: `| コード名 | 桁数・形式 | 採番規則／準拠標準 |`
<!-- FILL:START bd-code -->（未記入）<!-- FILL:END bd-code -->

> 🔍 **この節で確認すべきこと**
> - ER図のリレーション・キーに矛盾はないか
> - 容量・拡張の見積りがあるか
> - コード体系が標準・外部接続先と整合しているか

## 非機能・横断設計

### [必須] 非機能要件方針（可用性/性能拡張性/保守性/業務運用性/移行性/セキュリティ/環境）
<!-- FILL:START bd-nfr-policy -->（未記入）<!-- FILL:END bd-nfr-policy -->

#### 非機能要件の個別明細

観点ごとに目標値・方式を記入する。確認指標は記入の手がかり。
適用外は `[対象外: 理由]`、未定は `[要確認: 質問]` と書く。

##### 可用性

**継続性**［必須］（確認指標: 運用時間/稼働率/RTO/RPO）
<!-- FILL:START bd-nfr-policy--nf-availability--01 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-availability--01 -->

**耐障害性**［必須］（確認指標: 機器/コンポーネント/ディスクの冗長化レベル）
<!-- FILL:START bd-nfr-policy--nf-availability--02 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-availability--02 -->

**災害対策**［必須］（確認指標: DRサイト/データ外部保管/再開目標日数）
<!-- FILL:START bd-nfr-policy--nf-availability--03 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-availability--03 -->

**回復性**［必須］（確認指標: 復旧作業の自動化/代替業務運用範囲）
<!-- FILL:START bd-nfr-policy--nf-availability--04 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-availability--04 -->

##### 性能・拡張性

**業務処理量**［必須］（確認指標: ユーザ数/同時数/データ量/処理件数）
<!-- FILL:START bd-nfr-policy--nf-performance--01 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-performance--01 -->

**性能目標値**［必須］（確認指標: レスポンス順守率/スループット/帳票印刷能力）
<!-- FILL:START bd-nfr-policy--nf-performance--02 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-performance--02 -->

**リソース拡張性**［必須］（確認指標: 利用率上限/拡張倍率/スケールアップ・アウト）
<!-- FILL:START bd-nfr-policy--nf-performance--03 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-performance--03 -->

**性能品質保証**［必須］（確認指標: 帯域保証/性能テスト頻度/スパイク対応）
<!-- FILL:START bd-nfr-policy--nf-performance--04 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-performance--04 -->

##### 運用・保守性

**通常運用**［必須］（確認指標: 運用時間/バックアップ方式/監視レベル）
<!-- FILL:START bd-nfr-policy--nf-operation--01 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-operation--01 -->

**保守運用**［必須］（確認指標: 計画停止頻度/パッチ適用方針/保守自動化率）
<!-- FILL:START bd-nfr-policy--nf-operation--02 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-operation--02 -->

**障害時運用**［必須］（確認指標: 復旧自動化/駆けつけ時間/交換部材）
<!-- FILL:START bd-nfr-policy--nf-operation--03 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-operation--03 -->

**運用環境**［必須］（確認指標: 開発試験環境/マニュアル/リモート操作）
<!-- FILL:START bd-nfr-policy--nf-operation--04 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-operation--04 -->

**サポート体制**［必須］（確認指標: 保守契約範囲/ライフサイクル/対応時間帯）
<!-- FILL:START bd-nfr-policy--nf-operation--05 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-operation--05 -->

**その他運用管理方針**［任意］（確認指標: インシデント/問題/構成/変更/リリース管理）
<!-- FILL:START bd-nfr-policy--nf-operation--06 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-operation--06 -->

##### 移行性

**移行時期**［任意］（確認指標: 移行期間/停止可能日数/並行稼働）
<!-- FILL:START bd-nfr-policy--nf-portability--01 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-portability--01 -->

**移行方式**［任意］（確認指標: 拠点・業務展開ステップ数）
<!-- FILL:START bd-nfr-policy--nf-portability--02 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-portability--02 -->

**移行対象(機器)**［任意］（確認指標: 設備入れ替え範囲）
<!-- FILL:START bd-nfr-policy--nf-portability--03 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-portability--03 -->

**移行対象(データ)**［任意］（確認指標: 移行データ量/形式差異/変換ルール数）
<!-- FILL:START bd-nfr-policy--nf-portability--04 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-portability--04 -->

**移行計画**［任意］（確認指標: 作業分担/リハーサル回数/トラブル対処規定）
<!-- FILL:START bd-nfr-policy--nf-portability--05 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-portability--05 -->

##### セキュリティ

**前提条件・制約条件**［必須］（確認指標: 準拠法令/資格認証/ガイドライン）
<!-- FILL:START bd-nfr-policy--nf-security--01 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-security--01 -->

**セキュリティリスク分析**［必須］（確認指標: リスク分析対象範囲）
<!-- FILL:START bd-nfr-policy--nf-security--02 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-security--02 -->

**セキュリティ診断**［必須］（確認指標: NW/Web/DB脆弱性診断の実施）
<!-- FILL:START bd-nfr-policy--nf-security--03 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-security--03 -->

**セキュリティリスク管理**［必須］（確認指標: リスク見直し頻度/パッチ適用方針）
<!-- FILL:START bd-nfr-policy--nf-security--04 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-security--04 -->

**アクセス・利用制限**［必須］（確認指標: 認証方式/操作制限/認証情報管理）
<!-- FILL:START bd-nfr-policy--nf-security--05 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-security--05 -->

**データの秘匿**［必須］（確認指標: 伝送/蓄積の暗号化/鍵管理）
<!-- FILL:START bd-nfr-policy--nf-security--06 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-security--06 -->

**不正追跡・監視**［必須］（確認指標: ログ取得/保管期間/監視範囲）
<!-- FILL:START bd-nfr-policy--nf-security--07 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-security--07 -->

**ネットワーク対策**［必須］（確認指標: FW/IPS/DoS対策）
<!-- FILL:START bd-nfr-policy--nf-security--08 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-security--08 -->

**マルウェア対策**［必須］（確認指標: 対策範囲/スキャン頻度）
<!-- FILL:START bd-nfr-policy--nf-security--09 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-security--09 -->

**Web対策**［必須］（確認指標: セキュアコーディング/WAF）
<!-- FILL:START bd-nfr-policy--nf-security--10 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-security--10 -->

**インシデント対応/復旧**［必須］（確認指標: 対応体制の有無）
<!-- FILL:START bd-nfr-policy--nf-security--11 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-security--11 -->

##### システム環境・エコロジー

**システム制約/前提条件**［任意］（確認指標: 社内基準/法令/条例）
<!-- FILL:START bd-nfr-policy--nf-environment--01 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-environment--01 -->

**システム特性**［任意］（確認指標: ユーザ数/拠点数/対応言語数）
<!-- FILL:START bd-nfr-policy--nf-environment--02 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-environment--02 -->

**適合規格**［任意］（確認指標: UL60950/RoHS/VCCI等）
<!-- FILL:START bd-nfr-policy--nf-environment--03 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-environment--03 -->

**機材設置環境条件**［任意］（確認指標: 耐震/床荷重/電源/温湿度/空調）
<!-- FILL:START bd-nfr-policy--nf-environment--04 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-environment--04 -->

**環境マネージメント**［任意］（確認指標: 省エネ/CO2/騒音値）
<!-- FILL:START bd-nfr-policy--nf-environment--05 -->（未記入）<!-- FILL:END bd-nfr-policy--nf-environment--05 -->

### [必須] 横断的関心事（多くの機能に共通で必要な事柄：セキュリティ・プライバシー・可観測性）
<!-- FILL:START bd-cross-cutting -->（未記入）<!-- FILL:END bd-cross-cutting -->

### [必須] 非機能設計の5観点（信頼性・セキュリティ・コスト・運用・性能）
<!-- FILL:START bd-waf -->（未記入）<!-- FILL:END bd-waf -->

### [必須] セキュリティ方針（認証・アクセス制御の外部仕様）
<!-- FILL:START bd-security -->（未記入）<!-- FILL:END bd-security -->

> 🔍 **この節で確認すべきこと**
> - 認証・認可・ログ・監視が方針として定義されているか
> - 非機能のトレードオフが明示されているか

## 設計判断・品質・移行

### [必須] 重点整理事項の識別
<!-- FILL:START bd-critical -->（未記入）<!-- FILL:END bd-critical -->

### [必須] 代替案・採否理由・設計リスク
<!-- FILL:START bd-alternatives -->（未記入）<!-- FILL:END bd-alternatives -->

### [必須] 品質項目一覧の選択・設計方針への反映
> 📝 **記入形式**: `| 品質特性（ISO25010） | 採否 | 設計方針 |`
<!-- FILL:START bd-quality-select -->（未記入）<!-- FILL:END bd-quality-select -->

### [任意] 設計展開の軸・観点の設定
<!-- FILL:START bd-axis -->（未記入）<!-- FILL:END bd-axis -->

### [任意] 移行方式・移行対象概要
<!-- FILL:START bd-migration -->（未記入）<!-- FILL:END bd-migration -->

### [任意] ドキュメント体系・命名規則の規定
<!-- FILL:START bd-doc-rule -->（未記入）<!-- FILL:END bd-doc-rule -->

> 🔍 **この節で確認すべきこと**
> - 重要な設計判断に代替案と採否理由があるか
> - 未解決の設計リスクが列挙されているか

---

## 付録: 項目の根拠一覧

各項目が何のためにあるかの根拠をまとめる。記入担当のAIは、FILLを埋める前に該当IDの行を読む。
レビューでは、項目の網羅性や存在理由を疑うときだけ参照すればよい。

記入は次の2行を基本とする。

```text
- 結論: <決めた内容・数値・条件>          # 非機能の明細では <目標値・方式・対象外理由>
- 根拠: [入力] ユーザーストーリー「<該当箇所>」
```

根拠がない項目は `[要確認: 質問]`、適用対象外は `[対象外: 理由]` と書く。
「（未記入）」のまま残った項目は、カバレッジ評価で未充足として数えられる。

| ID | 項目 | 記入ガイド | 出典 | 品質観点 |
| --- | --- | --- | --- | --- |
| `bd-adr-summary` | 設計判断サマリ（ADR: 決定／代替案／トレードオフ） | 主要な設計判断を第三者が検証できる形で一覧化する | 認知科学(ADR/Nygard) | 保守性、ドキュメンテーション |
| `bd-glossary` | 用語集 | 専門用語を集約し本文の探索コストを下げる | 認知科学(Plain Language) | ドキュメンテーション |
| `bd-biz-system` | 業務体系・業務処理概要（業務の全体像と、何をどう処理するかのあらまし） | 仕様変更に強い業務分割・処理形態を明確化する | 設計品質観点(機能性) | 機能性 |
| `bd-trigger` | 処理起動条件一覧 | バッチ/オンライン/センタカットの起動条件を運用設計・試験の基礎にする | 設計品質観点(機能性) | 機能性、運用性 |
| `bd-biz-rule` | 業務規制条件・処理内容の明確化 | 規制すべきエラー種別・更新編集方法を明確化し詳細設計の土台にする | 設計品質観点(機能性) | 機能性 |
| `bd-func-spec` | 機能一覧・機能仕様（入力/処理/出力定義） | INPUT/PROCESS/OUTPUT単位で外部仕様を確定する | 設計観点 S16 | 機能性 |
| `bd-processing` | 処理方式の選定・確認（どのやり方で処理するかを決めて確かめる） | 処理方式を選定し非機能要件と整合させる | 設計観点 S13 | 性能 |
| `bd-screen` | 画面一覧・画面遷移設計 | 触れる画面と遷移を確定し漏れ・重複のないUI仕様にする | 設計品質観点(機能性) | 操作性、機能性 |
| `bd-io-item` | 入出力項目定義（データ項目・CRUD整理） | 桁数・精度・編集書式を統一し漏れ・重複を防ぐ | 設計品質観点(機能性) | 機能性 |
| `bd-message` | メッセージ一覧・エラーメッセージ仕様 | 通知・警告・エラーの内容と形式を統一する | 設計品質観点(機能性) | 操作性、機能性 |
| `bd-ext-if` | 外部インターフェース仕様（他システム連携） | 電文構造・送受手順を明確化し連携整合性を保証する | 設計品質観点(機能性) | 機能性 |
| `bd-report` | 帳票一覧・帳票仕様 | 出力帳票の種類・様式・条件を明確化する | 設計品質観点(機能性) | 機能性 |
| `bd-api` | API仕様（エンドポイント/リクエスト・レスポンス/認証/エラー） | Web/アプリ案件で内外のAPI契約を確定し実装・結合の齟齬を防ぐ（現代案件向け追補） | 叩き台(API)を外部IF仕様として具体化 | 機能性 |
| `bd-menu` | コマンド・メニュー体系設計 | 名称体系・操作方法を統一し操作ミスを防止する | 設計品質観点(機能性) | 操作性 |
| `bd-erd` | ER図・DB論理設計 | テーブル間リレーションとデータ構造を明確化する | 設計品質観点(機能性) | 機能性 |
| `bd-datafile` | データファイル仕様・DB拡張計画 | 拡張性・容量見積りを明確化し将来の業務拡大に備える | 設計品質観点(拡張性) | 拡張性 |
| `bd-code` | コード設計（コード体系） | コード体系化・標準採用・外部接続先との整合を取る | 設計品質観点(機能性) | 機能性 |
| `bd-nfr-policy` | 非機能要件方針（可用性/性能拡張性/保守性/業務運用性/移行性/セキュリティ/環境） | 横断で揃える非機能レベルを基本設計段階で方針化する | 設計観点 S50／非機能観点 | 信頼性、性能、拡張性、運用性、保守性、移行性、セキュリティ、システム環境エコロジー |
| `bd-cross-cutting` | 横断的関心事（多くの機能に共通で必要な事柄：セキュリティ・プライバシー・可観測性） | 機能ごとに見落としやすい横断要件を設計方針として明示する | 設計品質観点(Google: cross-cutting concerns) | セキュリティ、運用性、信頼性 |
| `bd-waf` | 非機能設計の5観点（信頼性・セキュリティ・コスト・運用・性能） | 非機能方針をトレードオフを含めて具体化し、運用後の品質劣化を防ぐ | 設計品質観点(Microsoft: Well-Architected) | 信頼性、セキュリティ、運用性、性能 |
| `bd-security` | セキュリティ方針（認証・アクセス制御の外部仕様） | 認証方式・権限レベルを外部仕様として定義する | 設計品質観点(セキュリティ) | セキュリティ |
| `bd-critical` | 重点整理事項の識別 | クリティカルな処理を洗い出し優先して方針を固める | 設計観点 S79 | 信頼性 |
| `bd-alternatives` | 代替案・採否理由・設計リスク | 実現案の比較、採用理由、未解決リスクを記録し、後続の判断を再現可能にする | 設計品質観点(Google: alternatives/risk) | 保守性、信頼性、ドキュメンテーション |
| `bd-quality-select` | 品質項目一覧の選択・設計方針への反映 | ISO25010系の観点を選択しプロジェクト特性に応じた設計方針として明文化する | 設計観点 S102 | ドキュメンテーション |
| `bd-axis` | 設計展開の軸・観点の設定 | 詳細設計への展開軸を仮検討し手戻りを防ぐ | 設計観点 S25 | 保守性 |
| `bd-migration` | 移行方式・移行対象概要 | 一括/段階移行の方式・対象範囲を明確化する | 設計品質観点(移行性) | 移行性 |
| `bd-doc-rule` | ドキュメント体系・命名規則の規定 | 管理番号体系・構成・改訂履歴ルールを定める | 設計品質観点(ドキュメンテーション) | ドキュメンテーション |

