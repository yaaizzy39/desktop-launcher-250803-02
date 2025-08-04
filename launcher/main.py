#!/usr/bin/env python3
"""
Windows Desktop Launcher
常駐型ランチャーアプリケーション
"""

import sys
import os
import json
import ctypes
import ctypes.wintypes
from PyQt6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget, 
                            QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                            QMainWindow, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QAbstractNativeEventFilter
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget

from ui.group_icon import GroupIcon
from ui.item_list_window import ItemListWindow
from ui.settings_window import SettingsWindow
from data.data_manager import DataManager
from data.settings_manager import SettingsManager

# Windows API定数
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

class GlobalHotkeyFilter(QAbstractNativeEventFilter):
    """グローバルホットキーのイベントフィルター"""
    
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    
    def nativeEventFilter(self, eventType, message):
        if eventType == "windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(message.__int__())
            if msg.message == WM_HOTKEY:
                if msg.wParam == 1:  # ホットキーID 1
                    self.callback()
                    return True, 0
        return False, 0


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
        self.icons_visible = True  # アイコンの表示状態
        self.hotkey = None  # ホットキー
        self.hotkey_id = 1  # グローバルホットキーID
        self.hotkey_filter = None  # ホットキーフィルター
        
        # システムトレイ設定
        self.setup_system_tray()
        
        # 初期グループを読み込み
        self.load_groups()
        
        # 初期設定を適用
        self.apply_initial_settings()
        
        # ホットキーを設定
        self.setup_hotkey()
        
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
        
        # アイコン表示/非表示アクション
        toggle_action = QAction("アイコンを隠す", self)
        toggle_action.triggered.connect(self.toggle_icons_visibility)
        tray_menu.addAction(toggle_action)
        self.toggle_tray_action = toggle_action  # 後でテキストを更新するために保存
        
        tray_menu.addSeparator()
        
        # 終了アクション
        quit_action = QAction("終了", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def load_groups(self):
        """保存されたグループを読み込み"""
        groups_data = self.data_manager.load_groups()
        
        if not groups_data:
            # 初回起動時はデフォルトグループを作成（名前を指定してダイアログを回避）
            self.create_new_group("Apps", QPoint(100, 100))
        else:
            for group_data in groups_data:
                self.create_group_from_data(group_data)
                
    def create_new_group(self, name=None, position=None):
        """新しいグループアイコンを作成"""
        # 名前が指定されていない場合は入力ダイアログを表示
        if name is None:
            name, ok = QInputDialog.getText(
                None, 
                "新しいグループを作成", 
                "グループ名を入力してください:",
                text="New Group"
            )
            # キャンセルされた場合は作成しない
            if not ok or not name.strip():
                return None
            name = name.strip()
            
        if position is None:
            # デスクトップの中央あたりに配置
            position = QPoint(200, 200)
            
        group_icon = GroupIcon(name, position, self.settings_manager, self)
        group_icon.clicked.connect(self.show_item_list)
        group_icon.double_clicked.connect(self.show_item_list_pinned)
        group_icon.position_changed.connect(self.save_groups)
        group_icon.items_changed.connect(self.save_groups)
        
        self.group_icons.append(group_icon)
        
        # 設定を適用
        try:
            appearance_settings = self.settings_manager.get_appearance_settings()
            group_icon.apply_appearance_settings(appearance_settings)
        except Exception as e:
            print(f"新しいグループへの設定適用エラー: {e}")
        
        group_icon.show()
        
        # 名前入力後にアイコン設定も促す（初回起動時のデフォルトグループ作成時を除く）
        if name != "Apps":  # デフォルトグループでない場合
            reply = QMessageBox.question(
                None, 
                "アイコン設定", 
                f"グループ '{name}' が作成されました。\nカスタムアイコンを設定しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                group_icon.change_icon()
        
        # データを保存
        self.save_groups()
        
        return group_icon
        
    def create_group_from_data(self, group_data):
        """データからグループアイコンを作成"""
        group_icon = GroupIcon(
            group_data['name'], 
            QPoint(group_data['x'], group_data['y']),
            self.settings_manager,
            self
        )
        group_icon.items = group_data.get('items', [])
        group_icon.custom_icon_path = group_data.get('custom_icon_path', None)
        group_icon.clicked.connect(self.show_item_list)
        group_icon.double_clicked.connect(self.show_item_list_pinned)
        group_icon.position_changed.connect(self.save_groups)
        group_icon.items_changed.connect(self.save_groups)
        
        self.group_icons.append(group_icon)
        
        # 設定を適用
        try:
            appearance_settings = self.settings_manager.get_appearance_settings()
            group_icon.apply_appearance_settings(appearance_settings)
        except Exception as e:
            print(f"グループ復元時の設定適用エラー: {e}")
        
        group_icon.show()
        
    def show_item_list(self, group_icon):
        """アイテムリストウィンドウを表示"""
        # ウィンドウを作成または取得
        if group_icon not in self.item_list_windows:
            self.item_list_windows[group_icon] = ItemListWindow(group_icon)
            
        window = self.item_list_windows[group_icon]
        
        # グループアイコンにリストウィンドウの参照を設定
        group_icon.list_window = window
        
        # 既に表示されている場合は隠す（トグル動作）
        if window.isVisible():
            window.hide()
            return
            
        # グループアイコンの近くに表示（画面境界を考慮）
        self.position_window_near_icon(window, group_icon)
        window.show()
        window.raise_()
        window.activateWindow()
        
    def show_item_list_pinned(self, group_icon):
        """アイテムリストウィンドウを固定モードで表示"""
        # ウィンドウを作成または取得
        if group_icon not in self.item_list_windows:
            self.item_list_windows[group_icon] = ItemListWindow(group_icon)
            
        window = self.item_list_windows[group_icon]
        
        # グループアイコンにリストウィンドウの参照を設定
        group_icon.list_window = window
        
        # 固定モードで表示
        window.is_pinned = True
        window.update_title_display()
        
        # グループアイコンの近くに表示（画面境界を考慮）
        self.position_window_near_icon(window, group_icon)
        window.show()
        window.raise_()
        window.activateWindow()
        
    def position_window_near_icon(self, window, group_icon):
        """画面境界を考慮してウィンドウをグループアイコンの近くに配置"""
        # 画面情報を取得
        screen = self.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        screen_x = screen.x()
        screen_y = screen.y()
        
        # グループアイコンの位置とサイズ
        icon_pos = group_icon.pos()
        icon_size = group_icon.size()
        
        # ウィンドウのサイズ
        window_width = window.width()
        window_height = window.height()
        
        # デフォルトの配置（右側）
        default_x = icon_pos.x() + icon_size.width() + 10
        default_y = icon_pos.y()
        
        # 水平位置の調整
        if default_x + window_width > screen_x + screen_width:
            # 右側にはみ出る場合は左側に配置
            x = icon_pos.x() - window_width - 10
            # 左側にもはみ出る場合は画面内に収まる位置に調整
            if x < screen_x:
                x = max(screen_x, icon_pos.x() + icon_size.width() // 2 - window_width // 2)
        else:
            x = default_x
            
        # 垂直位置の調整
        if default_y + window_height > screen_y + screen_height:
            # 下側にはみ出る場合は上側に配置
            y = icon_pos.y() + icon_size.height() - window_height
            # 上側にもはみ出る場合は画面内に収まる位置に調整
            if y < screen_y:
                y = max(screen_y, icon_pos.y() + icon_size.height() // 2 - window_height // 2)
        else:
            y = default_y
            
        # 最終的に画面境界内に収める
        x = max(screen_x, min(x, screen_x + screen_width - window_width))
        y = max(screen_y, min(y, screen_y + screen_height - window_height))
        
        # ウィンドウを配置
        window.move(x, y)
        
    def save_groups(self):
        """グループデータを保存"""
        groups_data = []
        for group_icon in self.group_icons:
            group_data = {
                'name': group_icon.name,
                'x': group_icon.x(),
                'y': group_icon.y(),
                'items': group_icon.items,
                'custom_icon_path': group_icon.custom_icon_path
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
            
            # ホットキー設定を適用
            hotkey = settings.get('hotkey', {})
            if hotkey:
                print(f"ホットキー設定を適用中: {hotkey}")
                self.setup_hotkey()  # ホットキーを再設定
            
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
            
    def align_all_icons_vertically(self, target_x):
        """すべてのアイコンを縦整列（X位置を統一）"""
        try:
            for group_icon in self.group_icons:
                current_y = group_icon.y()
                group_icon.move(target_x, current_y)
            
            # 位置変更を保存
            self.save_groups()
            print(f"縦整列完了: X={target_x}")
            
        except Exception as e:
            print(f"縦整列エラー: {e}")
            QMessageBox.critical(None, "エラー", f"縦整列中にエラーが発生しました:\n{str(e)}")
            
    def align_all_icons_horizontally(self, target_y):
        """すべてのアイコンを横整列（Y位置を統一）"""
        try:
            for group_icon in self.group_icons:
                current_x = group_icon.x()
                group_icon.move(current_x, target_y)
            
            # 位置変更を保存
            self.save_groups()
            print(f"横整列完了: Y={target_y}")
            
        except Exception as e:
            print(f"横整列エラー: {e}")
            QMessageBox.critical(None, "エラー", f"横整列中にエラーが発生しました:\n{str(e)}")
        
    def quit_application(self):
        """アプリケーションを終了"""
        # ホットキーの登録を解除
        self.unregister_hotkey()
        
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
    
    def setup_hotkey(self):
        """グローバルホットキーを設定"""
        try:
            # 既存のホットキーを削除
            self.unregister_hotkey()
            
            # ホットキー設定を取得
            hotkey_settings = self.settings_manager.get_hotkey_settings()
            hotkey_str = hotkey_settings.get('toggle_visibility', 'Ctrl+Alt+L')
            print(f"ホットキー設定取得: {hotkey_str}")
            
            # ホットキー文字列を解析
            modifiers, vk_code = self.parse_hotkey_string(hotkey_str)
            if modifiers is not None and vk_code is not None:
                # グローバルホットキーを登録
                success = self.register_global_hotkey(modifiers, vk_code)
                if success:
                    print(f"グローバルホットキー登録成功: {hotkey_str}")
                    
                    # システムトレイに右クリックメニューでテスト追加（既存のものがあれば削除）
                    if hasattr(self, 'tray_icon'):
                        menu = self.tray_icon.contextMenu()
                        # 既存のテストアクションを削除
                        for action in menu.actions():
                            if action.text().startswith("テスト:"):
                                menu.removeAction(action)
                        
                        test_action = QAction("テスト: アイコン切り替え", self)
                        test_action.triggered.connect(self.toggle_icons_visibility)
                        menu.insertAction(menu.actions()[0], test_action)
                        menu.insertSeparator(menu.actions()[1])
                    
                else:
                    print(f"グローバルホットキー登録失敗: {hotkey_str}")
            else:
                print(f"ホットキー解析失敗: {hotkey_str}")
                
        except Exception as e:
            print(f"ホットキー設定エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def parse_hotkey_string(self, hotkey_str):
        """ホットキー文字列を解析してmodifiersとvk_codeを返す"""
        try:
            parts = hotkey_str.split('+')
            modifiers = 0
            vk_code = None
            
            for part in parts:
                part = part.strip().lower()
                if part == 'ctrl':
                    modifiers |= MOD_CONTROL
                elif part == 'alt':
                    modifiers |= MOD_ALT
                elif part == 'shift':
                    modifiers |= MOD_SHIFT
                elif part == 'win':
                    modifiers |= MOD_WIN
                else:
                    # キーコードを取得
                    if len(part) == 1 and part.isalpha():
                        # A-Z
                        vk_code = ord(part.upper())
                    elif part.isdigit() and len(part) == 1:
                        # 0-9
                        vk_code = ord(part)
                    else:
                        print(f"未対応のキー: {part}")
                        return None, None
            
            return modifiers, vk_code
            
        except Exception as e:
            print(f"ホットキー解析エラー: {e}")
            return None, None
    
    def register_global_hotkey(self, modifiers, vk_code):
        """グローバルホットキーを登録"""
        try:
            # 既存のフィルターを削除
            if self.hotkey_filter:
                self.removeNativeEventFilter(self.hotkey_filter)
            
            # Windows APIでグローバルホットキーを登録
            user32 = ctypes.windll.user32
            # RegisterHotKeyを直接呼び出し
            success = user32.RegisterHotKey(0, self.hotkey_id, modifiers, vk_code)
            
            if success:
                # イベントフィルターを設定
                self.hotkey_filter = GlobalHotkeyFilter(self.toggle_icons_visibility)
                self.installNativeEventFilter(self.hotkey_filter)
                print(f"RegisterHotKey成功: modifiers={modifiers}, vk_code={vk_code}")
                return True
            else:
                error = ctypes.windll.kernel32.GetLastError()
                print(f"RegisterHotKey失敗. エラーコード: {error}")
                return False
                
        except Exception as e:
            print(f"グローバルホットキー登録エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def unregister_hotkey(self):
        """ホットキーの登録を解除"""
        try:
            if self.hotkey_filter:
                self.removeNativeEventFilter(self.hotkey_filter)
                self.hotkey_filter = None
            
            # Windows APIでホットキーの登録を解除
            user32 = ctypes.windll.user32
            user32.UnregisterHotKey(0, self.hotkey_id)
            print("ホットキー登録解除")
            
        except Exception as e:
            print(f"ホットキー登録解除エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def toggle_icons_visibility(self):
        """アイコンの表示/非表示を切り替え"""
        try:
            print("toggle_icons_visibility が呼び出されました")
            self.icons_visible = not self.icons_visible
            print(f"表示状態を変更: {self.icons_visible}")
            
            print(f"グループアイコン数: {len(self.group_icons)}")
            for group_icon in self.group_icons:
                print(f"グループ '{group_icon.name}' を {'表示' if self.icons_visible else '非表示'}")
                if self.icons_visible:
                    group_icon.show()
                else:
                    group_icon.hide()
                    # リストウィンドウも隠す
                    if group_icon in self.item_list_windows:
                        print(f"リストウィンドウも非表示")
                        self.item_list_windows[group_icon].hide()
            
            # システムトレイメニューのテキストを更新
            if self.icons_visible:
                self.toggle_tray_action.setText("アイコンを隠す")
            else:
                self.toggle_tray_action.setText("アイコンを表示")
                
            print(f"アイコン表示状態: {'表示' if self.icons_visible else '非表示'}")
            
        except Exception as e:
            print(f"表示切り替えエラー: {e}")
            import traceback
            traceback.print_exc()


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