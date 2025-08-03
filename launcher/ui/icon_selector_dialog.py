"""
IconSelectorDialog - アイコン選択ダイアログ
"""

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QScrollArea, QWidget, QPushButton, QLabel,
                            QGridLayout, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon


class IconPreviewWidget(QFrame):
    """アイコンプレビューウィジェット"""
    
    icon_selected = pyqtSignal(str)  # アイコンパスが選択された時
    
    def __init__(self, icon_path, icon_name):
        super().__init__()
        self.icon_path = icon_path
        self.icon_name = icon_name
        self.selected = False
        self.setup_ui()
        
    def setup_ui(self):
        """UI設定"""
        self.setFixedSize(80, 100)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # アイコン表示
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # アイコンを読み込み
        pixmap = QPixmap(self.icon_path)
        if not pixmap.isNull():
            # 64x64にスケール
            scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, 
                                        Qt.TransformationMode.SmoothTransformation)
            self.icon_label.setPixmap(scaled_pixmap)
        else:
            # 読み込み失敗時のフォールバック
            self.icon_label.setText("❌")
            self.icon_label.setStyleSheet("color: red; font-size: 32px;")
            
        # 名前表示
        self.name_label = QLabel(self.icon_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-size: 10px; color: #666;")
        self.name_label.setWordWrap(True)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label)
        self.setLayout(layout)
        
        self.update_style()
        
    def update_style(self):
        """スタイルを更新"""
        if self.selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(100, 150, 255, 100);
                    border: 2px solid #6496ff;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 50);
                    border: 1px solid rgba(200, 200, 200, 100);
                    border-radius: 8px;
                }
                QFrame:hover {
                    background-color: rgba(220, 240, 255, 100);
                    border: 1px solid rgba(100, 150, 255, 150);
                }
            """)
            
    def set_selected(self, selected):
        """選択状態を設定"""
        self.selected = selected
        self.update_style()
        
    def mousePressEvent(self, event):
        """マウスクリック時"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.icon_selected.emit(self.icon_path)
        super().mousePressEvent(event)


class IconCategoryTab(QWidget):
    """アイコンカテゴリタブ"""
    
    icon_selected = pyqtSignal(str)
    
    def __init__(self, category_path, category_name):
        super().__init__()
        self.category_path = category_path
        self.category_name = category_name
        self.icon_widgets = []
        self.selected_widget = None
        self.setup_ui()
        self.load_icons()
        
    def setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # アイコングリッドコンテナ
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_widget.setLayout(self.grid_layout)
        
        scroll_area.setWidget(self.grid_widget)
        layout.addWidget(scroll_area)
        self.setLayout(layout)
        
    def load_icons(self):
        """アイコンを読み込み"""
        if not os.path.exists(self.category_path):
            # カテゴリフォルダが存在しない場合
            no_icons_label = QLabel(f"{self.category_name}フォルダにアイコンがありません")
            no_icons_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_icons_label.setStyleSheet("color: #999; font-style: italic; padding: 50px;")
            self.grid_layout.addWidget(no_icons_label, 0, 0)
            return
            
        # サポートされている拡張子
        supported_extensions = ['.png', '.ico', '.svg', '.jpg', '.jpeg']
        
        # アイコンファイルを検索
        icon_files = []
        for file_name in os.listdir(self.category_path):
            file_path = os.path.join(self.category_path, file_name)
            if (os.path.isfile(file_path) and 
                any(file_name.lower().endswith(ext) for ext in supported_extensions)):
                icon_files.append((file_path, file_name))
                
        if not icon_files:
            # アイコンファイルがない場合
            no_icons_label = QLabel(f"{self.category_name}にアイコンファイルがありません")
            no_icons_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_icons_label.setStyleSheet("color: #999; font-style: italic; padding: 50px;")
            self.grid_layout.addWidget(no_icons_label, 0, 0)
            return
            
        # アイコンウィジェットを作成
        row = 0
        col = 0
        max_cols = 6  # 1行に表示する最大アイコン数
        
        for file_path, file_name in sorted(icon_files):
            # 拡張子を除いた名前
            icon_name = os.path.splitext(file_name)[0]
            
            icon_widget = IconPreviewWidget(file_path, icon_name)
            icon_widget.icon_selected.connect(self.on_icon_selected)
            
            self.icon_widgets.append(icon_widget)
            self.grid_layout.addWidget(icon_widget, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
    def on_icon_selected(self, icon_path):
        """アイコンが選択された時"""
        # 前の選択を解除
        if self.selected_widget:
            self.selected_widget.set_selected(False)
            
        # 新しい選択を設定
        sender = self.sender()
        if isinstance(sender, IconPreviewWidget):
            sender.set_selected(True)
            self.selected_widget = sender
            
        self.icon_selected.emit(icon_path)


class IconSelectorDialog(QDialog):
    """アイコン選択ダイアログ"""
    
    def __init__(self, parent=None, current_icon=None):
        super().__init__(parent)
        self.current_icon = current_icon
        self.selected_icon_path = None
        self.setup_ui()
        self.setup_window()
        
    def setup_window(self):
        """ウィンドウ設定"""
        self.setWindowTitle("グループアイコンを選択")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
    def setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # タイトル
        title_label = QLabel("グループアイコンを選択してください")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # アイコンフォルダのパス
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")
        
        # カテゴリタブを作成
        categories = [
            ("apps", "アプリ"),
            ("folders", "フォルダ"),
            ("categories", "カテゴリ"),
            ("custom", "カスタム")
        ]
        
        for folder_name, display_name in categories:
            category_path = os.path.join(icons_dir, folder_name)
            tab = IconCategoryTab(category_path, display_name)
            tab.icon_selected.connect(self.on_icon_selected)
            self.tab_widget.addTab(tab, display_name)
            
        layout.addWidget(self.tab_widget)
        
        # プレビューエリア
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("選択中:"))
        
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(32, 32)
        self.preview_label.setStyleSheet("border: 1px solid #ccc;")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        
        self.preview_path_label = QLabel("未選択")
        self.preview_path_label.setStyleSheet("color: #666;")
        preview_layout.addWidget(self.preview_path_label)
        preview_layout.addStretch()
        
        layout.addLayout(preview_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # デフォルトに戻すボタン
        default_btn = QPushButton("デフォルトに戻す")
        default_btn.clicked.connect(self.reset_to_default)
        button_layout.addWidget(default_btn)
        
        # キャンセルボタン
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # OKボタン
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setEnabled(False)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def on_icon_selected(self, icon_path):
        """アイコンが選択された時"""
        self.selected_icon_path = icon_path
        
        # プレビューを更新
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
        else:
            self.preview_label.setText("❌")
            
        self.preview_path_label.setText(os.path.basename(icon_path))
        self.ok_btn.setEnabled(True)
        
    def reset_to_default(self):
        """デフォルトアイコンに戻す"""
        self.selected_icon_path = None
        self.preview_label.clear()
        self.preview_label.setText("デフォルト")
        self.preview_path_label.setText("数字表示")
        self.ok_btn.setEnabled(True)
        
    def get_selected_icon(self):
        """選択されたアイコンパスを取得"""
        return self.selected_icon_path