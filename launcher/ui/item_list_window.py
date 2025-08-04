"""
ItemListWindow - 登録されたアイテムのリストを表示するウィンドウ
"""

import os
import subprocess
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                            QPushButton, QLabel, QFrame, QApplication,
                            QMessageBox, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QMimeData, QUrl, QPoint
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction, QDrag, QPainter
from ui.icon_utils import icon_extractor


class ItemWidget(QFrame):
    """個別アイテムを表示するウィジェット"""
    
    launch_requested = pyqtSignal(str)  # 起動要求シグナル
    remove_requested = pyqtSignal(str)  # 削除要求シグナル
    reorder_requested = pyqtSignal(object, int)  # 並び替え要求シグナル (item_widget, new_index)
    
    def __init__(self, item_info):
        super().__init__()
        self.item_info = item_info
        self.drag_start_position = None
        self.is_reorder_drag = False  # 並び替えドラッグかどうか
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
        
        # パス（簡略表示）
        path_text = self.item_info['path']
        if len(path_text) > 40:
            path_text = "..." + path_text[-37:]
        path_label = QLabel(path_text)
        path_label.setFont(QFont("Arial", 8))
        path_label.setStyleSheet("color: #666;")
        
        # 削除ボタンを廃止（右クリックメニューで削除に変更）
        
        # レイアウト構成
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)
        info_layout.addWidget(name_label)
        info_layout.addWidget(path_label)
        
        layout.addWidget(icon_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 右クリックメニューを有効にする
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
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
                # Shiftキーが押されている場合は並び替えドラッグ
                modifiers = QApplication.keyboardModifiers()
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    self.is_reorder_drag = True
                    self.start_reorder_drag()
                else:
                    self.is_reorder_drag = False
                    # 通常のドラッグ操作を開始
                    self.start_drag()
                
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
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # ファイルパスをMimeDataに設定
        mime_data.setUrls([QUrl.fromLocalFile(self.item_info['path'])])
        # カスタムデータも設定（リスト間移動用）
        mime_data.setData("application/x-launcher-item", str(self.item_info['path']).encode('utf-8'))
        
        drag.setMimeData(mime_data)
        
        # ドラッグ実行
        drop_action = drag.exec(Qt.DropAction.MoveAction | Qt.DropAction.CopyAction)
        
    def start_reorder_drag(self):
        """並び替えドラッグ操作を開始"""
        # 親ウィンドウに並び替えドラッグ開始を通知
        parent_list = self.parent()
        while parent_list and not isinstance(parent_list, ItemListWindow):
            parent_list = parent_list.parent()
        
        if parent_list:
            parent_list.reorder_drag_active = True
            
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 並び替え用のカスタムデータを設定
        mime_data.setData("application/x-launcher-reorder", str(id(self)).encode('utf-8'))
        
        drag.setMimeData(mime_data)
        
        # ドラッグ実行
        drop_action = drag.exec(Qt.DropAction.MoveAction)
        
        # ドラッグ終了後にフラグを解除
        if parent_list:
            parent_list.reorder_drag_active = False
        
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
    
    def __init__(self, group_icon):
        super().__init__()
        self.group_icon = group_icon
        self.mouse_entered = False
        self.mouse_left_after_enter = False
        self.is_pinned = False  # 固定表示モード
        self.dialog_showing = False  # ダイアログ表示中フラグ
        self.reorder_drag_active = False  # 並び替えドラッグ中フラグ
        
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
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # フォーカスを失ったら自動的に隠す
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        
    def setup_drag_drop(self):
        """ドラッグ&ドロップ設定"""
        self.setAcceptDrops(True)
        
    def setup_ui(self):
        """UI設定"""
        # 初期サイズを設定（後で動的に調整される）
        self.setFixedWidth(300)  # 幅は固定
        self.min_height = 120    # 最小高さ（ヘッダー + 余白）
        self.max_height = 600    # 最大高さ
        self.item_height = 42    # アイテム1個あたりの高さ（アイテム高さ40px + 余白2px）
        
        # メインレイアウト - 左マージンをさらに削減
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 8, 8, 8)  # 左マージンを0pxに、他も少し削減
        main_layout.setSpacing(3)
        
        # ヘッダー
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(100, 150, 255, 220);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 100);
            }
        """)
        header_frame.setFixedHeight(40)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(6, 5, 8, 5)  # 左マージンを削減
        
        # タイトル（ダブルクリック可能）
        self.title_label = QLabel(f"📁 {str(self.group_icon.name)}")
        self.title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title_label.mouseDoubleClickEvent = self.toggle_pin_mode
        
        # 閉じるボタン
        close_btn = QPushButton("×")
        close_btn.setFixedSize(25, 25)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 100, 100, 200);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 50, 50, 255);
            }
        """)
        close_btn.clicked.connect(self.hide)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        header_frame.setLayout(header_layout)
        
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
        main_layout.addWidget(header_frame)
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
        
    def refresh_items(self):
        """アイテムリストを更新"""
        # 既存のアイテムウィジェットを削除
        for i in reversed(range(self.items_layout.count() - 1)):  # ストレッチを除く
            child = self.items_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
                
        # 新しいアイテムウィジェットを追加
        for item_info in self.group_icon.items:
            item_widget = ItemWidget(item_info)
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
        
        # ダイアログを常に最前面に表示
        msg_box.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        
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
            not self.dialog_showing and not self.reorder_drag_active):  # 並び替えドラッグ中でない場合のみ
            self.mouse_left_after_enter = True
            # 少し遅延してから隠す（誤操作防止）
            self.hide_timer.start(300)  # 300ms後に隠す
        super().leaveEvent(event)
        
    def delayed_hide(self):
        """遅延非表示処理"""
        # 固定モード、ダイアログ表示中、または並び替えドラッグ中の場合は隠さない
        if self.is_pinned or self.dialog_showing or self.reorder_drag_active:
            return
        # マウスがウィンドウ内に戻ってきていないかチェック
        if not self.underMouse() and self.mouse_left_after_enter:
            self.hide()
            
    def focusOutEvent(self, event):
        """フォーカスを失ったら隠す"""
        # 固定モード、マウスがウィンドウ内、ダイアログ表示中、または並び替えドラッグ中は隠さない
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
            event.acceptProposedAction()
            # ドロップ可能な視覚フィードバック
            if event.mimeData().hasFormat("application/x-launcher-reorder"):
                self.setStyleSheet("QWidget { border: 2px dashed #ff9900; }")  # 並び替えは橙色
            else:
                self.setStyleSheet("QWidget { border: 2px dashed #00ff00; }")  # 通常は緑色
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        """ドラッグリーブイベント"""
        self.setStyleSheet("")
        
    def dropEvent(self, event):
        """ドロップイベント"""
        self.setStyleSheet("")
        
        # 並び替えドロップの場合
        if event.mimeData().hasFormat("application/x-launcher-reorder"):
            widget_id = event.mimeData().data("application/x-launcher-reorder").data().decode('utf-8')
            
            # ドロップ位置からインデックスを計算
            drop_y = event.position().y()
            target_index = self.calculate_drop_index(drop_y)
            
            # ドラッグされたウィジェットを見つける
            dragged_widget = None
            for i in range(self.items_layout.count() - 1):  # ストレッチを除く
                widget = self.items_layout.itemAt(i).widget()
                if widget and str(id(widget)) == widget_id:
                    dragged_widget = widget
                    break
                    
            if dragged_widget:
                self.reorder_item(dragged_widget, target_index)
                
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
            
            print(f"ウィンドウ高さ調整: アイテム数={item_count}, 高さ={target_height}px")
            
        except Exception as e:
            print(f"ウィンドウ高さ調整エラー: {e}")
            
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