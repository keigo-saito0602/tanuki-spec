---
template: requirements
spec_items_version: "1.1.0"
status: draft
---

# 要件定義書テンプレート

> **ゴール**: ユーザーストーリー/顧客のしたいことを起点に、作るべきものの範囲と品質水準を確定する
> 👥 **読み手**: 非技術者（クライアント・経営視点）
> 🧭 **読み方**: まずサマリだけ読んで違和感を洗い出し、本論で裏取りする（2パス読み）
> 🔤 **凡例**: **太字** = 決定事項 / ⚠️ = リスク / ❓ = 未決事項
> 📎 **記入方法**: 末尾の「付録: 項目の根拠一覧」を参照する。

## サマリ（最初に読む）

### [必須] エグゼクティブサマリ（何を作る／なぜ／意思決定のお願い）
<!-- FILL:START req-exec-summary -->（未記入）<!-- FILL:END req-exec-summary -->

### [必須] 未決事項・スコープ外
<!-- FILL:START req-open-questions -->（未記入）<!-- FILL:END req-open-questions -->

### [任意] 決定事項サマリ（表）
> 📝 **記入形式**: `| 決定事項 | 決めた内容 | 根拠 |`
<!-- FILL:START req-decision-summary -->（未記入）<!-- FILL:END req-decision-summary -->

### [任意] 用語集
> 📝 **記入形式**: `| 用語 | 定義 |`
<!-- FILL:START req-glossary -->（未記入）<!-- FILL:END req-glossary -->

## 業務要件

### [必須] システム化の目的・背景（経営戦略との紐づけ）
<!-- FILL:START req-purpose -->（未記入）<!-- FILL:END req-purpose -->

### [必須] システム化対象業務・スコープ定義（対象/対象外/範囲）
> 📝 **記入形式**: `| 業務／機能 | 対象／対象外 | 理由 |`
<!-- FILL:START req-scope -->（未記入）<!-- FILL:END req-scope -->

### [必須] ステークホルダー・関係者体制（役割・権限・組織）
> 📝 **記入形式**: `| 関係者 | 役割 | 権限 |`
<!-- FILL:START req-stakeholder -->（未記入）<!-- FILL:END req-stakeholder -->

### [必須] 業務フロー（As-Is／To-Be、インパクト分析）
<!-- FILL:START req-bizflow -->（未記入）<!-- FILL:END req-bizflow -->

### [必須] ユーザーストーリー／利用シーン
<!-- FILL:START req-userstory -->（未記入）<!-- FILL:END req-userstory -->

> 🔍 **この節で確認すべきこと**
> - 目的は事業のねらいと整合しているか
> - スコープ内/外の線引きは明確で漏れがないか
> - 関係者の役割・権限に抜けはないか

## 機能要件

### [必須] 機能要件一覧・詳細（P5W2Hで整理）
> 📝 **記入形式**: `| 機能ID | 機能名 | 誰が・いつ・何を | 優先度 |`
<!-- FILL:START req-func-list -->（未記入）<!-- FILL:END req-func-list -->

### [必須] 要件の優先順位方針（分類・優先度基準）
<!-- FILL:START req-priority -->（未記入）<!-- FILL:END req-priority -->

> 🔍 **この節で確認すべきこと**
> - 各機能に「誰が・いつ・何を」が書かれているか
> - 優先度（Must/Should/Could）が付いているか
> - 例外・エラー時の振る舞いに触れているか

## データ要件

### [必須] データ要件・データモデル（ERD/DFD、CRUD分析）
<!-- FILL:START req-datamodel -->（未記入）<!-- FILL:END req-datamodel -->

### [必須] 入出力（画面・帳票）要件・UI標準
<!-- FILL:START req-io -->（未記入）<!-- FILL:END req-io -->

### [必須] 他システム連携・外部インターフェース要件
<!-- FILL:START req-interface -->（未記入）<!-- FILL:END req-interface -->

### [任意] コード設計・コード体系
> 📝 **記入形式**: `| コード名 | 桁数・形式 | 準拠標準／既存表 |`
<!-- FILL:START req-code -->（未記入）<!-- FILL:END req-code -->

> 🔍 **この節で確認すべきこと**
> - 扱うデータの種類・項目に漏れはないか
> - 個人情報・機微データの扱いが明示されているか
> - 画面・帳票の入出力が業務と一致しているか

## システム基盤・処理方式

### [必須] 処理方式・システム構成要件（オンライン/バッチ等の選定）
<!-- FILL:START req-processing -->（未記入）<!-- FILL:END req-processing -->

### [条件付] 業務パッケージ(PKG)導入時のFIT&GAP分析
- **適用条件**: 業務パッケージ/SaaSを採用する場合
<!-- FILL:START req-pkg-fitgap -->（未記入）<!-- FILL:END req-pkg-fitgap -->

> 🔍 **この節で確認すべきこと**
> - 処理方式（オンライン/バッチ等）が機能と整合しているか
> - 外部システム連携の授受方式・タイミングが明確か

## 非機能要件

### [必須] 非機能要件の観点別ブレークダウン
<!-- FILL:START req-nfr-breakdown -->（未記入）<!-- FILL:END req-nfr-breakdown -->

#### 非機能要件の個別明細

観点ごとに目標値・方式を記入する。確認指標は記入の手がかり。記入は1行にまとめ、
詳しい根拠が要る場合は付録を参照する。適用外は `[対象外: 理由]`、未定は `[要確認: 質問]` と書く。

##### 可用性
| 必須 | 項目 | 確認指標 | 記入 |
| --- | --- | --- | --- |
| 必須 | 継続性 | 運用時間/稼働率/RTO/RPO | <!-- FILL:START req-nfr-breakdown--nf-availability--01 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-availability--01 --> |
| 必須 | 耐障害性 | 機器/コンポーネント/ディスクの冗長化レベル | <!-- FILL:START req-nfr-breakdown--nf-availability--02 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-availability--02 --> |
| 必須 | 災害対策 | DRサイト/データ外部保管/再開目標日数 | <!-- FILL:START req-nfr-breakdown--nf-availability--03 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-availability--03 --> |
| 必須 | 回復性 | 復旧作業の自動化/代替業務運用範囲 | <!-- FILL:START req-nfr-breakdown--nf-availability--04 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-availability--04 --> |

##### 性能・拡張性
| 必須 | 項目 | 確認指標 | 記入 |
| --- | --- | --- | --- |
| 必須 | 業務処理量 | ユーザ数/同時数/データ量/処理件数 | <!-- FILL:START req-nfr-breakdown--nf-performance--01 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-performance--01 --> |
| 必須 | 性能目標値 | レスポンス順守率/スループット/帳票印刷能力 | <!-- FILL:START req-nfr-breakdown--nf-performance--02 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-performance--02 --> |
| 必須 | リソース拡張性 | 利用率上限/拡張倍率/スケールアップ・アウト | <!-- FILL:START req-nfr-breakdown--nf-performance--03 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-performance--03 --> |
| 必須 | 性能品質保証 | 帯域保証/性能テスト頻度/スパイク対応 | <!-- FILL:START req-nfr-breakdown--nf-performance--04 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-performance--04 --> |

##### 運用・保守性
| 必須 | 項目 | 確認指標 | 記入 |
| --- | --- | --- | --- |
| 必須 | 通常運用 | 運用時間/バックアップ方式/監視レベル | <!-- FILL:START req-nfr-breakdown--nf-operation--01 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-operation--01 --> |
| 必須 | 保守運用 | 計画停止頻度/パッチ適用方針/保守自動化率 | <!-- FILL:START req-nfr-breakdown--nf-operation--02 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-operation--02 --> |
| 必須 | 障害時運用 | 復旧自動化/駆けつけ時間/交換部材 | <!-- FILL:START req-nfr-breakdown--nf-operation--03 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-operation--03 --> |
| 必須 | 運用環境 | 開発試験環境/マニュアル/リモート操作 | <!-- FILL:START req-nfr-breakdown--nf-operation--04 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-operation--04 --> |
| 必須 | サポート体制 | 保守契約範囲/ライフサイクル/対応時間帯 | <!-- FILL:START req-nfr-breakdown--nf-operation--05 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-operation--05 --> |
| 任意 | その他運用管理方針 | インシデント/問題/構成/変更/リリース管理 | <!-- FILL:START req-nfr-breakdown--nf-operation--06 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-operation--06 --> |

##### 移行性
| 必須 | 項目 | 確認指標 | 記入 |
| --- | --- | --- | --- |
| 任意 | 移行時期 | 移行期間/停止可能日数/並行稼働 | <!-- FILL:START req-nfr-breakdown--nf-portability--01 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-portability--01 --> |
| 任意 | 移行方式 | 拠点・業務展開ステップ数 | <!-- FILL:START req-nfr-breakdown--nf-portability--02 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-portability--02 --> |
| 任意 | 移行対象(機器) | 設備入れ替え範囲 | <!-- FILL:START req-nfr-breakdown--nf-portability--03 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-portability--03 --> |
| 任意 | 移行対象(データ) | 移行データ量/形式差異/変換ルール数 | <!-- FILL:START req-nfr-breakdown--nf-portability--04 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-portability--04 --> |
| 任意 | 移行計画 | 作業分担/リハーサル回数/トラブル対処規定 | <!-- FILL:START req-nfr-breakdown--nf-portability--05 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-portability--05 --> |

##### セキュリティ
| 必須 | 項目 | 確認指標 | 記入 |
| --- | --- | --- | --- |
| 必須 | 前提条件・制約条件 | 準拠法令/資格認証/ガイドライン | <!-- FILL:START req-nfr-breakdown--nf-security--01 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-security--01 --> |
| 必須 | セキュリティリスク分析 | リスク分析対象範囲 | <!-- FILL:START req-nfr-breakdown--nf-security--02 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-security--02 --> |
| 必須 | セキュリティ診断 | NW/Web/DB脆弱性診断の実施 | <!-- FILL:START req-nfr-breakdown--nf-security--03 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-security--03 --> |
| 必須 | セキュリティリスク管理 | リスク見直し頻度/パッチ適用方針 | <!-- FILL:START req-nfr-breakdown--nf-security--04 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-security--04 --> |
| 必須 | アクセス・利用制限 | 認証方式/操作制限/認証情報管理 | <!-- FILL:START req-nfr-breakdown--nf-security--05 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-security--05 --> |
| 必須 | データの秘匿 | 伝送/蓄積の暗号化/鍵管理 | <!-- FILL:START req-nfr-breakdown--nf-security--06 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-security--06 --> |
| 必須 | 不正追跡・監視 | ログ取得/保管期間/監視範囲 | <!-- FILL:START req-nfr-breakdown--nf-security--07 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-security--07 --> |
| 必須 | ネットワーク対策 | FW/IPS/DoS対策 | <!-- FILL:START req-nfr-breakdown--nf-security--08 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-security--08 --> |
| 必須 | マルウェア対策 | 対策範囲/スキャン頻度 | <!-- FILL:START req-nfr-breakdown--nf-security--09 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-security--09 --> |
| 必須 | Web対策 | セキュアコーディング/WAF | <!-- FILL:START req-nfr-breakdown--nf-security--10 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-security--10 --> |
| 必須 | インシデント対応/復旧 | 対応体制の有無 | <!-- FILL:START req-nfr-breakdown--nf-security--11 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-security--11 --> |

##### システム環境・エコロジー
| 必須 | 項目 | 確認指標 | 記入 |
| --- | --- | --- | --- |
| 任意 | システム制約/前提条件 | 社内基準/法令/条例 | <!-- FILL:START req-nfr-breakdown--nf-environment--01 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-environment--01 --> |
| 任意 | システム特性 | ユーザ数/拠点数/対応言語数 | <!-- FILL:START req-nfr-breakdown--nf-environment--02 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-environment--02 --> |
| 任意 | 適合規格 | UL60950/RoHS/VCCI等 | <!-- FILL:START req-nfr-breakdown--nf-environment--03 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-environment--03 --> |
| 任意 | 機材設置環境条件 | 耐震/床荷重/電源/温湿度/空調 | <!-- FILL:START req-nfr-breakdown--nf-environment--04 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-environment--04 --> |
| 任意 | 環境マネージメント | 省エネ/CO2/騒音値 | <!-- FILL:START req-nfr-breakdown--nf-environment--05 -->（未記入）<!-- FILL:END req-nfr-breakdown--nf-environment--05 --> |

### [必須] 業務系非機能要件（業務運用視点の可用性・保守性・移行性等）
<!-- FILL:START req-nfr-business -->（未記入）<!-- FILL:END req-nfr-business -->

> 🔍 **この節で確認すべきこと**
> - 性能・可用性・セキュリティの目標が数値で書かれているか
> - 「対象外」とした非機能に理由があるか

## 品質・受け入れ

### [必須] 受け入れ条件・検収基準
<!-- FILL:START req-acceptance -->（未記入）<!-- FILL:END req-acceptance -->

### [必須] カットオーバークライテリア（サービス開始判定基準）
<!-- FILL:START req-cutover-criteria -->（未記入）<!-- FILL:END req-cutover-criteria -->

### [必須] 試験支援要件（試験環境・データ・シナリオ抽出可能性）
<!-- FILL:START req-test-support -->（未記入）<!-- FILL:END req-test-support -->

> 🔍 **この節で確認すべきこと**
> - 受け入れ条件が合否判定できる形になっているか
> - サービス開始判定（カットオーバー基準）があるか

## 移行・運用

### [必須] 移行要件・移行計画（方式・切り戻し・リハーサル・PoNR）
<!-- FILL:START req-migration-plan -->（未記入）<!-- FILL:END req-migration-plan -->

### [必須] 運用要件（通常/障害時/保守運用の作業分担）
<!-- FILL:START req-operation -->（未記入）<!-- FILL:END req-operation -->

### [任意] 業務改善効果・KPI測定項目
<!-- FILL:START req-kpi -->（未記入）<!-- FILL:END req-kpi -->

> 🔍 **この節で確認すべきこと**
> - 移行方式と失敗時の切り戻し手順があるか
> - 通常時・障害時の運用分担が決まっているか

## プロジェクト管理・ドキュメント

### [必須] 制約・前提条件
<!-- FILL:START req-constraints -->（未記入）<!-- FILL:END req-constraints -->

### [必須] 課題管理・検討経緯記録（不採用案・廃案理由を含む）
> 📝 **記入形式**: `| 課題 | 検討経緯 | 結論／廃案理由 |`
<!-- FILL:START req-issue-log -->（未記入）<!-- FILL:END req-issue-log -->

### [必須] 開発体制・スキル要件（要員計画）
> 📝 **記入形式**: `| 役割 | 必要スキル | 人数 |`
<!-- FILL:START req-team -->（未記入）<!-- FILL:END req-team -->

### [必須] 法規制・コンプライアンス対応要件
<!-- FILL:START req-compliance -->（未記入）<!-- FILL:END req-compliance -->

### [任意] ドキュメント体系・成果物一覧・用語統一
> 📝 **記入形式**: `| 成果物 | 目的 | 作成タイミング |`
<!-- FILL:START req-doc-system -->（未記入）<!-- FILL:END req-doc-system -->

> 🔍 **この節で確認すべきこと**
> - 予算・期間・技術の制約が明示されているか
> - 廃案・不採用の理由が記録されているか
> - 法規制・コンプライアンス対応が確認されているか

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
| `req-exec-summary` | エグゼクティブサマリ（何を作る／なぜ／意思決定のお願い） | 忙しい非技術者が1画面で判断できるよう結論を冒頭に置く | 認知科学(Minto/BLUF) | ドキュメンテーション |
| `req-open-questions` | 未決事項・スコープ外 | 決めていないことを可視化し空白を指摘できるようにする | 認知科学(未決明示) | ドキュメンテーション |
| `req-decision-summary` | 決定事項サマリ（表） | 決定を一覧化しスキャン読みで追えるようにする | 認知科学(チャンク化) | ドキュメンテーション |
| `req-glossary` | 用語集 | 専門用語を集約し本文の探索コストを下げる | 認知科学(Plain Language) | ドキュメンテーション |
| `req-purpose` | システム化の目的・背景（経営戦略との紐づけ） | 「真の目的」を明確化し、以後の要件取捨選択・優先順位判断の拠り所にする | 要件定義観点 S21/S107 | 機能性 |
| `req-scope` | システム化対象業務・スコープ定義（対象/対象外/範囲） | システム化範囲を確定し対象漏れ・認識齟齬を防ぐ | 要件品質観点(機能性)／要件定義観点 S21 | 機能性 |
| `req-stakeholder` | ステークホルダー・関係者体制（役割・権限・組織） | 所掌の違いによる要求スコープ・実現レベルの食い違いを防ぐ | 要件定義観点 S22/S56/S107 | 機能性 |
| `req-bizflow` | 業務フロー（As-Is／To-Be、インパクト分析） | 現状と新業務の変化・影響を可視化し見直し漏れを防ぐ | 要件定義観点 S23-25 | 機能性 |
| `req-userstory` | ユーザーストーリー／利用シーン | 利用者視点の利用文脈（Who/What/Why）を起点として明確化する | 叩き台／cc-sdd(spec-requirements) | 機能性、操作性 |
| `req-func-list` | 機能要件一覧・詳細（P5W2Hで整理） | Priority/Who/When&条件/What&量/Where/Why/How/HowMuchの見落としを防ぐ | 要件定義観点 S111 | 機能性 |
| `req-priority` | 要件の優先順位方針（分類・優先度基準） | 要件をグループ化し優先度判断をぶれさせない | 要件定義観点 S112 | 機能性 |
| `req-datamodel` | データ要件・データモデル（ERD/DFD、CRUD分析） | データ構造・流れを独立の柱で整理しDB設計との手戻りを防ぐ | 要件品質観点(機能性)／要件定義観点 S24/S36 | 機能性 |
| `req-io` | 入出力（画面・帳票）要件・UI標準 | 入出力様式・操作方法を統一し操作ミスを抑制する | 要件品質観点(操作性) | 操作性 |
| `req-interface` | 他システム連携・外部インターフェース要件 | 授受方式・タイミング・形式を明確化し結合試験の手戻りを防ぐ | 要件品質観点(機能性)／要件定義観点 S51 | 機能性 |
| `req-code` | コード設計・コード体系 | JIS/業界標準・既存コード表との整合を事前確認する | 要件品質観点(機能性) | 機能性 |
| `req-processing` | 処理方式・システム構成要件（オンライン/バッチ等の選定） | 機能要件と方式を整合させ開発規模・予算の見誤りを防ぐ | 要件定義観点 S26-27/S33 | 性能、拡張性 |
| `req-pkg-fitgap` | 業務パッケージ(PKG)導入時のFIT&GAP分析 | 過度なカスタマイズによる保守困難化・サポート切れを回避する | 要件定義観点 S28-30 | 機能性、保守性 |
| `req-nfr-breakdown` | 非機能要件の観点別ブレークダウン | 一括りの「非機能要件」での抜け漏れを防ぐ（詳細は non_functional を展開） | 要件品質観点(各シート)／要件定義観点 S73-83／非機能観点 | 信頼性、性能、拡張性、運用性、保守性、移行性、セキュリティ、システム環境エコロジー |
| `req-nfr-business` | 業務系非機能要件（業務運用視点の可用性・保守性・移行性等） | 基盤系だけでなく業務運用側の非機能も明文化する | 要件定義観点 S81-83 | 運用性、信頼性、移行性 |
| `req-acceptance` | 受け入れ条件・検収基準 | 完成の合格判定基準を明確にする。受け入れ条件はEARS 5パターン（常時/イベント駆動/状態駆動/異常系/オプション）で書き、具体シナリオは受入試験(AC)のGherkinへ落とす（references/ears-gherkin-guidelines.md） | 叩き台／cc-sdd(EARS受け入れ基準) | 機能性 |
| `req-cutover-criteria` | カットオーバークライテリア（サービス開始判定基準） | 本番移行可否を業務・システム・試験網羅性・品質・体制から段階判定する | 要件定義観点 S109-110 | 移行性、信頼性 |
| `req-test-support` | 試験支援要件（試験環境・データ・シナリオ抽出可能性） | 要件からテスト項目が導出できることを事前確認しV字の試験漏れを防ぐ | 要件品質観点(移行性)／要件定義観点 S116 | 信頼性 |
| `req-migration-plan` | 移行要件・移行計画（方式・切り戻し・リハーサル・PoNR） | 移行方式と失敗時の切り戻し手順を事前定義しトラブルを防ぐ | 要件品質観点(移行性)／要件定義観点 S51 | 移行性 |
| `req-operation` | 運用要件（通常/障害時/保守運用の作業分担） | 平常時・故障時・保全時の運用分担を明確化する | 要件品質観点(運用性/保守性) | 運用性、保守性 |
| `req-kpi` | 業務改善効果・KPI測定項目 | システム化効果を定量評価できる指標を要件段階で定義する | 要件品質観点(機能性/環境)／要件定義観点 S102 | システム環境エコロジー、機能性 |
| `req-constraints` | 制約・前提条件 | 予算・期間・技術等の制約を明示する | 叩き台 | 機能性 |
| `req-issue-log` | 課題管理・検討経緯記録（不採用案・廃案理由を含む） | 論点の蒸し返し時に判断根拠を遡れるようにし手戻りを防ぐ | 要件定義観点 S5/S111 | ドキュメンテーション |
| `req-team` | 開発体制・スキル要件（要員計画） | 必要な業務知識・技術知識を持つ人材確保を確認する | 要件定義観点 S22/S108 | 機能性 |
| `req-compliance` | 法規制・コンプライアンス対応要件 | 個人情報保護法・PCIDSS等への対応可否を要件段階で確認する | 要件品質観点(セキュリティ) | セキュリティ |
| `req-doc-system` | ドキュメント体系・成果物一覧・用語統一 | 粒度・用語を統一し後工程・保守での解釈齟齬を防ぐ | 要件品質観点(ドキュメンテーション)／要件定義観点 S113-115 | ドキュメンテーション |

