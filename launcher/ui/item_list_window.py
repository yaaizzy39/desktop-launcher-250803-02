"""
ItemListWindow - 登録されたアイテムのリストを表示するウィンドウ
"""

import os
import subprocess
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                            QPushButton, QLabel, QFrame, QApplication,
                            QMessageBox, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QMimeData, QUrl
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction, QDrag
from ui.icon_utils import icon_extractor


class ItemWidget(QFrame):
    """個別アイテムを表示するウィジェット"""
    
    launch_requested = pyqtSignal(str)  # 起動要求シグナル
    remove_requested = pyqtSignal(str)  # 削除要求シグナル
    
    def __init__(self, item_info):
        super().__init__()
        self.item_info = item_info
        self.drag_start_position = None
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
        
        # 削除ボタン
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 100, 100, 200);
                border: none;
                border-radius: 10px;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 50, 50, 255);
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.item_info['path']))
        
        # レイアウト構成
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)
        info_layout.addWidget(name_label)
        info_layout.addWidget(path_label)
        
        layout.addWidget(icon_label)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(remove_btn)
        
        self.setLayout(layout)
        
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
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """マウス移動イベント（ドラッグ処理）"""
        if (event.buttons() & Qt.MouseButton.LeftButton and 
            self.drag_start_position is not None):
            
            # ドラッグ距離をチェック
            distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
            if distance >= QApplication.startDragDistance():
                # ドラッグ操作を開始
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


class ItemListWindow(QWidget):
    """アイテムリストウィンドウ"""
    
    def __init__(self, group_icon):
        super().__init__()
        self.group_icon = group_icon
        self.mouse_entered = False
        self.mouse_left_after_enter = False
        self.is_pinned = False  # 固定表示モード
        
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
        self.setFixedSize(300, 400)
        
        # メインレイアウト
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
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
        header_layout.setContentsMargins(10, 5, 10, 5)
        
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
        
        # アイテムコンテナ
        self.items_widget = QWidget()
        self.items_layout = QVBoxLayout()
        self.items_layout.setContentsMargins(5, 5, 5, 5)
        self.items_layout.setSpacing(2)
        self.items_layout.addStretch()
        self.items_widget.setLayout(self.items_layout)
        
        scroll_area.setWidget(self.items_widget)
        
        # レイアウト構成
        main_layout.addWidget(header_frame)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        
        # 初期アイテム表示
        self.refresh_items()
        self.update_title_display()
        
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
        reply = QMessageBox.question(
            self, "確認", 
            f"このアイテムをリストから削除しますか?\n{os.path.basename(item_path)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.group_icon.remove_item(item_path)
            
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
        if self.mouse_entered and not self.is_pinned:  # 固定モードでない場合のみ
            self.mouse_left_after_enter = True
            # 少し遅延してから隠す（誤操作防止）
            self.hide_timer.start(300)  # 300ms後に隠す
        super().leaveEvent(event)
        
    def delayed_hide(self):
        """遅延非表示処理"""
        # 固定モードの場合は隠さない
        if self.is_pinned:
            return
        # マウスがウィンドウ内に戻ってきていないかチェック
        if not self.underMouse() and self.mouse_left_after_enter:
            self.hide()
            
    def focusOutEvent(self, event):
        """フォーカスを失ったら隠す"""
        # 固定モードまたはマウスがウィンドウ内にある場合は隠さない
        if not self.is_pinned and not self.underMouse():
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
        if event.mimeData().hasFormat("application/x-launcher-item") or event.mimeData().hasUrls():
            event.acceptProposedAction()
            # ドロップ可能な視覚フィードバック
            self.setStyleSheet("QWidget { border: 2px dashed #00ff00; }")
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        """ドラッグリーブイベント"""
        self.setStyleSheet("")
        
    def dropEvent(self, event):
        """ドロップイベント"""
        self.setStyleSheet("")
        
        # リスト間移動の場合
        if event.mimeData().hasFormat("application/x-launcher-item"):
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