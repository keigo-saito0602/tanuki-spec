Feature: 予約

  @AC-001 @US-001 @US-002 @FR-001 @FR-002
  Scenario: ログインしてから予約確定
    Given 空きレッスン枠がある
    When ログインする
    And 予約確定ボタンを押す
    Then 予約が確定する
