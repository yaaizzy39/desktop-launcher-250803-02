#!/usr/bin/env python3
"""
iconLaunch
常駐型ランチャーアプリケーション
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import __version__
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
from ui.profile_window import ProfileWindow
from data.data_manager import DataManager
from data.settings_manager import SettingsManager
from data.profile_manager import ProfileManager

# Windows API定数
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

# プロファイル切り替え用のホットキーID（F1-F12用）
PROFILE_HOTKEY_START_ID = 100

class GlobalHotkeyFilter(QAbstractNativeEventFilter):
    """グローバルホットキーのイベントフィルター"""
    
    def __init__(self, toggle_callback, profile_callback, app_instance):
        super().__init__()
        self.toggle_callback = toggle_callback
        self.profile_callback = profile_callback
        self.app_instance = app_instance
    
    def nativeEventFilter(self, eventType, message):
        if eventType == "windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(message.__int__())
            if msg.message == WM_HOTKEY:
                hotkey_id = msg.wParam
                print(f"[DEBUG] ホットキーイベント受信: ID={hotkey_id}")
                
                if hotkey_id == 1:  # ホットキーID 1 (表示切り替え)
                    print(f"[DEBUG] 表示切り替えホットキー実行")
                    self.toggle_callback()
                    return True, 0
                elif hotkey_id in self.app_instance.profile_hotkeys:  # 登録されたプロファイルホットキー
                    print(f"[DEBUG] プロファイル切り替えホットキー実行: ID={hotkey_id}")
                    self.profile_callback(hotkey_id)
                    return True, 0
                else:
                    print(f"[DEBUG] 未知のホットキーID: {hotkey_id}")
        return False, 0


class LauncherApp(QApplication):
    """メインアプリケーションクラス"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        
        # データマネージャー初期化
        self.data_manager = DataManager()
        self.settings_manager = SettingsManager(self.data_manager)
        self.profile_manager = ProfileManager(self.data_manager)
        
        # settings_managerにprofile_managerへの参照を設定
        self.settings_manager.profile_manager = self.profile_manager
        
        # グループアイコン管理
        self.group_icons = []
        self.item_list_windows = {}
        self.settings_window = None
        self.profile_window = None
        self.icons_visible = True  # アイコンの表示状態
        self.hotkey = None  # ホットキー
        self.hotkey_id = 1  # グローバルホットキーID
        self.hotkey_filter = None  # ホットキーフィルター
        self.profile_hotkeys = {}  # プロファイル切り替え用ホットキー
        
        # システムトレイ設定
        self.setup_system_tray()
        
        # 初期グループを読み込み
        self.load_groups()
        
        # 初期設定を適用
        self.apply_initial_settings()
        
        # アプリケーションアイコンを設定
        self.setup_app_icon()
        
        # ホットキーを設定
        self.setup_hotkey()
        
        # プロファイルホットキーを設定
        self.setup_profile_hotkeys()
        
    def load_app_icon(self):
        """アプリケーションアイコンを読み込み"""
        try:
            import os
            
            # ビルド環境かどうかを判定
            if getattr(sys, 'frozen', False):
                # PyInstallerでビルドされた環境
                # _internal/app_icon.icoを探す
                base_path = os.path.dirname(sys.executable)
                icon_path = os.path.join(base_path, "_internal", "app_icon.ico")
                print(f"ビルド環境でのアイコンファイル検索パス: {icon_path}")
            else:
                # 開発環境
                script_dir = os.path.dirname(os.path.abspath(__file__))
                icon_path = os.path.join(os.path.dirname(script_dir), "app_icon.ico")
                print(f"開発環境でのアイコンファイル検索パス: {icon_path}")
            
            if os.path.exists(icon_path):
                print(f"アイコンファイル見つかりました: {icon_path}")
                icon = QIcon(icon_path)
                if not icon.isNull():
                    print("アイコン読み込み成功")
                    return icon
                else:
                    print("アイコンファイルが無効です")
            else:
                print(f"アイコンファイルが見つかりません: {icon_path}")
                
        except Exception as e:
            print(f"アイコン読み込みエラー: {e}")
            
        return None
        
    def setup_app_icon(self):
        """アプリケーション全体のアイコンを設定"""
        app_icon = self.load_app_icon()
        if app_icon:
            # QApplicationのアイコンを設定（全ウィンドウに適用）
            self.setWindowIcon(app_icon)
            print("アプリケーションアイコン設定完了")
        
    def setup_system_tray(self):
        """システムトレイアイコンを設定"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # アプリケーションアイコンを設定
        app_icon = self.load_app_icon()
        if app_icon:
            self.tray_icon.setIcon(app_icon)
        else:
            # フォールバック：基本的なアイコン
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(100, 100, 255))
            self.tray_icon.setIcon(QIcon(pixmap))
        
        # コンテキストメニュー作成
        tray_menu = QMenu()
        
        # 新しいグループ作成アクション
        new_group_action = QAction("新しいグループを作成", self)
        new_group_action.triggered.connect(lambda: self.create_new_group())
        tray_menu.addAction(new_group_action)
        
        # プロファイル管理アクション
        profile_action = QAction("プロファイル管理", self)
        profile_action.triggered.connect(self.show_profile_manager)
        tray_menu.addAction(profile_action)
        
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
            self.create_default_group()
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
        
        # デフォルトアイコンをiconLaunchアプリアイコンに設定
        app_icon_path = self.get_app_icon_path()
        if app_icon_path:
            group_icon.custom_icon_path = app_icon_path
            print(f"[DEBUG] 新グループにデフォルトアイコン設定: {app_icon_path}")
        
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
        # アイテムデータを読み込み、チェック状態がないものはデフォルトでTrue
        items = group_data.get('items', [])
        for item in items:
            if 'checked' not in item:
                item['checked'] = True
        group_icon.items = items
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
        
    def create_default_group(self):
        """初回起動時のデフォルトグループを作成"""
        # デフォルトグループのデータを作成
        default_group_data = {
            'name': 'Apps',
            'x': 100,
            'y': 100,
            'custom_icon_path': self.get_app_icon_path(),
            'items': []
        }
        
        # グループを作成
        group_icon = self.create_group_from_data(default_group_data)
        print(f"デフォルトグループ作成: {default_group_data['custom_icon_path']}")
        return group_icon
        
    def get_app_icon_path(self):
        """アプリケーションアイコンのパスを取得"""
        try:
            # ビルド環境かどうかを判定
            if getattr(sys, 'frozen', False):
                # PyInstallerでビルドされた環境
                base_path = os.path.dirname(sys.executable)
                icon_path = os.path.join(base_path, "_internal", "app_icon.ico")
            else:
                # 開発環境
                script_dir = os.path.dirname(os.path.abspath(__file__))
                icon_path = os.path.join(os.path.dirname(script_dir), "app_icon.ico")
                
            if os.path.exists(icon_path):
                return icon_path
            else:
                print(f"アプリケーションアイコンが見つかりません: {icon_path}")
                return None
                
        except Exception as e:
            print(f"アプリケーションアイコンパス取得エラー: {e}")
            return None
        
    def show_item_list(self, group_icon):
        """アイテムリストウィンドウを表示"""
        # ウィンドウを作成または取得
        if group_icon not in self.item_list_windows:
            self.item_list_windows[group_icon] = ItemListWindow(group_icon, self.settings_manager)
            
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
            self.item_list_windows[group_icon] = ItemListWindow(group_icon, self.settings_manager)
            
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
        
        # アイコンが画面の右半分にある場合は左側に、左半分にある場合は右側にリストを配置
        icon_center_x = icon_pos.x() + icon_size.width() // 2
        screen_center_x = screen_x + screen_width // 2
        
        visual_gap = 3  # アイコンとリストの視覚的距離
        base_offset = 2
        size_factor = 0.30
        window_offset = base_offset + (icon_size.width() * size_factor)
        target_gap = visual_gap - window_offset
        
        if icon_center_x > screen_center_x:
            # アイコンが画面右半分にある場合：左側にリストを配置
            x = int(icon_pos.x() - window_width - target_gap)
            print(f"初期配置：リストを左側に配置 X={x} (アイコン中心={icon_center_x}, 画面中心={screen_center_x})")
        else:
            # アイコンが画面左半分にある場合：右側にリストを配置
            x = int(icon_pos.x() + icon_size.width() + target_gap)
            print(f"初期配置：リストを右側に配置 X={x} (アイコン中心={icon_center_x}, 画面中心={screen_center_x})")
        
        # 画面外はみ出しの最終調整
        if x < screen_x:
            x = screen_x + 5  # 左端に少し余白
            print(f"左端調整: {x}")
        elif x + window_width > screen_x + screen_width:
            x = screen_x + screen_width - window_width - 5  # 右端に少し余白
            print(f"右端調整: {x}")
        
        default_y = icon_pos.y()
            
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
        final_x = max(screen_x, min(x, screen_x + screen_width - window_width))
        final_y = max(screen_y, min(y, screen_y + screen_height - window_height))
        
        print(f"FINAL -> X:{final_x}, Y:{final_y}")
        
        # ウィンドウを配置
        window.move(final_x, final_y)
        
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
        
    def remove_group(self, group_icon):
        """グループを削除"""
        try:
            if group_icon in self.group_icons:
                self.group_icons.remove(group_icon)
                # データを保存
                self.save_groups()
                print(f"グループ '{group_icon.name}' を削除しました")
        except Exception as e:
            print(f"グループ削除エラー: {e}")
        
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
                
                # 対応するリストウィンドウがあれば設定を適用
                if group_icon in self.item_list_windows:
                    self.item_list_windows[group_icon].apply_appearance_settings()
                
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
        <h3>iconLaunch</h3>
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
        
        QMessageBox.about(None, "iconLaunch について", about_text)
        
    def apply_initial_settings(self):
        """初期設定を適用"""
        try:
            appearance_settings = self.settings_manager.get_appearance_settings()
            for group_icon in self.group_icons:
                group_icon.apply_appearance_settings(appearance_settings)
                
                # 対応するリストウィンドウがあれば設定を適用
                if group_icon in self.item_list_windows:
                    self.item_list_windows[group_icon].apply_appearance_settings()
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
        self.unregister_profile_hotkeys()
        
        # ウィンドウを閉じる
        if self.settings_window:
            self.settings_window.close()
            
        if self.profile_window:
            self.profile_window.close()
            
        # 全てのウィンドウを閉じる
        for group_icon in self.group_icons:
            group_icon.close()
            
        for window in self.item_list_windows.values():
            window.close()
            
        # システムトレイから削除
        self.tray_icon.hide()
        
        # アプリケーション終了
        self.quit()
        
    def restart_application(self):
        """アプリケーションを再起動"""
        try:
            import subprocess
            import sys
            import os
            
            print("アプリケーションを再起動中...")
            
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
            
            # 現在のPythonインタープリターとスクリプトパスを取得
            python_exe = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            
            print(f"Python実行ファイル: {python_exe}")
            print(f"スクリプトパス: {script_path}")
            print(f"実行引数: {sys.argv}")
            print(f"frozen状態: {getattr(sys, 'frozen', False)}")
            
            # 実行環境に応じて再起動方法を決定
            if getattr(sys, 'frozen', False):
                # PyInstallerでコンパイルされた実行ファイルの場合
                cmd = [script_path] + sys.argv[1:]
                print(f"実行コマンド（frozen）: {cmd}")
                subprocess.Popen(cmd, cwd=os.getcwd())
            else:
                # 通常のPythonスクリプトの場合
                cmd = [python_exe, script_path] + sys.argv[1:]
                print(f"実行コマンド（script）: {cmd}")
                subprocess.Popen(cmd, cwd=os.getcwd())
            
            print("新しいプロセスを開始しました。現在のプロセスを終了します。")
            
            # 少し待機してから終了
            QTimer.singleShot(500, self.quit)
            
        except Exception as e:
            print(f"再起動エラー: {e}")
            # 再起動に失敗した場合は通常の終了
            self.quit_application()
    
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
                    elif part.startswith('f') and len(part) > 1:
                        # F1-F12 ファンクションキー
                        try:
                            f_num = int(part[1:])
                            if 1 <= f_num <= 12:
                                # F1=0x70, F2=0x71, ..., F12=0x7B
                                vk_code = 0x70 + f_num - 1
                            else:
                                print(f"未対応のファンクションキー: {part}")
                                return None, None
                        except ValueError:
                            print(f"無効なファンクションキー: {part}")
                            return None, None
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
                self.hotkey_filter = GlobalHotkeyFilter(self.toggle_icons_visibility, self.switch_profile_by_hotkey, self)
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
            
    def show_profile_manager(self):
        """プロファイル管理ウィンドウを表示"""
        try:
            if self.profile_window is None:
                self.profile_window = ProfileWindow(self.profile_manager, self.settings_manager)
                self.profile_window.profile_switched.connect(self.on_profile_switched)
                self.profile_window.profiles_changed.connect(self.setup_profile_hotkeys)
                
            self.profile_window.show()
            self.profile_window.raise_()
            self.profile_window.activateWindow()
            
        except Exception as e:
            print(f"プロファイル管理ウィンドウ表示エラー: {e}")
            QMessageBox.critical(None, "エラー", f"プロファイル管理ウィンドウの表示中にエラーが発生しました:\n{str(e)}")
            
    def on_profile_switched(self, profile_name):
        """プロファイル切り替え時の処理"""
        try:
            print(f"プロファイル切り替え: {profile_name}")
            
            # 既存のグループアイコンを全て削除
            for group_icon in self.group_icons[:]:  # コピーを作成してイテレート
                group_icon.close()
                if group_icon in self.item_list_windows:
                    self.item_list_windows[group_icon].close()
                    del self.item_list_windows[group_icon]
            
            self.group_icons.clear()
            
            # 新しいプロファイルのグループを読み込み
            self.load_groups()
            
            # 外観設定を再適用
            self.apply_initial_settings()
            
            print(f"プロファイル切り替え完了: {profile_name}")
            
        except Exception as e:
            print(f"プロファイル切り替え処理エラー: {e}")
            import traceback
            traceback.print_exc()
            
    def switch_profile_by_hotkey(self, hotkey_id):
        """ホットキーによるプロファイル切り替え"""
        try:
            if hotkey_id not in self.profile_hotkeys:
                print(f"ホットキーID {hotkey_id} は登録されていません")
                return
            
            hotkey_info = self.profile_hotkeys[hotkey_id]
            if isinstance(hotkey_info, dict):
                profile_name = hotkey_info['name']
                hotkey_string = hotkey_info.get('hotkey_string', 'Unknown')
            else:
                # 旧形式の場合（後方互換性）
                profile_name = hotkey_info
                hotkey_string = "Unknown"
            
            current_profile = self.profile_manager.get_current_profile_name()
            
            # 現在のプロファイルと同じ場合はスキップ
            if profile_name == current_profile:
                print(f"既に '{profile_name}' を使用中です")
                return
                
            print(f"ホットキーでプロファイル切り替え: {hotkey_string} -> {profile_name}")
            
            # プロファイルを切り替え
            success, message = self.profile_manager.switch_to_profile(profile_name)
            
            if success:
                self.on_profile_switched(profile_name)
                # システムトレイ通知を無効化
                # if hasattr(self, 'tray_icon'):
                #     self.tray_icon.showMessage(
                #         "プロファイル切り替え",
                #         f"[{hotkey_string}] '{profile_name}' に切り替えました",
                #         QSystemTrayIcon.MessageIcon.Information,
                #         1500
                #     )
            else:
                print(f"プロファイル切り替え失敗: {message}")
                
        except Exception as e:
            print(f"ホットキープロファイル切り替えエラー: {e}")
            import traceback
            traceback.print_exc()
            
    def setup_profile_hotkeys(self):
        """プロファイル切り替え用ホットキーを設定"""
        try:
            print("=== プロファイルホットキー設定開始 ===")
            
            # 既存のプロファイルホットキーを削除
            self.unregister_profile_hotkeys()
            
            # プロファイル一覧を取得
            profiles = self.profile_manager.get_profile_list()
            print(f"利用可能プロファイル数: {len(profiles)}")
            
            if len(profiles) == 0:
                print("プロファイルが存在しないため、ホットキー設定をスキップ")
                return
            
            user32 = ctypes.windll.user32
            registered_count = 0
            failed_profiles = []
            
            # 各プロファイルに保存されたホットキー情報を使用
            for profile in profiles:
                profile_info = self.profile_manager.get_profile_info(profile['name'])
                if not profile_info or not profile_info.get('hotkey'):
                    print(f"プロファイル '{profile['name']}' にはホットキーが設定されていません")
                    continue
                else:
                    # ホットキー情報がある場合のみ詳細ログ
                    hotkey_data = profile_info.get('hotkey', {})
                    print(f"プロファイル '{profile['name']}' のホットキー: {hotkey_data.get('hotkey_string', 'N/A')}")
                    
                hotkey_info = profile_info['hotkey']
                if not hotkey_info or 'hotkey_string' not in hotkey_info:
                    print(f"プロファイル '{profile['name']}' のホットキー情報が無効です")
                    continue
                
                # ホットキー情報を解析
                hotkey_string = hotkey_info['hotkey_string']
                modifiers, vk_code = self.parse_hotkey_string(hotkey_string)
                
                if modifiers is None or vk_code is None:
                    print(f"プロファイル '{profile['name']}' のホットキー解析に失敗: {hotkey_string}")
                    failed_profiles.append(profile['name'])
                    continue
                
                # 動的なホットキーIDを生成（ホットキー文字列のハッシュベース）
                hotkey_id = PROFILE_HOTKEY_START_ID + hash(hotkey_string) % 1000
                
                print(f"ホットキー登録試行: {hotkey_string} -> {profile['name']} (ID={hotkey_id})")
                
                success = user32.RegisterHotKey(0, hotkey_id, modifiers, vk_code)
                if success:
                    self.profile_hotkeys[hotkey_id] = {
                        'name': profile['name'],
                        'hotkey_string': hotkey_string,
                        'modifier_name': hotkey_info.get('modifier', ''),
                        'key': hotkey_info.get('fkey', '')
                    }
                    registered_count += 1
                    print(f"[OK] プロファイルホットキー登録成功: {hotkey_string} -> {profile['name']}")
                else:
                    error = ctypes.windll.kernel32.GetLastError()
                    if error == 1409:  # ERROR_HOTKEY_ALREADY_REGISTERED
                        print(f"[NG] {hotkey_string} は既に使用中")
                    else:
                        print(f"[NG] {hotkey_string} 登録失敗: エラーコード {error}")
                    failed_profiles.append(profile['name'])
                    
            print(f"プロファイルホットキー設定完了: {registered_count}/{len(profiles)}個登録成功")
            
            # 登録成功したホットキーマッピングを表示
            print("\n=== 登録済みホットキーマッピング ===")
            for hotkey_id in sorted(self.profile_hotkeys.keys()):
                hotkey_info = self.profile_hotkeys[hotkey_id]
                if isinstance(hotkey_info, dict):
                    hotkey_string = hotkey_info.get('hotkey_string', 'Unknown')
                    profile_name = hotkey_info.get('name', 'Unknown')
                    print(f"  {hotkey_string} -> '{profile_name}'")
                else:
                    print(f"  (旧形式) -> '{hotkey_info}'")
            print("=====================================")
            
            if failed_profiles:
                print(f"[WARNING] 以下のプロファイルはホットキー登録に失敗しました: {', '.join(failed_profiles)}")
                print("  -> 他のアプリケーションと競合している可能性があります")
                print("  -> プロファイル管理ウィンドウで別のホットキーに変更してください")
            
            print("=== プロファイルホットキー設定終了 ===\n")
            
        except Exception as e:
            print(f"プロファイルホットキー設定エラー: {e}")
            import traceback
            traceback.print_exc()
            
    def unregister_profile_hotkeys(self):
        """プロファイル切り替え用ホットキーの登録を解除"""
        try:
            user32 = ctypes.windll.user32
            
            for hotkey_id in self.profile_hotkeys.keys():
                user32.UnregisterHotKey(0, hotkey_id)
                
            self.profile_hotkeys.clear()
            print("プロファイルホットキー登録解除完了")
            
        except Exception as e:
            print(f"プロファイルホットキー登録解除エラー: {e}")


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
        QMessageBox.critical(None, "iconLaunch",
                           "システムトレイが利用できません。")
        sys.exit(1)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()