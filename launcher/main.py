#!/usr/bin/env python3
"""
Windows Desktop Launcher
常駐型ランチャーアプリケーション
"""

import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget, 
                            QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                            QMainWindow, QMessageBox)
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QAction

from ui.group_icon import GroupIcon
from ui.item_list_window import ItemListWindow
from ui.settings_window import SettingsWindow
from data.data_manager import DataManager
from data.settings_manager import SettingsManager


class LauncherApp(QApplication):
    """メインアプリケーションクラス"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        
        # データマネージャー初期化
        self.data_manager = DataManager()
        self.settings_manager = SettingsManager(self.data_manager)
        
        # グループアイコン管理
        self.group_icons = []
        self.item_list_windows = {}
        self.settings_window = None
        
        # システムトレイ設定
        self.setup_system_tray()
        
        # 初期グループを読み込み
        self.load_groups()
        
        # 初期設定を適用
        self.apply_initial_settings()
        
    def setup_system_tray(self):
        """システムトレイアイコンを設定"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # アイコンを作成（一時的に基本的なアイコン）
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(100, 100, 255))
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # コンテキストメニュー作成
        tray_menu = QMenu()
        
        # 新しいグループ作成アクション
        new_group_action = QAction("新しいグループを作成", self)
        new_group_action.triggered.connect(lambda: self.create_new_group())
        tray_menu.addAction(new_group_action)
        
        tray_menu.addSeparator()
        
        # 設定アクション
        settings_action = QAction("設定", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        # 情報アクション
        about_action = QAction("バージョン情報", self)
        about_action.triggered.connect(self.show_about)
        tray_menu.addAction(about_action)
        
        tray_menu.addSeparator()
        
        # 終了アクション
        quit_action = QAction("終了", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # トレイアイコンのメッセージ
        self.tray_icon.showMessage(
            "Desktop Launcher",
            "ランチャーアプリが起動しました\n右クリックでメニューを表示",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
        
    def load_groups(self):
        """保存されたグループを読み込み"""
        groups_data = self.data_manager.load_groups()
        
        if not groups_data:
            # 初回起動時はデフォルトグループを作成
            self.create_new_group("Apps", QPoint(100, 100))
        else:
            for group_data in groups_data:
                self.create_group_from_data(group_data)
                
    def create_new_group(self, name="New Group", position=None):
        """新しいグループアイコンを作成"""
        if position is None:
            # デスクトップの中央あたりに配置
            position = QPoint(200, 200)
            
        group_icon = GroupIcon(name, position, self.settings_manager)
        group_icon.clicked.connect(self.show_item_list)
        group_icon.double_clicked.connect(self.show_item_list_pinned)
        group_icon.position_changed.connect(self.save_groups)
        group_icon.items_changed.connect(self.save_groups)
        
        self.group_icons.append(group_icon)
        group_icon.show()
        
        # データを保存
        self.save_groups()
        
        return group_icon
        
    def create_group_from_data(self, group_data):
        """データからグループアイコンを作成"""
        group_icon = GroupIcon(
            group_data['name'], 
            QPoint(group_data['x'], group_data['y']),
            self.settings_manager
        )
        group_icon.items = group_data.get('items', [])
        group_icon.clicked.connect(self.show_item_list)
        group_icon.double_clicked.connect(self.show_item_list_pinned)
        group_icon.position_changed.connect(self.save_groups)
        group_icon.items_changed.connect(self.save_groups)
        
        self.group_icons.append(group_icon)
        group_icon.show()
        
    def show_item_list(self, group_icon):
        """アイテムリストウィンドウを表示"""
        # ウィンドウを作成または取得
        if group_icon not in self.item_list_windows:
            self.item_list_windows[group_icon] = ItemListWindow(group_icon)
            
        window = self.item_list_windows[group_icon]
        
        # 既に表示されている場合は隠す（トグル動作）
        if window.isVisible():
            window.hide()
            return
            
        # グループアイコンの近くに表示
        icon_pos = group_icon.pos()
        window.move(icon_pos.x() + 60, icon_pos.y())
        window.show()
        window.raise_()
        window.activateWindow()
        
    def show_item_list_pinned(self, group_icon):
        """アイテムリストウィンドウを固定モードで表示"""
        # ウィンドウを作成または取得
        if group_icon not in self.item_list_windows:
            self.item_list_windows[group_icon] = ItemListWindow(group_icon)
            
        window = self.item_list_windows[group_icon]
        
        # 固定モードで表示
        window.is_pinned = True
        window.update_title_display()
        
        # グループアイコンの近くに表示
        icon_pos = group_icon.pos()
        window.move(icon_pos.x() + 60, icon_pos.y())
        window.show()
        window.raise_()
        window.activateWindow()
        
    def save_groups(self):
        """グループデータを保存"""
        groups_data = []
        for group_icon in self.group_icons:
            group_data = {
                'name': group_icon.name,
                'x': group_icon.x(),
                'y': group_icon.y(),
                'items': group_icon.items
            }
            groups_data.append(group_data)
            
        self.data_manager.save_groups(groups_data)
        
    def show_settings(self):
        """設定ウィンドウを表示"""
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.settings_manager)
            self.settings_window.settings_applied.connect(self.apply_settings)
            
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
        
    def apply_settings(self, settings):
        """設定を適用"""
        try:
            # 外観設定を適用
            appearance = settings.get('appearance', {})
            print(f"外観設定を適用中: {appearance}")
            
            for group_icon in self.group_icons:
                print(f"グループアイコン '{group_icon.name}' に設定を適用中...")
                group_icon.apply_appearance_settings(appearance)
                
            # 動作設定を適用
            behavior = settings.get('behavior', {})
            
            # その他の設定適用処理をここに追加
            print("設定が適用されました")
            
        except Exception as e:
            print(f"設定適用エラー: {e}")
            QMessageBox.critical(None, "エラー", f"設定の適用中にエラーが発生しました:\n{str(e)}")
            
    def show_about(self):
        """バージョン情報を表示"""
        about_text = """
        <h3>Desktop Launcher</h3>
        <p><b>バージョン:</b> 1.0.0</p>
        <p><b>作成者:</b> Claude Code</p>
        <p><b>説明:</b> Windows用デスクトップランチャーアプリケーション</p>
        <hr>
        <p>アプリやフォルダをドラッグ&ドロップで登録し、<br>
        グループごとに分類して簡単に起動できます。</p>
        <p><b>機能:</b></p>
        <ul>
        <li>常駐機能（システムトレイ）</li>
        <li>ドラッグ&ドロップ対応</li>
        <li>グループ管理</li>
        <li>詳細設定</li>
        <li>自動バックアップ</li>
        </ul>
        """
        
        QMessageBox.about(None, "Desktop Launcher について", about_text)
        
    def apply_initial_settings(self):
        """初期設定を適用"""
        try:
            appearance_settings = self.settings_manager.get_appearance_settings()
            for group_icon in self.group_icons:
                group_icon.apply_appearance_settings(appearance_settings)
        except Exception as e:
            print(f"初期設定適用エラー: {e}")
        
    def quit_application(self):
        """アプリケーションを終了"""
        # 設定ウィンドウを閉じる
        if self.settings_window:
            self.settings_window.close()
            
        # 全てのウィンドウを閉じる
        for group_icon in self.group_icons:
            group_icon.close()
            
        for window in self.item_list_windows.values():
            window.close()
            
        # システムトレイから削除
        self.tray_icon.hide()
        
        # アプリケーション終了
        self.quit()


def main():
    """メイン関数"""
    # Windowsでの高DPI対応
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    app = LauncherApp(sys.argv)
    
    # システムトレイが利用可能かチェック
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Desktop Launcher",
                           "システムトレイが利用できません。")
        sys.exit(1)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()