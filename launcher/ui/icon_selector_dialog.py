"""
IconSelectorDialog - アイコン選択ダイアログ
"""

import os
import sys
import shutil
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QScrollArea, QWidget, QPushButton, QLabel,
                            QGridLayout, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor, QRegion


def write_debug_log(message):
    """デバッグ情報をファイルに出力（現在無効化）"""
    # デバッグログ出力を一時停止
    pass

def get_icons_directory():
    """アイコンディレクトリのパスを取得（開発環境とビルド環境に対応）"""
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた環境
        base_path = os.path.dirname(sys.executable)
        icons_dir = os.path.join(base_path, "icons")
        
        write_debug_log(f"get_icons_directory: ビルド環境, base_path = {base_path}")
        write_debug_log(f"get_icons_directory: icons_dir = {icons_dir}")
        
        # iconsフォルダが存在しない場合は作成
        if not os.path.exists(icons_dir):
            write_debug_log(f"get_icons_directory: iconsフォルダが存在しないため作成")
            os.makedirs(icons_dir, exist_ok=True)
            
        # バンドルされたアイコンをコピー（初回起動時のみ）
        bundled_icons_dir = os.path.join(sys._MEIPASS, "icons")
        write_debug_log(f"get_icons_directory: bundled_icons_dir = {bundled_icons_dir}")
        write_debug_log(f"get_icons_directory: bundled_icons_dir 存在? {os.path.exists(bundled_icons_dir)}")
        write_debug_log(f"get_icons_directory: icons_dir内容 = {os.listdir(icons_dir) if os.path.exists(icons_dir) else 'フォルダ存在せず'}")
        
        if os.path.exists(bundled_icons_dir) and (not os.path.exists(icons_dir) or not os.listdir(icons_dir)):
            write_debug_log(f"get_icons_directory: バンドルされたアイコンをコピー中...")
            for item in os.listdir(bundled_icons_dir):
                src = os.path.join(bundled_icons_dir, item)
                dst = os.path.join(icons_dir, item)
                if os.path.isfile(src):
                    write_debug_log(f"get_icons_directory: {src} -> {dst}")
                    shutil.copy2(src, dst)
                    
        return icons_dir
    else:
        # 開発環境
        dev_icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")
        write_debug_log(f"get_icons_directory: 開発環境, icons_dir = {dev_icons_dir}")
        return dev_icons_dir


def ensure_user_icons_directory():
    """ユーザーがアイコンを追加できるディレクトリを確保"""
    icons_dir = get_icons_directory()
    if not os.path.exists(icons_dir):
        os.makedirs(icons_dir, exist_ok=True)
    return icons_dir


def resolve_icon_path(icon_path):
    """アイコンパスを実行環境に応じて解決"""
    write_debug_log(f"resolve_icon_path: 入力パス = {icon_path}")
    
    if not icon_path:
        write_debug_log(f"resolve_icon_path: パスが空のため None を返す")
        return None
    
    icons_dir = get_icons_directory()
    write_debug_log(f"resolve_icon_path: アイコンディレクトリ = {icons_dir}")
        
    # 絶対パスの場合
    if os.path.isabs(icon_path):
        write_debug_log(f"resolve_icon_path: 絶対パスとして処理")
        
        # ビルド環境では常にアイコンディレクトリ内を優先して使用
        filename = os.path.basename(icon_path)
        alt_path = os.path.join(icons_dir, filename)
        write_debug_log(f"resolve_icon_path: アイコンディレクトリ内をチェック = {alt_path}")
        if os.path.exists(alt_path):
            write_debug_log(f"resolve_icon_path: アイコンディレクトリ内でファイル存在確認OK")
            return alt_path
            
        # アイコンディレクトリ内にない場合のみ、元のパスをチェック
        if os.path.exists(icon_path):
            write_debug_log(f"resolve_icon_path: 絶対パスでファイル存在確認OK")
            return icon_path
    else:
        write_debug_log(f"resolve_icon_path: 相対パスとして処理")
        # 相対パスの場合はアイコンディレクトリ内で検索
        full_path = os.path.join(icons_dir, icon_path)
        write_debug_log(f"resolve_icon_path: フルパス = {full_path}")
        if os.path.exists(full_path):
            write_debug_log(f"resolve_icon_path: フルパスでファイル存在確認OK")
            return full_path
            
        # ファイル名のみの場合
        filename = os.path.basename(icon_path)
        alt_path = os.path.join(icons_dir, filename)
        write_debug_log(f"resolve_icon_path: ファイル名のみの代替パス = {alt_path}")
        if os.path.exists(alt_path):
            write_debug_log(f"resolve_icon_path: ファイル名のみの代替パスでファイル存在確認OK")
            return alt_path
    
    write_debug_log(f"resolve_icon_path: ファイルが見つからないため None を返す")
    return None  # 見つからない場合


def get_relative_icon_path(icon_path):
    """アイコンパスを相対パス（ファイル名のみ）に変換"""
    if not icon_path:
        return None
        
    icons_dir = get_icons_directory()
    
    # iconsディレクトリ内のファイルかチェック
    if icon_path.startswith(icons_dir):
        return os.path.basename(icon_path)
    
    # 他の場所のファイルの場合はファイル名のみ返す
    return os.path.basename(icon_path)


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
        # 円形の背景スタイルを設定
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 200);
                border-radius: 32px;
                border: 2px solid rgba(200, 200, 200, 150);
            }
        """)
        
        # アイコンを読み込み
        pixmap = QPixmap(self.icon_path)
        if not pixmap.isNull():
            # 64x64にスケール
            scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, 
                                        Qt.TransformationMode.SmoothTransformation)
            # 円形にマスク
            circular_pixmap = self.create_circular_pixmap(scaled_pixmap, 64)
            self.icon_label.setPixmap(circular_pixmap)
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
        
    def create_circular_pixmap(self, source_pixmap, size):
        """ピクスマップを円形にマスクする"""
        # 正方形のピクスマップを作成
        circular_pixmap = QPixmap(size, size)
        circular_pixmap.fill(QColor(0, 0, 0, 0))  # 透明で初期化
        
        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 円形の描画領域を設定
        region = QRegion(0, 0, size, size, QRegion.RegionType.Ellipse)
        painter.setClipRegion(region)
        
        # 画像を中央に描画
        x = (size - source_pixmap.width()) // 2
        y = (size - source_pixmap.height()) // 2
        painter.drawPixmap(x, y, source_pixmap)
        
        painter.end()
        return circular_pixmap
        
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
        
        # アイコンフォルダのパス（ビルド環境対応）
        icons_dir = ensure_user_icons_directory()
        
        # 単一のアイコンタブを作成
        self.icon_tab = IconCategoryTab(icons_dir, "アイコン")
        self.icon_tab.icon_selected.connect(self.on_icon_selected)
        
        layout.addWidget(self.icon_tab)
        
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