# 洞窟探検RPG
Python 3.11とpygameで作成したシンプルな2Dロールプレイングゲームです。

## ゲーム概要
プレイヤーは洞窟の奥に隠された宝を探す冒険に出ます。ゲームは10回のイベントで構成され、最終イベントは必ず戦闘です。
- **クリア条件**: 10回目の戦闘に勝利して宝を入手する
- **ゲームオーバー条件**: いずれかの戦闘に敗北する

## 動作環境
- Python 3.11以上
- pygame 2.5以上

## インストール方法
1. Pythonをインストール: [Python公式サイト](https://www.python.org/downloads/)
2. pygameをインストール:
   ```
   pip install pygame>=2.5
   ```
3. `main.py`を実行:
   ```
   python main.py
   ```

## 操作方法
- **スペースキー**: タイトル画面でゲーム開始
- **矢印キー (<- ->)**: 選択肢の切り替え
- **Zキー**: 決定・メッセージ送り

## ゲームシステム

### イベントシステム
全10回のイベントがあり、以下の種類があります:

| 種別 | 説明 | 発生確率重み (前半 / 後半) |
|------|------|--------------------------|
| 分岐 | 通路が左右に分かれている。好きな方へ進む。 | 30 / 15 |
| 戦闘 | 洞窟生物と遭遇した！ | 10 / 40 |
| 休憩 | 静かな空間で少し休んだ。何も起こらない。 | 25 / 10 |
| 水   | 壁の割れ目から水が流れている。飲む／飲まない？ | 20 / 10 |
| 宝箱 | 古びた箱を発見。中身はランダム | 15 / 25 |

### 戦闘システム
- 10面サイコロ(1-10)で判定
- 敵ごとに「目標値」があり、出目 ≤ 目標値 で勝利
- プレイヤーのHP: 最大3、戦闘勝利時に20%の確率で1回復

### 敵の種類
| 名前 | 目標値 | 登場フェーズ |
|------|--------|--------------|
| コウモリ | 7 | 1-3 |
| ゴブリン | 6 | 2-5 |
| オーク | 5 | 4-7 |
| トロール | 4 | 6-9 |
| 洞窟王 | 3 | 10 (固定) |

## 技術情報
- 640×480ウィンドウ、60FPS
- 画像・音声なし（矩形とテキスト描画のみ）
- Python標準のrandomモジュール使用
- 単一ファイル構成

## 更新履歴
### 2025-06-13 更新
- 日本語化対応
  - 全テキストを日本語に翻訳
  - OS別の日本語フォント設定（Windows: Yu Gothic、macOS: Hiragino Sans、Linux: Noto Sans CJK JP）
- UI/UX改善
  - 一部表示の修正
  - テキスト表示画面でZキーを押すと次の画面に進むよう修正
  - 戦闘システムを二段階に分割（敵出現→ダイスロール）
  - タイトル画面に「全10フェーズの冒険」の説明を追加
- バグ修正
  - 宝箱から敵が出現した場合に敗北してもゲームオーバーにならない問題を修正

* このアプリケーション並びにREADME.mdファイルは、Amazon Q CLIで作成しました。