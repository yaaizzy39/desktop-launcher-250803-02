"""
ItemListWindow - 登録されたアイテムのリストを表示するウィンドウ
"""

import os
import subprocess
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                            QPushButton, QLabel, QFrame, QApplication,
                            QMessageBox, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction


class ItemWidget(QFrame):
    """個別アイテムを表示するウィジェット"""
    
    launch_requested = pyqtSignal(str)  # 起動要求シグナル
    remove_requested = pyqtSignal(str)  # 削除要求シグナル
    
    def __init__(self, item_info):
        super().__init__()
        self.item_info = item_info
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
        
        # タイプに応じてアイコンを設定
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
        
    def mousePressEvent(self, event):
        """マウスクリックで起動"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.launch_requested.emit(self.item_info['path'])
        super().mousePressEvent(event)


class ItemListWindow(QWidget):
    """アイテムリストウィンドウ"""
    
    def __init__(self, group_icon):
        super().__init__()
        self.group_icon = group_icon
        self.setup_ui()
        self.setup_window()
        
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
        
        # タイトル
        title_label = QLabel(f"📁 {str(self.group_icon.name)}")
        title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        
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
        
        header_layout.addWidget(title_label)
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
        
        # フッター
        footer_frame = QFrame()
        footer_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(240, 240, 240, 200);
                border-radius: 8px;
                border: 1px solid rgba(200, 200, 200, 150);
            }
        """)
        footer_frame.setFixedHeight(30)
        
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(10, 5, 10, 5)
        
        info_label = QLabel("アイテムをクリックして起動 | ドラッグ&ドロップで追加")
        info_label.setFont(QFont("Arial", 8))
        info_label.setStyleSheet("color: #666;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        footer_layout.addWidget(info_label)
        footer_frame.setLayout(footer_layout)
        
        # レイアウト構成
        main_layout.addWidget(header_frame)
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(footer_frame)
        
        self.setLayout(main_layout)
        
        # 初期アイテム表示
        self.refresh_items()
        
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
            
    def focusOutEvent(self, event):
        """フォーカスを失ったら隠す"""
        # マウスがウィンドウ内にある場合は隠さない
        if not self.underMouse():
            self.hide()
        super().focusOutEvent(event)
        
    def enterEvent(self, event):
        """マウスがウィンドウに入った"""
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """マウスがウィンドウから出た"""
        # 少し遅延してから隠す
        QApplication.instance().processEvents()
        if not self.underMouse():
            self.hide()
        super().leaveEvent(event)