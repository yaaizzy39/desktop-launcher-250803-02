"""
ItemListWindow - 登録されたアイテムのリストを表示するウィンドウ
"""

import os
import subprocess
import sys
import win32com.client
import win32gui
import win32con
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                            QPushButton, QLabel, QFrame, QApplication,
                            QMessageBox, QMenu, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QMimeData, QUrl, QPoint, QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction, QDrag, QPainter, QCursor, QPen, QColor
from ui.icon_utils import icon_extractor


class ItemWidget(QFrame):
    """個別アイテムを表示するウィジェット"""
    
    launch_requested = pyqtSignal(str)  # 起動要求シグナル
    remove_requested = pyqtSignal(str)  # 削除要求シグナル
    reorder_requested = pyqtSignal(object, int)  # 並び替え要求シグナル (item_widget, new_index)
    
    def __init__(self, item_info, settings_manager=None):
        super().__init__()
        self.item_info = item_info
        self.settings_manager = settings_manager
        self.drag_start_position = None
        self.is_reorder_drag = False  # 並び替えドラッグかどうか
        self.drop_position = None  # ドロップ位置を保存
        # チェック状態をitem_infoに追加（デフォルトはTrue）
        if 'checked' not in self.item_info:
            self.item_info['checked'] = True
        self.setup_ui()
        
    def setup_ui(self):
        """UI設定"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 240);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 5px;
                margin: 1px;
            }
            QFrame:hover {
                background-color: rgba(220, 240, 255, 240);
                border: 1px solid rgba(100, 150, 255, 200);
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(8)
        
        # チェックボックス
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.item_info.get('checked', True))
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        self.checkbox.setFixedSize(20, 20)
        
        # アイコン
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        
        # ファイルの実際のアイコンを取得
        try:
            file_icon = icon_extractor.get_file_icon(self.item_info['path'], 24)
            if not file_icon.isNull():
                pixmap = file_icon.pixmap(24, 24)
                icon_label.setPixmap(pixmap)
            else:
                # フォールバック: デフォルトアイコン
                self._set_default_icon(icon_label)
        except Exception as e:
            print(f"アイコン設定エラー: {e}")
            self._set_default_icon(icon_label)
                
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # アイテム名
        name_label = QLabel(self.item_info['name'])
        name_label.setFont(QFont("Arial", 9))
        name_label.setStyleSheet("color: #333; font-weight: bold;")
        
        # パス（簡略表示）- 設定に基づいて表示/非表示
        self.path_label = None
        if self.should_show_file_path():
            path_text = self.item_info['path']
            if len(path_text) > 40:
                path_text = "..." + path_text[-37:]
            self.path_label = QLabel(path_text)
            self.path_label.setFont(QFont("Arial", 8))
            self.path_label.setStyleSheet("color: #666;")
        
        # 削除ボタンを廃止（右クリックメニューで削除に変更）
        
        # レイアウト構成
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)
        info_layout.addWidget(name_label)
        if self.path_label:
            info_layout.addWidget(self.path_label)
        
        layout.addWidget(self.checkbox)
        layout.addWidget(icon_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 右クリックメニューを有効にする
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def on_checkbox_changed(self, state):
        """チェックボックス状態変更時の処理"""
        self.item_info['checked'] = (state == Qt.CheckState.Checked.value)
        # 親リストウィンドウを取得してデータ保存を要求
        parent_list = self.parent()
        while parent_list and not isinstance(parent_list, ItemListWindow):
            parent_list = parent_list.parent()
        
        if parent_list and parent_list.group_icon:
            parent_list.group_icon.items_changed.emit()
            print(f"チェック状態変更: {self.item_info['name']} = {'ON' if self.item_info['checked'] else 'OFF'}")
        
    def should_show_file_path(self):
        """ファイルパスを表示するかどうかを判定"""
        if self.settings_manager:
            appearance_settings = self.settings_manager.get_appearance_settings()
            return appearance_settings.get('show_file_paths', True)
        return True  # デフォルトは表示
        
    def _set_default_icon(self, icon_label):
        """デフォルトアイコンを設定"""
        if self.item_info['type'] == 'folder':
            # フォルダアイコン
            icon_label.setStyleSheet("""
                QLabel {
                    background-color: #ffd700;
                    border-radius: 3px;
                    border: 1px solid #ccaa00;
                }
            """)
            icon_label.setText("📁")
        else:
            # ファイルアイコン
            if self.item_info['path'].lower().endswith('.exe'):
                icon_label.setStyleSheet("""
                    QLabel {
                        background-color: #ff6b6b;
                        border-radius: 3px;
                        border: 1px solid #cc5555;
                    }
                """)
                icon_label.setText("⚡")
            else:
                icon_label.setStyleSheet("""
                    QLabel {
                        background-color: #4ecdc4;
                        border-radius: 3px;
                        border: 1px solid #3ea39c;
                    }
                """)
                icon_label.setText("📄")
        
    def mousePressEvent(self, event):
        """マウスプレスイベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            # 右クリック時はリストが隠れないようにフラグを設定
            parent_list = self.parent()
            while parent_list and not isinstance(parent_list, ItemListWindow):
                parent_list = parent_list.parent()
            
            if parent_list:
                parent_list.dialog_showing = True
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """マウス移動イベント（ドラッグ処理）"""
        if (event.buttons() & Qt.MouseButton.LeftButton and 
            self.drag_start_position is not None):
            
            # ドラッグ距離をチェック
            distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
            if distance >= QApplication.startDragDistance():
                # Shiftキーが押されていない場合は並び替えドラッグ
                modifiers = QApplication.keyboardModifiers()
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    self.is_reorder_drag = False
                    # 通常のドラッグ操作を開始
                    self.start_drag()
                else:
                    self.is_reorder_drag = True
                    self.start_reorder_drag()
                
    def mouseReleaseEvent(self, event):
        """マウスリリースイベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drag_start_position is not None:
                # ドラッグ距離をチェック
                distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
                if distance < QApplication.startDragDistance():
                    # クリックとして処理（起動）
                    self.launch_requested.emit(self.item_info['path'])
                    
                self.drag_start_position = None
        super().mouseReleaseEvent(event)
        
    def start_drag(self):
        """ドラッグ操作を開始"""
        # ドラッグ開始時のマウス位置を保存
        current_pos = self.mapToGlobal(QPoint(0, 0))
        
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # カスタムデータのみを設定（ファイルURLは設定しない）
        # これにより標準のファイルコピー動作を防ぐ
        mime_data.setData("application/x-launcher-item", str(self.item_info['path']).encode('utf-8'))
        
        # プレーンテキストとしてもパスを設定（フォールバック用）
        mime_data.setText(self.item_info['path'])
        
        drag.setMimeData(mime_data)
        
        # ドラッグ時のカーソルを設定
        self.set_drag_cursors(drag)
        
        # マウス位置追跡タイマーを開始
        self.start_mouse_tracking()
        
        # ドラッグ実行（複数のアクションを許可して禁止マークを防ぐ）
        drop_action = drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
        
        # マウス位置追跡を停止
        self.stop_mouse_tracking()
        
        # ドラッグ終了後の処理
        self.handle_drag_finished(drop_action)
        
    def start_reorder_drag(self):
        """並び替えドラッグ操作を開始"""
        # 親ウィンドウに並び替えドラッグ開始を通知
        parent_list = self.parent()
        while parent_list and not isinstance(parent_list, ItemListWindow):
            parent_list = parent_list.parent()
        
        if parent_list:
            parent_list.reorder_drag_active = True
            
        # ドラッグ中フラグを設定
        self.is_being_dragged = True
        
        # ドラッグ中の視覚的フィードバック
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 150);
                border: 2px solid rgba(255, 153, 0, 255);
                border-radius: 5px;
                margin: 1px;
            }
        """)
            
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 並び替え用のカスタムデータを設定
        mime_data.setData("application/x-launcher-reorder", str(id(self)).encode('utf-8'))
        
        drag.setMimeData(mime_data)
        
        # ドラッグ実行
        drop_action = drag.exec(Qt.DropAction.MoveAction)
        
        # ドラッグ終了後にフラグを解除
        self.is_being_dragged = False
        
        # スタイルをリセット
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 240);
                border: 1px solid rgba(200, 200, 200, 150);
                border-radius: 5px;
                margin: 1px;
            }
            QFrame:hover {
                background-color: rgba(220, 240, 255, 240);
                border: 1px solid rgba(100, 150, 255, 200);
            }
        """)
        
        if parent_list:
            parent_list.reorder_drag_active = False
            
    def start_mouse_tracking(self):
        """マウス位置追跡を開始"""
        self.mouse_tracking_timer = QTimer()
        self.mouse_tracking_timer.timeout.connect(self.track_mouse_position)
        self.mouse_tracking_timer.start(50)  # 50msごとに位置を追跡
        
    def stop_mouse_tracking(self):
        """マウス位置追跡を停止"""
        if hasattr(self, 'mouse_tracking_timer'):
            self.mouse_tracking_timer.stop()
            self.mouse_tracking_timer.deleteLater()
            
    def track_mouse_position(self):
        """現在のマウス位置を追跡"""
        try:
            # Windowsシステムからマウス位置を取得
            import win32gui
            self.drop_position = win32gui.GetCursorPos()
        except Exception as e:
            print(f"マウス位置追跡エラー: {e}")
            
    def set_drag_cursors(self, drag):
        """ドラッグ時のカーソルを設定"""
        try:
            # カスタムドラッグアイコンを作成
            drag_pixmap = self.create_drag_pixmap()
            drag.setPixmap(drag_pixmap)
            
            # 移動用カーソルを設定（すべてのアクションに対して同じカーソルを設定）
            move_cursor_pixmap = self.create_move_cursor_pixmap()
            drag.setDragCursor(move_cursor_pixmap, Qt.DropAction.CopyAction)
            drag.setDragCursor(move_cursor_pixmap, Qt.DropAction.MoveAction)
            drag.setDragCursor(move_cursor_pixmap, Qt.DropAction.LinkAction)
            drag.setDragCursor(move_cursor_pixmap, Qt.DropAction.IgnoreAction)
            
            # デフォルトカーソルも同じものに設定
            drag.setDragCursor(move_cursor_pixmap, Qt.DropAction.ActionMask)
            
            print("ドラッグカーソル設定完了")
            
        except Exception as e:
            print(f"ドラッグカーソル設定エラー: {e}")
            
    def create_drag_pixmap(self):
        """ドラッグ用のピクスマップを作成"""
        try:
            # アイテムのアイコンをベースにドラッグ画像を作成
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 背景の半透明の丸
            painter.setBrush(QColor(100, 150, 255, 150))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(8, 8, 48, 48)
            
            # アイコンの文字（フォルダまたはファイル）
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 20, QFont.Weight.Bold))
            
            if self.item_info['type'] == 'folder':
                icon_text = "📁"
            else:
                icon_text = "📄"
                
            painter.drawText(16, 40, icon_text)
            painter.end()
            
            return pixmap
            
        except Exception as e:
            print(f"ドラッグピクスマップ作成エラー: {e}")
            # フォールバック
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(100, 150, 255, 200))
            return pixmap
            
    def create_move_cursor_pixmap(self):
        """移動用カーソルのピクスマップを作成"""
        try:
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 白い背景円（見やすくするため）
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawEllipse(2, 2, 28, 28)
            
            # 移動アイコン（十字矢印）
            painter.setPen(QPen(QColor(50, 150, 50), 3))  # 緑色で太い線
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            # 十字の線（中心から）
            painter.drawLine(16, 6, 16, 26)   # 縦線
            painter.drawLine(6, 16, 26, 16)   # 横線
            
            # 矢印の先端（より明確に）
            painter.setPen(QPen(QColor(50, 150, 50), 2))
            painter.drawLine(16, 6, 13, 9)    # 上矢印左
            painter.drawLine(16, 6, 19, 9)    # 上矢印右
            painter.drawLine(16, 26, 13, 23)  # 下矢印左
            painter.drawLine(16, 26, 19, 23)  # 下矢印右
            painter.drawLine(6, 16, 9, 13)    # 左矢印上
            painter.drawLine(6, 16, 9, 19)    # 左矢印下  
            painter.drawLine(26, 16, 23, 13)  # 右矢印上
            painter.drawLine(26, 16, 23, 19)  # 右矢印下
            
            painter.end()
            
            return pixmap
            
        except Exception as e:
            print(f"移動カーソル作成エラー: {e}")
            # フォールバック：透明なピクスマップ
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.transparent)
            return pixmap
            
    def handle_drag_finished(self, drop_action):
        """ドラッグ終了後の処理"""
        try:
            print(f"ドラッグ終了: アクション={drop_action}")
            
            # 並び替えドラッグでない場合のみ処理
            if not self.is_reorder_drag:
                # 外部ドロップかどうかを確認するために少し待機
                QTimer.singleShot(200, self.check_and_create_shortcut)
                    
        except Exception as e:
            print(f"ドラッグ終了処理エラー: {e}")
            
    def check_and_create_shortcut(self):
        """ショートカット作成の最終確認"""
        try:
            # 親リストウィンドウを取得
            parent_list = self.parent()
            while parent_list and not isinstance(parent_list, ItemListWindow):
                parent_list = parent_list.parent()
                
            if not parent_list:
                return
                
            # アイテムがまだリストに存在するかチェック
            item_still_exists = False
            if parent_list.group_icon:
                for item in parent_list.group_icon.items:
                    if item['path'] == self.item_info['path']:
                        item_still_exists = True
                        break
                        
            # アイテムがリストから削除されていない（つまり外部ドロップ）場合のみ処理
            if item_still_exists:
                # 他のリストにアイテムが移動されたかチェック
                moved_to_other_list = self.check_if_moved_to_other_list()
                
                if not moved_to_other_list:
                    # 真の外部ドロップと判断してショートカットを作成
                    desktop_path = self.get_desktop_path()
                    if desktop_path:
                        shortcut_created = self.create_shortcut_at_position(
                            self.item_info['path'], 
                            self.item_info['name'], 
                            desktop_path,
                            self.drop_position
                        )
                        
                        if shortcut_created:
                            # リストからアイテムを直接削除（確認ダイアログなし）
                            self.remove_item_directly(self.item_info['path'])
                            print(f"ショートカット作成完了、リストから削除: {self.item_info['name']}")
                        else:
                            print(f"ショートカット作成失敗: {self.item_info['name']}")
                else:
                    print(f"他のリストに移動されたため、ショートカット作成をスキップ: {self.item_info['name']}")
            else:
                print(f"アイテムが既に削除されているため、処理をスキップ: {self.item_info['name']}")
                            
        except Exception as e:
            print(f"ショートカット作成確認エラー: {e}")
            
    def check_if_moved_to_other_list(self):
        """アイテムが他のリストに移動されたかチェック"""
        try:
            # QApplicationインスタンスから全てのグループアイコンを取得
            app = QApplication.instance()
            if hasattr(app, 'group_icons'):
                current_parent = self.parent()
                while current_parent and not isinstance(current_parent, ItemListWindow):
                    current_parent = current_parent.parent()
                    
                for group_icon in app.group_icons:
                    # 現在の親リスト以外をチェック
                    if current_parent and group_icon != current_parent.group_icon:
                        for item in group_icon.items:
                            if item['path'] == self.item_info['path']:
                                return True
            return False
        except Exception as e:
            print(f"他リスト移動チェックエラー: {e}")
            return False
            
    def get_desktop_path(self):
        """デスクトップのパスを取得"""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                desktop_path = winreg.QueryValueEx(key, "Desktop")[0]
                return desktop_path
        except Exception as e:
            print(f"デスクトップパス取得エラー: {e}")
            # フォールバック
            return os.path.join(os.path.expanduser("~"), "Desktop")
            
    def create_shortcut_at_position(self, target_path, shortcut_name, desktop_path, position):
        """指定位置にショートカットを作成"""
        try:
            # ショートカットファイル名を作成
            shortcut_path = os.path.join(desktop_path, f"{shortcut_name}.lnk")
            
            # 既に同名のショートカットがある場合は番号を付ける
            counter = 1
            original_shortcut_path = shortcut_path
            while os.path.exists(shortcut_path):
                name_without_ext = os.path.splitext(shortcut_name)[0]
                shortcut_path = os.path.join(desktop_path, f"{name_without_ext} ({counter}).lnk")
                counter += 1
                
            # Windows COMオブジェクトを使ってショートカットを作成
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target_path
            
            # フォルダの場合は作業ディレクトリを設定
            if os.path.isdir(target_path):
                shortcut.WorkingDirectory = target_path
            else:
                # ファイルの場合は親ディレクトリを作業ディレクトリに
                shortcut.WorkingDirectory = os.path.dirname(target_path)
                
            shortcut.save()
            
            # ショートカット作成後、指定位置に配置
            if position:
                self.position_desktop_icon(shortcut_path, position)
            
            print(f"ショートカット作成成功: {shortcut_path} at {position}")
            return True
            
        except Exception as e:
            print(f"ショートカット作成エラー: {e}")
            return False
            
    def position_desktop_icon(self, shortcut_path, position):
        """デスクトップアイコンを指定位置に配置"""
        try:
            if not position:
                return
                
            print(f"ショートカット位置設定: {os.path.basename(shortcut_path)} at {position}")
            
            # Windowsの制約により、プログラム的にデスクトップアイコンの
            # 正確な位置を設定するのは非常に困難です。
            # 現在はドロップ位置の情報を取得し、ログに記録しています。
            
            # 将来的な実装案:
            # 1. デスクトップのグリッド位置を計算
            # 2. 最も近いグリッド位置にアイコンを配置
            # 3. レジストリまたはINIファイルを使用して位置情報を保存
            
            # 現在は通常の場所（デスクトップ）にショートカットが作成されます
            
        except Exception as e:
            print(f"デスクトップアイコン配置エラー: {e}")
            
    def create_shortcut_on_desktop(self, target_path, shortcut_name, desktop_path):
        """デスクトップにショートカットを作成（後方互換性のため）"""
        return self.create_shortcut_at_position(target_path, shortcut_name, desktop_path, None)
        
    def remove_item_directly(self, item_path):
        """確認ダイアログなしでリストからアイテムを直接削除"""
        try:
            # 親リストウィンドウを取得
            parent_list = self.parent()
            while parent_list and not isinstance(parent_list, ItemListWindow):
                parent_list = parent_list.parent()
                
            if parent_list and parent_list.group_icon:
                # グループアイコンからアイテムを削除
                parent_list.group_icon.remove_item(item_path)
                # リストを更新
                parent_list.refresh_items()
                print(f"アイテムを直接削除: {os.path.basename(item_path)}")
            else:
                print(f"親リストが見つからないため削除失敗: {item_path}")
                
        except Exception as e:
            print(f"直接削除エラー: {e}")
        
    def show_context_menu(self, position):
        """右クリックコンテキストメニューを表示"""
        # メニュー表示中はリストを隠さないようにフラグを設定
        parent_list = self.parent()
        while parent_list and not isinstance(parent_list, ItemListWindow):
            parent_list = parent_list.parent()
        
        if parent_list:
            parent_list.dialog_showing = True
        
        menu = QMenu()
        menu.setParent(None)  # 独立したメニュー
        
        # メニューのスタイルを調整
        menu.setStyleSheet("""
            QMenu {
                font-size: 12px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 16px;
                min-width: 100px;
            }
            QMenu::item:selected {
                background-color: #4a90e2;
                color: white;
            }
        """)
        
        # 削除アクション
        delete_action = QAction("削除", menu)
        delete_action.triggered.connect(lambda: self.remove_requested.emit(self.item_info['path']))
        menu.addAction(delete_action)
        
        # アイテム情報表示アクション
        info_action = QAction("プロパティ", menu)
        info_action.triggered.connect(self.show_item_info)
        menu.addAction(info_action)
        
        # メニューを表示
        global_pos = self.mapToGlobal(position)
        action = menu.exec(global_pos)
        
        # メニュー終了後にフラグを解除（選択・キャンセル問わず）
        if parent_list:
            parent_list.dialog_showing = False
        
    def show_item_info(self):
        """アイテム情報を表示"""
        from PyQt6.QtWidgets import QMessageBox
        info_text = f"""
アイテム名: {self.item_info['name']}
パス: {self.item_info['path']}
タイプ: {self.item_info['type']}
        """
        QMessageBox.information(self, "アイテム情報", info_text.strip())


class ItemListWindow(QWidget):
    """アイテムリストウィンドウ"""
    
    def __init__(self, group_icon, settings_manager=None):
        super().__init__()
        self.group_icon = group_icon
        self.settings_manager = settings_manager
        self.mouse_entered = False
        self.mouse_left_after_enter = False
        self.is_pinned = False  # 固定表示モード
        self.dialog_showing = False  # ダイアログ表示中フラグ
        self.reorder_drag_active = False  # 並び替えドラッグ中フラグ
        self.drag_preview_index = -1  # ドラッグプレビュー位置
        self.animation_group = None  # アニメーショングループ
        self.animating_widgets = []  # アニメーション中のウィジェット
        self.original_positions = {}  # 元の位置を保存
        
        # ウィンドウドラッグ用
        self.window_drag_start_position = None
        self.is_window_dragging = False
        
        # 遅延非表示用タイマー
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.delayed_hide)
        
        self.setup_ui()
        self.setup_window()
        self.setup_drag_drop()
        
        # グループアイコンの変更を監視
        self.group_icon.items_changed.connect(self.refresh_items)
        
    def setup_window(self):
        """ウィンドウ設定"""
        # 基本フラグ
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        
        # 最前面表示設定をアイコン設定に合わせる
        if self.settings_manager:
            appearance_settings = self.settings_manager.get_appearance_settings()
            always_on_top = appearance_settings.get('always_on_top', True)
            if always_on_top:
                flags |= Qt.WindowType.WindowStaysOnTopHint
                
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # フォーカスを失ったら自動的に隠す
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        
    def setup_drag_drop(self):
        """ドラッグ&ドロップ設定"""
        self.setAcceptDrops(True)
        
    def calculate_max_height(self):
        """画面高さに基づいて最大高さを計算"""
        try:
            # 利用可能な画面サイズを取得
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            screen_height = screen_geometry.height()
            
            # 画面高さの90%を最大高さとする（タスクバーやウィンドウフレーム分を考慮）
            max_height = int(screen_height * 0.9)
            
            # 最低でも600pxは確保
            max_height = max(max_height, 600)
            
            print(f"画面高さ: {screen_height}px, 計算された最大高さ: {max_height}px")
            return max_height
            
        except Exception as e:
            print(f"最大高さ計算エラー: {e}")
            return 600  # エラー時はデフォルト値
        
    def setup_ui(self):
        """UI設定"""
        # 初期サイズを設定（後で動的に調整される）
        self.setFixedWidth(300)  # 幅は固定
        self.min_height = 120    # 最小高さ（ヘッダー + 余白）
        self.max_height = self.calculate_max_height()  # 最大高さ（画面高さに基づく）
        self.item_height = 42    # アイテム1個あたりの高さ（アイテム高さ40px + 余白2px）
        
        # メインレイアウト - 左マージンをさらに削減
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 8, 8, 8)  # 左マージンを0pxに、他も少し削減
        main_layout.setSpacing(3)
        
        # ヘッダー
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(100, 150, 255, 220);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 100);
            }
        """)
        self.header_frame.setFixedHeight(40)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(6, 5, 8, 5)  # 左マージンを削減
        
        # タイトル（ダブルクリック可能）
        self.title_label = QLabel(f"📁 {str(self.group_icon.name)}")
        self.title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_label.mouseDoubleClickEvent = self.toggle_pin_mode
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        self.header_frame.setLayout(header_layout)
        
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: rgba(255, 255, 255, 200);
                border-radius: 8px;
                border: 1px solid rgba(200, 200, 200, 150);
                margin-left: 0px;
            }
            QScrollBar:vertical {
                background-color: rgba(200, 200, 200, 100);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(100, 150, 255, 150);
                border-radius: 6px;
                min-height: 20px;
            }
        """)
        
        # アイテムコンテナ - マージンをさらに削減
        self.items_widget = QWidget()
        self.items_layout = QVBoxLayout()
        self.items_layout.setContentsMargins(2, 3, 3, 3)  # 左マージンを大幅削減
        self.items_layout.setSpacing(1)
        self.items_layout.addStretch()
        self.items_widget.setLayout(self.items_layout)
        
        scroll_area.setWidget(self.items_widget)
        
        # レイアウト構成
        main_layout.addWidget(self.header_frame)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        
        # ウィンドウ全体のスタイル調整 - 左端の視覚的境界を最小化
        self.setStyleSheet("""
            QWidget {
                margin-left: 0px;
                padding-left: 0px;
            }
        """)
        
        # 初期アイテム表示
        self.refresh_items()
        self.update_title_display()
        
        # 初期サイズを調整
        self.adjust_window_height()
        
        # ヘッダーフレームにドラッグ機能を追加
        self.setup_header_drag()
        
    def setup_header_drag(self):
        """ヘッダードラッグ機能を設定"""
        # ヘッダーフレームにマウスイベントフィルターを設定
        self.header_frame.mousePressEvent = self.header_mouse_press_event
        self.header_frame.mouseMoveEvent = self.header_mouse_move_event
        self.header_frame.mouseReleaseEvent = self.header_mouse_release_event
        
        # 右クリックメニューを設定
        self.header_frame.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.header_frame.customContextMenuRequested.connect(self.show_header_context_menu)
        
        # ドラッグ可能であることを示すカーソルを設定
        self.header_frame.setCursor(Qt.CursorShape.SizeAllCursor)
        
    def header_mouse_press_event(self, event):
        """ヘッダーマウスプレスイベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.window_drag_start_position = event.globalPosition().toPoint()
            self.is_window_dragging = False
            
    def header_mouse_move_event(self, event):
        """ヘッダーマウス移動イベント（ウィンドウドラッグ）"""
        if (event.buttons() & Qt.MouseButton.LeftButton and 
            self.window_drag_start_position is not None):
            
            # ドラッグ距離をチェック
            distance = (event.globalPosition().toPoint() - self.window_drag_start_position).manhattanLength()
            if distance >= QApplication.startDragDistance():
                self.is_window_dragging = True
                # ウィンドウを移動
                global_pos = event.globalPosition().toPoint()
                new_position = self.pos() + (global_pos - self.window_drag_start_position)
                self.move(new_position)
                self.window_drag_start_position = global_pos
                
    def header_mouse_release_event(self, event):
        """ヘッダーマウスリリースイベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.window_drag_start_position is not None:
                if not self.is_window_dragging:
                    # ドラッグしていない場合（クリック）- 何もしない（既存のダブルクリック機能は残す）
                    pass
                    
                # フラグをリセット
                self.window_drag_start_position = None
                self.is_window_dragging = False
                
    def show_header_context_menu(self, position):
        """ヘッダー右クリックコンテキストメニューを表示"""
        # メニュー表示中は自動非表示を無効化
        self.dialog_showing = True
        self.hide_timer.stop()  # 実行中のタイマーを停止
        
        menu = QMenu()
        menu.setParent(None)  # 独立したメニュー
        
        # メニューのスタイルを調整
        menu.setStyleSheet("""
            QMenu {
                font-size: 12px;
                padding: 5px;
                background-color: white;
                border: 1px solid #ccc;
            }
            QMenu::item {
                padding: 8px 16px;
                min-width: 120px;
            }
            QMenu::item:selected {
                background-color: #4a90e2;
                color: white;
            }
        """)
        
        # 全て起動アクション
        launch_all_action = QAction("全て起動", menu)
        launch_all_action.triggered.connect(self.on_launch_all_triggered)
        menu.addAction(launch_all_action)
        
        # チェックされたアイテムがない場合は無効化
        checked_items = [item for item in self.group_icon.items if item.get('checked', True)]
        if not checked_items:
            launch_all_action.setEnabled(False)
        
        # メニューを表示
        global_pos = self.header_frame.mapToGlobal(position)
        menu.exec(global_pos)
        
        # メニュー終了後の処理
        self.on_menu_closed()
        
    def on_launch_all_triggered(self):
        """全て起動メニューがトリガーされた時の処理"""
        # メニューが確実に閉じられるようにタイマーで少し遅延
        QTimer.singleShot(100, self.launch_all_items)
        
    def on_menu_closed(self):
        """メニューが閉じられた時の処理"""
        # メニュー終了後、自動非表示を再開
        self.dialog_showing = False
        print("メニュー終了: 自動非表示機能を復活")
        
    def launch_all_items(self):
        """チェックされたアイテムを上から順番に起動"""
        try:
            if not self.group_icon.items:
                print("起動するアイテムがありません")
                return
                
            # チェックされたアイテムのみをフィルタリング
            checked_items = [item for item in self.group_icon.items if item.get('checked', True)]
            
            if not checked_items:
                print("チェックされたアイテムがありません")
                return
                
            print(f"チェックされたアイテム起動開始: {len(checked_items)}個のアイテム")
            
            # チェックされたアイテムリストをコピーして起動処理を開始
            self.launch_queue = list(checked_items)
            self.launch_index = 0
            
            # 最初のアイテム起動
            self.launch_next_item()
            
        except Exception as e:
            print(f"全て起動処理エラー: {e}")
            QMessageBox.critical(
                self, "エラー", 
                f"一括起動中にエラーが発生しました:\n{str(e)}"
            )
            
    def launch_next_item(self):
        """次のアイテムを起動（タイマー制御）"""
        try:
            if self.launch_index >= len(self.launch_queue):
                # 全て起動完了
                print("全て起動完了")
                self.hide()
                return
                
            item_info = self.launch_queue[self.launch_index]
            item_path = item_info['path']
            item_name = item_info['name']
            
            try:
                if os.path.exists(item_path):
                    if os.path.isdir(item_path):
                        # フォルダを開く
                        os.startfile(item_path)
                        print(f"フォルダ起動: {item_name}")
                    else:
                        # ファイルを実行
                        os.startfile(item_path)
                        print(f"ファイル起動: {item_name}")
                else:
                    print(f"ファイルが見つかりません: {item_path}")
                    
            except Exception as e:
                print(f"起動エラー - {item_name}: {e}")
                
            # 次のアイテムを起動（3秒後）
            self.launch_index += 1
            if self.launch_index < len(self.launch_queue):
                QTimer.singleShot(3000, self.launch_next_item)
            else:
                # 最後のアイテムの場合は完了処理
                QTimer.singleShot(1000, lambda: (print("チェックされたアイテムの起動完了"), self.hide()))
                
        except Exception as e:
            print(f"アイテム起動エラー: {e}")
        
    def refresh_items(self):
        """アイテムリストを更新"""
        # 既存のアイテムウィジェットを削除
        for i in reversed(range(self.items_layout.count() - 1)):  # ストレッチを除く
            child = self.items_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
                
        # 新しいアイテムウィジェットを追加
        for item_info in self.group_icon.items:
            item_widget = ItemWidget(item_info, self.settings_manager)
            item_widget.launch_requested.connect(self.launch_item)
            item_widget.remove_requested.connect(self.remove_item)
            item_widget.reorder_requested.connect(self.reorder_item)
            self.items_layout.insertWidget(self.items_layout.count() - 1, item_widget)
            
        # アイテムがない場合のメッセージ
        if not self.group_icon.items:
            empty_label = QLabel("アイテムがありません\nファイルやフォルダをドラッグ&ドロップしてください")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    color: #999;
                    font-style: italic;
                    padding: 20px;
                }
            """)
            self.items_layout.insertWidget(0, empty_label)
            
        # ウィンドウサイズを調整
        self.adjust_window_height()
        
    def apply_appearance_settings(self):
        """外観設定を適用してUIを更新"""
        # 最前面表示設定を更新
        if self.settings_manager:
            appearance_settings = self.settings_manager.get_appearance_settings()
            always_on_top = appearance_settings.get('always_on_top', True)
            
            # 現在のフラグを取得
            flags = self.windowFlags()
            
            # 最前面表示フラグを更新
            if always_on_top:
                flags |= Qt.WindowType.WindowStaysOnTopHint
            else:
                flags &= ~Qt.WindowType.WindowStaysOnTopHint
                
            # フラグを適用（表示状態を維持）
            was_visible = self.isVisible()
            self.setWindowFlags(flags)
            if was_visible:
                self.show()
                
            print(f"リストウィンドウ最前面表示: {'ON' if always_on_top else 'OFF'}")
        
        self.refresh_items()
        
    def reorder_item(self, item_widget, new_index):
        """アイテムの並び順を変更"""
        try:
            # 現在のアイテムのインデックスを取得
            current_index = -1
            for i, item_info in enumerate(self.group_icon.items):
                if item_info['path'] == item_widget.item_info['path']:
                    current_index = i
                    break
                    
            if current_index == -1:
                return  # アイテムが見つからない
                
            # アイテムを移動
            item_info = self.group_icon.items.pop(current_index)
            self.group_icon.items.insert(new_index, item_info)
            
            # UIを更新
            self.refresh_items()
            
            # データを保存
            self.group_icon.items_changed.emit()
            
            print(f"アイテム並び替え: {current_index} -> {new_index}")
            
        except Exception as e:
            print(f"並び替えエラー: {e}")
            
    def launch_item(self, item_path):
        """アイテムを起動"""
        try:
            if os.path.exists(item_path):
                if os.path.isdir(item_path):
                    # フォルダを開く
                    os.startfile(item_path)
                else:
                    # ファイルを実行
                    os.startfile(item_path)
                    
                # 起動後にウィンドウを隠す
                self.hide()
            else:
                QMessageBox.warning(
                    self, "エラー", 
                    f"ファイルまたはフォルダが見つかりません:\n{item_path}"
                )
        except Exception as e:
            QMessageBox.critical(
                self, "エラー", 
                f"起動に失敗しました:\n{str(e)}"
            )
            
    def remove_item(self, item_path):
        """アイテムを削除"""
        # ダイアログ表示フラグを設定（全ての自動非表示を無効化）
        self.dialog_showing = True
        
        # カスタム確認ダイアログを作成（ボタンを大きくするため）
        msg_box = QMessageBox()
        msg_box.setParent(None)  # 親を指定しない（独立したダイアログ）
        msg_box.setWindowTitle("確認")
        msg_box.setText(f"このアイテムをリストから削除しますか?\n{os.path.basename(item_path)}")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # ダイアログの最前面表示設定をアイコン設定に合わせる
        dialog_flags = Qt.WindowType.Dialog
        if self.settings_manager:
            appearance_settings = self.settings_manager.get_appearance_settings()
            always_on_top = appearance_settings.get('always_on_top', True)
            if always_on_top:
                dialog_flags |= Qt.WindowType.WindowStaysOnTopHint
        msg_box.setWindowFlags(dialog_flags)
        
        # ボタンを大きくするためのスタイルシート
        msg_box.setStyleSheet("""
            QMessageBox {
                font-size: 12px;
                min-width: 300px;
            }
            QMessageBox QPushButton {
                font-size: 14px;
                padding: 8px 16px;
                min-width: 80px;
                min-height: 30px;
            }
        """)
        
        yes_button = msg_box.addButton("はい", QMessageBox.ButtonRole.YesRole)
        no_button = msg_box.addButton("いいえ", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(no_button)
        
        # ダイアログを表示
        result = msg_box.exec()
        
        # ダイアログ表示フラグを解除
        self.dialog_showing = False
        
        # 結果をチェック
        if msg_box.clickedButton() == yes_button:
            self.group_icon.remove_item(item_path)
            # 削除後にリストを再表示・更新
            self.refresh_items()
            
    def show(self):
        """ウィンドウを表示"""
        # 表示時に状態をリセット
        self.mouse_entered = False
        self.mouse_left_after_enter = False
        self.hide_timer.stop()
        super().show()
        
    def enterEvent(self, event):
        """マウスがウィンドウに入った"""
        self.mouse_entered = True
        self.hide_timer.stop()  # タイマーを停止
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """マウスがウィンドウから出た"""
        if (self.mouse_entered and not self.is_pinned and 
            not self.dialog_showing and not self.reorder_drag_active):  # メニュー表示中でない場合のみ
            self.mouse_left_after_enter = True
            # 少し遅延してから隠す（誤操作防止）
            self.hide_timer.start(300)  # 300ms後に隠す
        super().leaveEvent(event)
        
    def delayed_hide(self):
        """遅延非表示処理"""
        # 固定モード、メニュー表示中、または並び替えドラッグ中の場合は隠さない
        if self.is_pinned or self.dialog_showing or self.reorder_drag_active:
            return
        # マウスがウィンドウ内に戻ってきていないかチェック
        if not self.underMouse() and self.mouse_left_after_enter:
            self.hide()
            
    def focusOutEvent(self, event):
        """フォーカスを失ったら隠す"""
        # 固定モード、マウスがウィンドウ内、メニュー表示中、または並び替えドラッグ中は隠さない
        if (not self.is_pinned and not self.underMouse() and 
            not self.dialog_showing and not self.reorder_drag_active):
            self.hide()
        super().focusOutEvent(event)
        
    def mousePressEvent(self, event):
        """マウスクリック時（ウィンドウ内の空白部分をクリック）"""
        # ウィンドウ内の空白部分をクリックした場合は隠さない
        # アイテムのクリックは各ItemWidgetで処理される
        super().mousePressEvent(event)
        
    def toggle_pin_mode(self, event):
        """固定表示モードを切り替え"""
        self.is_pinned = not self.is_pinned
        self.update_title_display()
        
        if self.is_pinned:
            # 固定モード：タイマーを停止
            self.hide_timer.stop()
        else:
            # 通常モード：マウスがウィンドウ外にある場合は隠す
            if not self.underMouse():
                self.hide_timer.start(300)
                
    def update_title_display(self):
        """タイトル表示を更新"""
        pin_icon = "📌" if self.is_pinned else "📁"
        self.title_label.setText(f"{pin_icon} {str(self.group_icon.name)}")
        
        # 固定モード時は背景色を少し変更
        if self.is_pinned:
            self.title_label.setStyleSheet("color: white; background-color: rgba(255, 200, 100, 50); border-radius: 3px; padding: 2px;")
        else:
            self.title_label.setStyleSheet("color: white;")
            
    def dragEnterEvent(self, event):
        """ドラッグエンターイベント"""
        if (event.mimeData().hasFormat("application/x-launcher-item") or 
            event.mimeData().hasFormat("application/x-launcher-reorder") or 
            event.mimeData().hasUrls()):
            
            # 並び替えドラッグの場合、ドラッグ元が自分のリストかチェック
            if event.mimeData().hasFormat("application/x-launcher-reorder"):
                widget_id = event.mimeData().data("application/x-launcher-reorder").data().decode('utf-8')
                is_from_this_list = False
                
                # 自分のリスト内のウィジェットかチェック
                for i in range(self.items_layout.count() - 1):  # ストレッチを除く
                    widget = self.items_layout.itemAt(i).widget()
                    if widget and str(id(widget)) == widget_id:
                        is_from_this_list = True
                        break
                
                # 自分のリストからのドラッグの場合のみ受け入れ
                if is_from_this_list:
                    event.acceptProposedAction()
                    self.setStyleSheet("QWidget { border: 2px dashed #ff9900; }")  # 並び替えは橙色
                    self.reorder_drag_active = True
                    # 並び替えドラッグ開始時に元の位置を保存
                    self.save_original_positions()
                else:
                    # 他のリストからの並び替えドラッグは受け入れない
                    event.ignore()
            else:
                # 通常のドラッグ（リスト間移動やファイルドロップ）
                event.acceptProposedAction()
                self.setStyleSheet("QWidget { border: 2px dashed #00ff00; }")  # 通常は緑色
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        """ドラッグリーブイベント"""
        self.setStyleSheet("")
        self.drag_preview_index = -1
        self.clear_drag_preview()
        
    def dragMoveEvent(self, event):
        """ドラッグ移動イベント"""
        if event.mimeData().hasFormat("application/x-launcher-reorder"):
            # ドロップ位置からインデックスを計算
            drop_y = event.position().y()
            target_index = self.calculate_drop_index(drop_y)
            
            # プレビュー位置が変わった場合のみ更新
            if target_index != self.drag_preview_index:
                self.drag_preview_index = target_index
                self.show_drag_preview(target_index)
                
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
        
    def dropEvent(self, event):
        """ドロップイベント"""
        self.setStyleSheet("")
        self.clear_drag_preview()
        self.drag_preview_index = -1
        self.reorder_drag_active = False
        
        # 並び替えドロップの場合
        if event.mimeData().hasFormat("application/x-launcher-reorder"):
            widget_id = event.mimeData().data("application/x-launcher-reorder").data().decode('utf-8')
            
            # ドロップ位置からインデックスを計算
            drop_y = event.position().y()
            target_index = self.calculate_drop_index(drop_y)
            
            # ドラッグされたウィジェットを見つける
            dragged_widget = None
            dragged_item_path = None
            for i in range(self.items_layout.count() - 1):  # ストレッチを除く
                widget = self.items_layout.itemAt(i).widget()
                if widget and str(id(widget)) == widget_id:
                    dragged_widget = widget
                    dragged_item_path = widget.item_info['path']
                    break
                    
            # パスで並び替えを実行（より確実）
            if dragged_item_path:
                self.reorder_item_by_path(dragged_item_path, target_index)
                
            event.acceptProposedAction()
            
        # リスト間移動の場合
        elif event.mimeData().hasFormat("application/x-launcher-item"):
            item_path = event.mimeData().data("application/x-launcher-item").data().decode('utf-8')
            
            # 既に存在するかチェック
            for item in self.group_icon.items:
                if item['path'] == item_path:
                    return  # 重複なので追加しない
                    
            # 他のグループから削除（常に実行 - アクションに関係なく移動として処理）
            self.remove_item_from_other_groups(item_path)
            
            # このグループに追加
            self.group_icon.add_item(item_path)
            # UI更新を強制的に実行
            self.refresh_items()
            event.acceptProposedAction()
            
        # 通常のファイル/フォルダドロップの場合
        elif event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path:
                    self.group_icon.add_item(file_path)
            # ドロップ後にリストを更新（サイズ調整を含む）
            self.refresh_items()
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def remove_item_from_other_groups(self, item_path):
        """他のグループから指定されたアイテムを削除"""
        # QApplicationインスタンスから全てのグループアイコンを取得
        app = QApplication.instance()
        if hasattr(app, 'group_icons'):
            for group_icon in app.group_icons:
                if group_icon != self.group_icon:
                    group_icon.remove_item(item_path)
                    
    def adjust_window_height(self):
        """アイテム数に応じてウィンドウの高さを調整"""
        try:
            # アイテム数を取得
            item_count = len(self.group_icon.items)
            
            # アイテムがない場合は最小サイズ
            if item_count == 0:
                target_height = self.min_height
            else:
                # ヘッダー高さ（40px） + マージン（16px） + アイテム高さ × アイテム数 + 余白（20px）
                target_height = 40 + 16 + (self.item_height * item_count) + 20
                
            # 最小・最大高さでクランプ
            target_height = max(self.min_height, min(target_height, self.max_height))
            
            # ウィンドウサイズを設定
            self.setFixedHeight(target_height)
            
            # ウィンドウが画面下部を超えないよう位置を調整
            self.adjust_window_position()
            
            print(f"ウィンドウ高さ調整: アイテム数={item_count}, 高さ={target_height}px")
            
        except Exception as e:
            print(f"ウィンドウ高さ調整エラー: {e}")
            
    def adjust_window_position(self):
        """ウィンドウが画面外に出ないよう位置を調整"""
        try:
            # 画面の利用可能領域を取得
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            
            # 現在のウィンドウ位置とサイズ
            current_pos = self.pos()
            window_height = self.height()
            
            # ウィンドウ下端が画面下部を超える場合
            if current_pos.y() + window_height > screen_geometry.bottom():
                # ウィンドウを画面内に収まるよう上に移動
                new_y = screen_geometry.bottom() - window_height
                # ただし画面上端より上には行かないよう制限
                new_y = max(new_y, screen_geometry.top())
                
                self.move(current_pos.x(), new_y)
                print(f"ウィンドウ位置調整: Y座標 {current_pos.y()} → {new_y}")
                
        except Exception as e:
            print(f"ウィンドウ位置調整エラー: {e}")
            
    def calculate_drop_index(self, drop_y):
        """ドロップ位置からアイテムのインデックスを計算"""
        try:
            # ヘッダーの高さを考慮
            header_height = 48  # ヘッダー高さ + マージン
            
            # スクロールエリア内でのY位置を計算
            if drop_y < header_height:
                return 0
                
            relative_y = drop_y - header_height
            
            # アイテムの高さで割って位置を計算
            index = int(relative_y / self.item_height)
            
            # アイテム数でクランプ
            max_index = len(self.group_icon.items)
            index = max(0, min(index, max_index))
            
            print(f"ドロップ位置計算: Y={drop_y}, 相対Y={relative_y}, インデックス={index}")
            return index
            
        except Exception as e:
            print(f"ドロップ位置計算エラー: {e}")
            return 0
            
    def save_original_positions(self):
        """全ウィジェットの元の位置を保存"""
        try:
            self.original_positions.clear()
            for i in range(self.items_layout.count() - 1):  # ストレッチを除く
                widget = self.items_layout.itemAt(i).widget()
                if widget and hasattr(widget, 'item_info'):
                    self.original_positions[widget] = widget.pos()
            print(f"元の位置を保存: {len(self.original_positions)}個")
        except Exception as e:
            print(f"元の位置保存エラー: {e}")
            
    def reset_to_original_positions(self):
        """全ウィジェットを元の位置に戻す"""
        try:
            for widget, original_pos in self.original_positions.items():
                widget.move(original_pos)
            print("元の位置に復元")
        except Exception as e:
            print(f"元の位置復元エラー: {e}")
            
    def calculate_new_positions_from_original(self, widgets, from_index, to_index):
        """元の位置を基準に新しい順序でのY位置を計算"""
        try:
            if not widgets or not self.original_positions:
                return [widget.y() for widget in widgets]
                
            # 元の位置から基準Y座標を取得
            first_widget = widgets[0]  
            base_y = self.original_positions[first_widget].y()
            
            # 結果配列を初期化（元の順序での位置）
            result_positions = []
            for i in range(len(widgets)):
                result_positions.append(base_y + (i * self.item_height))
            
            # 並び替えのシミュレーション
            # 元のfrom_indexの位置にあるアイテムをto_indexに移動
            if from_index != to_index:
                # ドラッグされるアイテムの新しい位置
                dragged_y = base_y + (to_index * self.item_height)
                
                if from_index < to_index:
                    # 下に移動: from+1からtoまでを1つ上に
                    for i in range(from_index + 1, to_index + 1):
                        result_positions[i] = base_y + ((i - 1) * self.item_height)
                else:
                    # 上に移動: toからfrom-1までを1つ下に
                    for i in range(to_index, from_index):
                        result_positions[i] = base_y + ((i + 1) * self.item_height)
                        
                # ドラッグされたアイテムの位置を設定
                result_positions[from_index] = dragged_y
            
            print(f"簡単計算: {from_index}->{to_index}, 結果Y座標:{[int(y) for y in result_positions]}")
            return result_positions
            
        except Exception as e:
            print(f"位置計算エラー: {e}")
            return [self.original_positions.get(widget, widget.pos()).y() for widget in widgets]
            
    def show_drag_preview(self, target_index):
        """ドラッグプレビューを表示（アイテムを実際に移動）"""
        try:
            # アイテム数チェック
            item_count = len(self.group_icon.items)
            if target_index < 0 or target_index > item_count:
                return
                
            # 現在のウィジェットリストを取得
            widgets = []
            for i in range(self.items_layout.count() - 1):  # ストレッチを除く
                widget = self.items_layout.itemAt(i).widget()
                if widget and hasattr(widget, 'item_info'):
                    widgets.append(widget)
                    
            if not widgets:
                return
                
            # ドラッグ中のアイテムを探す
            dragged_widget = None
            dragged_index = -1
            
            # 現在ドラッグ中のウィジェットを特定
            for i, widget in enumerate(widgets):
                if hasattr(widget, 'is_being_dragged') and widget.is_being_dragged:
                    dragged_widget = widget
                    dragged_index = i
                    break
                    
            if dragged_widget is None:
                return
                
            # 同じ位置なら何もしない
            if dragged_index == target_index:
                # 元の位置に戻す
                self.reset_to_original_positions()
                return
                
            # アニメーション付きで位置を変更
            self.animate_reorder_preview(widgets, dragged_index, target_index)
                        
        except Exception as e:
            print(f"ドラッグプレビューエラー: {e}")
            
    def animate_reorder_preview(self, widgets, from_index, to_index):
        """アイテムの位置をアニメーション付きで変更"""
        try:
            # 既存のアニメーションを停止
            if self.animation_group:
                self.animation_group.stop()
                
            # まず全てのウィジェットを元の位置に戻す
            self.reset_to_original_positions()
            
            self.animation_group = QParallelAnimationGroup()
            self.animating_widgets = []
            
            # 新しい順序でのY位置を計算（元の位置ベース）
            new_positions = self.calculate_new_positions_from_original(widgets, from_index, to_index)
            
            # 全てのアイテムを新しい位置にアニメーション
            for i, widget in enumerate(widgets):
                target_y = new_positions[i]
                current_y = widget.y()
                
                if current_y != target_y:
                    # ドラッグ中のアイテムは少し長めのアニメーション
                    duration = 300 if i == from_index else 250
                    self.animate_widget_to_position(widget, target_y, duration)
                    
            # アニメーション開始
            if self.animation_group.animationCount() > 0:
                self.animation_group.start()
                
        except Exception as e:
            print(f"並び替えプレビューアニメーションエラー: {e}")
            
    def calculate_new_positions(self, widgets, from_index, to_index):
        """新しい順序での各ウィジェットのY位置を計算"""
        try:
            if not widgets:
                return []
                
            # 現在の位置を基準にする
            positions = [widget.y() for widget in widgets]
            result_positions = positions.copy()
            
            # ドラッグされるアイテムの新しい位置
            dragged_y = positions[0] + (to_index * self.item_height)
            result_positions[from_index] = dragged_y
            
            # 他のアイテムの位置を調整
            if from_index < to_index:
                # 下に移動: from+1からtoまでのアイテムを1つ上に
                for i in range(from_index + 1, min(to_index + 1, len(widgets))):
                    result_positions[i] = positions[0] + ((i - 1) * self.item_height)
            else:
                # 上に移動: toからfrom-1までのアイテムを1つ下に
                for i in range(to_index, from_index):
                    result_positions[i] = positions[0] + ((i + 1) * self.item_height)
                    
            print(f"位置計算: {from_index}->{to_index}, 元位置:{positions}, 新位置:{result_positions}")
            return result_positions
            
        except Exception as e:
            print(f"新しい位置計算エラー: {e}")
            return [widget.y() for widget in widgets]
            
    def animate_widget_to_position(self, widget, target_y, duration):
        """ウィジェットを指定されたY座標に移動するアニメーション"""
        try:
            # 現在の位置を取得
            current_pos = widget.pos()
            target_pos = QPoint(current_pos.x(), target_y)
            
            # アニメーションを作成
            animation = QPropertyAnimation(widget, b"pos")
            animation.setDuration(duration)
            animation.setStartValue(current_pos)
            animation.setEndValue(target_pos)
            animation.setEasingCurve(QEasingCurve.Type.OutQuart)  # より滑らかなイージング
            
            # アニメーション終了時の処理
            animation.finished.connect(lambda: self.on_animation_finished(widget))
            
            # アニメーショングループに追加
            self.animation_group.addAnimation(animation)
            self.animating_widgets.append(widget)
            
            print(f"位置アニメーション: {current_pos.y()} -> {target_y}")
            
        except Exception as e:
            print(f"位置移動アニメーションエラー: {e}")
            
    def animate_widget_shift(self, widget, y_offset, duration):
        """ウィジェットを指定された距離だけ移動するアニメーション（後方互換性のため残す）"""
        try:
            current_y = widget.y()
            target_y = current_y + y_offset
            self.animate_widget_to_position(widget, target_y, duration)
            
        except Exception as e:
            print(f"ウィジェット移動アニメーションエラー: {e}")
            
    def on_animation_finished(self, widget):
        """アニメーション終了時の処理"""
        try:
            if widget in self.animating_widgets:
                self.animating_widgets.remove(widget)
                
            # 全てのアニメーションが終了したかチェック
            if not self.animating_widgets:
                print("全てのアニメーションが完了")
                
        except Exception as e:
            print(f"アニメーション終了処理エラー: {e}")
            
    def clear_drag_preview(self):
        """ドラッグプレビューをクリア"""
        try:
            # 全てのアニメーションを停止
            if self.animation_group:
                self.animation_group.stop()
                self.animation_group = None
                
            self.animating_widgets.clear()
            
            # 元の位置に復元
            self.reset_to_original_positions()
            
            # 全てのアイテムウィジェットのスタイルをリセット
            for i in range(self.items_layout.count() - 1):  # ストレッチを除く
                widget = self.items_layout.itemAt(i).widget()
                if widget and hasattr(widget, 'item_info'):
                    # ドラッグ中フラグをクリア
                    if hasattr(widget, 'is_being_dragged'):
                        widget.is_being_dragged = False
                        
                    # 元のスタイルに戻す
                    widget.setStyleSheet("""
                        QFrame {
                            background-color: rgba(255, 255, 255, 240);
                            border: 1px solid rgba(200, 200, 200, 150);
                            border-radius: 5px;
                            margin: 1px;
                        }
                        QFrame:hover {
                            background-color: rgba(220, 240, 255, 240);
                            border: 1px solid rgba(100, 150, 255, 200);
                        }
                    """)
            
            # 元の位置データをクリア
            self.original_positions.clear()
                    
        except Exception as e:
            print(f"ドラッグプレビュークリアエラー: {e}")
            
    def reorder_item_with_animation(self, item_widget, new_index):
        """アニメーション付きアイテム並び替え"""
        try:
            # まずプレビューをクリア
            self.clear_drag_preview()
            
            # 通常の並び替え処理を実行
            self.reorder_item(item_widget, new_index)
            
        except Exception as e:
            print(f"アニメーション付き並び替えエラー: {e}")
            
    def reorder_item_by_path(self, item_path, new_index):
        """パスを指定してアイテムの並び順を変更"""
        try:
            # 現在のアイテムのインデックスを取得
            current_index = -1
            for i, item_info in enumerate(self.group_icon.items):
                if item_info['path'] == item_path:
                    current_index = i
                    break
                    
            if current_index == -1:
                return  # アイテムが見つからない
                
            # 同じ位置の場合は何もしない
            if current_index == new_index:
                return
                
            # アイテムを移動
            item_info = self.group_icon.items.pop(current_index)
            self.group_icon.items.insert(new_index, item_info)
            
            # UIを更新
            self.refresh_items()
            
            # データを保存
            self.group_icon.items_changed.emit()
            
            print(f"パス指定並び替え: {current_index} -> {new_index} ({item_path})")
            
        except Exception as e:
            print(f"パス指定並び替えエラー: {e}")