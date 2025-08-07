# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iconLaunch - Windows用デスクトップランチャーアプリケーション
- プロファイル管理機能付きランチャー
- グループごとのアプリケーション管理
- 状態の保存・切り替え機能
- ホットキーによる瞬時の切り替え

## Development Setup

### Common Commands
- Run command: `python launcher/main.py`
- Build command: PyInstallerを使用してexe化
- Test command: 手動テスト（UIアプリケーションのため）

### Architecture Notes
- Project type: Desktop launcher application
- Technology stack: Python, PyQt6
- Main entry point: `launcher/main.py`
- Data storage: JSON形式でローカル設定フォルダに保存

## プロファイル管理機能

### 新機能の概要
1. **プロファイル管理システム**
   - ユーザーが状態に名前を付けて保存・管理
   - グループアイコンの配置、登録アプリ情報を含む完全な状態保存
   - 「仕事用」「遊び用」等、用途別の切り替え

2. **ホットキーによる瞬時切り替え**
   - Ctrl+Shift+F1〜F12で最大12個のプロファイルに瞬時切り替え
   - アプリケーション再起動不要

3. **既存機能との統合**
   - エクスポート/インポート機能はそのまま保持
   - 設定ウィンドウからプロファイル管理へのアクセス
   - システムトレイメニューからもアクセス可能

### ファイル構造
```
launcher/
├── main.py                 # メインアプリケーション（プロファイル機能統合済み）
├── data/
│   ├── data_manager.py     # グループデータ管理
│   ├── settings_manager.py # アプリケーション設定管理
│   └── profile_manager.py  # プロファイル管理（新規）
├── ui/
│   ├── group_icon.py       # グループアイコン
│   ├── item_list_window.py # アプリリスト
│   ├── settings_window.py  # 設定ウィンドウ（プロファイル管理ボタン追加）
│   └── profile_window.py   # プロファイル管理ウィンドウ（新規）
└── utils/
    └── shortcut_resolver.py
```

### 設定・データ保存場所
- メイン設定: `%APPDATA%/iconLaunch/`
- プロファイル: `%APPDATA%/iconLaunch/profiles/`
- 各プロファイル: `profiles/{プロファイル名}/profile.json`

## 使用方法

### プロファイル管理
1. システムトレイアイコン右クリック → 「プロファイル管理」
2. 設定ウィンドウ → 「プロファイル管理」ボタン
3. 新規作成、切り替え、名前変更、削除、エクスポート/インポートが可能

### ホットキー切り替え
- Ctrl+Shift+F1〜F12: プロファイル1〜12に瞬時切り替え
- システムトレイに通知表示
- 既に使用中のプロファイルの場合はスキップ

### 既存機能
- Ctrl+Alt+L: アイコン表示/非表示切り替え（従来通り）
- エクスポート/インポート機能も継続して利用可能

## 実装詳細

### 主要クラス
- `ProfileManager`: プロファイルのCRUD操作
- `ProfileWindow`: プロファイル管理UI
- `LauncherApp`: メインアプリケーション（プロファイル機能統合）

### 技術的特徴
- リアルタイム切り替え（再起動不要）
- WindowsグローバルホットキーAPI使用
- JSON形式での設定保存
- PyQt6シグナル・スロットによる疎結合設計