"""
GroupIcon - デスクトップに表示されるグループアイコンウィジェット
"""

import os
import time
from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QApplication, 
                            QMenu, QInputDialog, QMessageBox, QDialog)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import (QPainter, QBrush, QColor, QPen, QFont, 
                        QPixmap, QIcon, QAction, QDrag, QRegion)
from utils.shortcut_resolver import resolve_shortcut, get_display_name


class GroupIcon(QWidget):
    """グループアイコンウィジェット"""
    
    # シグナル定義
    clicked = pyqtSignal(object)  # クリック時
    double_clicked = pyqtSignal(object)  # ダブルクリック時（固定モードで表示）
    position_changed = pyqtSignal()  # 位置変更時
    items_changed = pyqtSignal()  # アイテム変更時
    
    def __init__(self, name="Group", position=QPoint(100, 100), settings_manager=None, main_app=None):
        super().__init__()
        
        self.name = name
        self.items = []  # 登録されたアイテムのリスト
        self.drag_start_position = None
        self.settings_manager = settings_manager
        self.main_app = main_app  # メインアプリケーションへの参照
        self.last_click_time = 0  # ダブルクリック検出用
        self.custom_icon_path = None  # カスタムアイコンのパス
        
        self.setup_ui()
        self.setup_drag_drop()
        
        # ウィンドウの設定
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 位置設定
        self.move(position)
        
    def setup_ui(self):
        """UI設定"""
        self.setFixedSize(80, 80)
        
        # レイアウト
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # アイコン表示用ラベル
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(50, 50)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: rgba(100, 150, 255, 200);
                border-radius: 25px;
                border: 2px solid rgba(255, 255, 255, 100);
            }
        """)
        
        # テキスト表示用ラベル
        self.text_label = QLabel(str(self.name))
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 150);
                border-radius: 8px;
                padding: 2px 4px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        self.setLayout(layout)
        
        # アイテム数表示を更新
        self.update_display()
        
    def setup_drag_drop(self):
        """ドラッグ＆ドロップ設定"""
        self.setAcceptDrops(True)
        
    def update_display(self):
        """表示を更新"""
        # カスタムアイコンがある場合はアイコンを表示、ない場合はアイテム数を表示
        if self.custom_icon_path and os.path.exists(self.custom_icon_path):
            self.display_custom_icon()
        else:
            self.display_item_count()
        
        # グループ名の表示・非表示を設定
        self.update_group_name_visibility()
        
    def update_group_name_visibility(self):
        """グループ名の表示・非表示を更新"""
        if self.settings_manager:
            appearance_settings = self.settings_manager.get_appearance_settings()
            show_names = appearance_settings.get('show_group_names', True)
        else:
            show_names = True
            
        if show_names:
            self.text_label.setText(str(self.name))
            self.text_label.show()
        else:
            self.text_label.hide()
        
    def display_custom_icon(self):
        """カスタムアイコンを表示"""
        try:
            # アイコンを読み込み
            pixmap = QPixmap(self.custom_icon_path)
            if not pixmap.isNull():
                # アイコンサイズに合わせてスケール
                icon_size = self.icon_label.width()
                target_size = icon_size - 4
                scaled_pixmap = pixmap.scaled(target_size, target_size, 
                                            Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
                
                # 円形にマスクされたピクスマップを作成
                circular_pixmap = self.create_circular_pixmap(scaled_pixmap, target_size)
                self.icon_label.setPixmap(circular_pixmap)
                
                # 背景スタイルを設定（アイコン用）
                border_radius = icon_size // 2
                self.icon_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: rgba(255, 255, 255, 200);
                        border-radius: {border_radius}px;
                        border: 2px solid rgba(200, 200, 200, 150);
                    }}
                """)
            else:
                # 読み込み失敗時はアイテム数表示にフォールバック
                self.display_item_count()
        except Exception as e:
            print(f"カスタムアイコン表示エラー: {e}")
            self.display_item_count()
            
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
            
    def display_item_count(self):
        """アイテム数を表示"""
        # アイテム数を表示
        item_count = len(self.items)
        self.icon_label.setText(str(item_count))
        self.icon_label.setPixmap(QPixmap())  # ピクスマップをクリア
        
        # 設定から色を取得、なければデフォルト色を使用
        if self.settings_manager:
            appearance_settings = self.settings_manager.get_appearance_settings()
            icon_color = appearance_settings.get('icon_color', '#6496ff')
        else:
            icon_color = '#6496ff'
            
        # アイコンサイズを取得
        icon_size = self.icon_label.width()
        border_radius = icon_size // 2
        
        # フォントサイズをアイコンサイズに合わせて調整
        font_size = max(12, min(24, icon_size // 4))
        
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {icon_color};
                border-radius: {border_radius}px;
                border: 2px solid rgba(255, 255, 255, 100);
                color: white;
                font-size: {font_size}px;
                font-weight: bold;
            }}
        """)
        
    def mousePressEvent(self, event):
        """マウスプレスイベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())
            
    def mouseMoveEvent(self, event):
        """マウス移動イベント（ドラッグ処理）"""
        if (event.buttons() & Qt.MouseButton.LeftButton and 
            self.drag_start_position is not None):
            
            # ドラッグ距離をチェック
            distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
            if distance >= QApplication.startDragDistance():
                # ウィンドウを移動
                self.move(self.mapToGlobal(event.position().toPoint() - self.drag_start_position))
                
    def mouseReleaseEvent(self, event):
        """マウスリリースイベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drag_start_position is not None:
                # ドラッグ距離をチェック
                distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
                if distance < QApplication.startDragDistance():
                    # ダブルクリック検出
                    current_time = time.time()
                    if current_time - self.last_click_time < 0.3:  # 300ms以内ならダブルクリック
                        self.double_clicked.emit(self)
                    else:
                        # シングルクリックとして処理
                        self.clicked.emit(self)
                    
                    self.last_click_time = current_time
                else:
                    # ドラッグ終了として処理
                    self.position_changed.emit()
                    
                self.drag_start_position = None
                
    def show_context_menu(self, position):
        """コンテキストメニューを表示"""
        menu = QMenu(self)
        
        # 名前変更
        rename_action = QAction("名前を変更", self)
        rename_action.triggered.connect(self.rename_group)
        menu.addAction(rename_action)
        
        # アイコンを変更
        icon_action = QAction("アイコンを変更", self)
        icon_action.triggered.connect(self.change_icon)
        menu.addAction(icon_action)
        
        menu.addSeparator()
        
        # 設定
        settings_action = QAction("設定", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        # 整列機能
        align_vertical_action = QAction("縦整列", self)
        align_vertical_action.triggered.connect(self.align_vertically)
        menu.addAction(align_vertical_action)
        
        align_horizontal_action = QAction("横整列", self)
        align_horizontal_action.triggered.connect(self.align_horizontally)
        menu.addAction(align_horizontal_action)
        
        menu.addSeparator()
        
        # アイテムをクリア
        clear_action = QAction("アイテムをクリア", self)
        clear_action.triggered.connect(self.clear_items)
        menu.addAction(clear_action)
        
        # グループを削除
        delete_action = QAction("グループを削除", self)
        delete_action.triggered.connect(self.delete_group)
        menu.addAction(delete_action)
        
        menu.exec(position)
        
    def rename_group(self):
        """グループ名を変更"""
        text, ok = QInputDialog.getText(
            self, "グループ名変更", "新しい名前:", text=self.name
        )
        if ok and text.strip():
            self.name = text.strip()
            self.update_display()
            self.items_changed.emit()
            
    def change_icon(self):
        """アイコンを変更"""
        from ui.icon_selector_dialog import IconSelectorDialog
        
        dialog = IconSelectorDialog(self, self.custom_icon_path)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_icon = dialog.get_selected_icon()
            self.custom_icon_path = selected_icon
            self.update_display()
            self.items_changed.emit()  # データ保存のため
            
    def show_settings(self):
        """設定ウィンドウを表示"""
        if self.main_app:
            self.main_app.show_settings()
        else:
            # main_appが設定されていない場合の警告
            QMessageBox.warning(
                self, "エラー", 
                "設定ウィンドウを表示できません。\nメインアプリケーションとの接続に問題があります。"
            )
            
    def align_vertically(self):
        """縦整列（X位置を統一）"""
        if self.main_app:
            target_x = self.x()
            self.main_app.align_all_icons_vertically(target_x)
        else:
            QMessageBox.warning(
                self, "エラー", 
                "整列機能を実行できません。\nメインアプリケーションとの接続に問題があります。"
            )
            
    def align_horizontally(self):
        """横整列（Y位置を統一）"""
        if self.main_app:
            target_y = self.y()
            self.main_app.align_all_icons_horizontally(target_y)
        else:
            QMessageBox.warning(
                self, "エラー", 
                "整列機能を実行できません。\nメインアプリケーションとの接続に問題があります。"
            )
            
    def clear_items(self):
        """アイテムをクリア"""
        reply = QMessageBox.question(
            self, "確認", "このグループのアイテムをすべて削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.items.clear()
            self.update_display()
            self.items_changed.emit()
            
    def delete_group(self):
        """グループを削除"""
        reply = QMessageBox.question(
            self, "確認", f"グループ '{self.name}' を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            self.deleteLater()
            
    def dragEnterEvent(self, event):
        """ドラッグエンターイベント"""
        if event.mimeData().hasUrls():
            # ファイルやフォルダのドロップを受け入れ
            event.acceptProposedAction()
            self.setStyleSheet("QWidget { border: 2px dashed #ffff00; }")
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        """ドラッグリーブイベント"""
        self.setStyleSheet("")
        
    def dropEvent(self, event):
        """ドロップイベント"""
        self.setStyleSheet("")
        
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path:
                    self.add_item(file_path)
                    
            event.acceptProposedAction()
            self.items_changed.emit()
        else:
            event.ignore()
            
    def add_item(self, file_path):
        """アイテムを追加"""
        # ショートカットの場合はリンク先を解決
        resolved_path = resolve_shortcut(file_path)
        
        # 既に存在するかチェック（解決後のパスで）
        for item in self.items:
            if item['path'] == resolved_path:
                return  # 重複なので追加しない
                
        # 表示名を取得（ショートカットの場合は.lnkを除去）
        display_name = get_display_name(file_path)
        
        # アイテム情報を作成
        item_info = {
            'path': resolved_path,  # 解決後のパスを保存
            'name': display_name,   # 表示用の名前
            'type': 'folder' if os.path.isdir(resolved_path) else 'file',
            'original_path': file_path  # 元のパス（ショートカットの場合のため）
        }
        
        self.items.append(item_info)
        self.update_display()
        self.items_changed.emit()
        
    def remove_item(self, item_path):
        """アイテムを削除"""
        self.items = [item for item in self.items if item['path'] != item_path]
        self.update_display()
        self.items_changed.emit()
        
    def apply_appearance_settings(self, settings):
        """外観設定を適用"""
        try:
            # サイズ変更
            icon_size = settings.get('icon_size', 80)
            self.setFixedSize(icon_size, icon_size)
            
            # アイコンラベルサイズ調整
            icon_label_size = int(icon_size * 0.6)
            self.icon_label.setFixedSize(icon_label_size, icon_label_size)
            
            # 透明度適用
            opacity = settings.get('opacity', 80) / 100.0
            self.setWindowOpacity(opacity)
            
            # 常に最前面設定
            always_on_top = settings.get('always_on_top', True)
            flags = self.windowFlags()
            if always_on_top:
                flags |= Qt.WindowType.WindowStaysOnTopHint
            else:
                flags &= ~Qt.WindowType.WindowStaysOnTopHint
            self.setWindowFlags(flags)
            
            # 表示を更新（カスタムアイコンがあればそれを表示、なければ数字を表示）
            self.update_display()
            
            # グループ名の表示設定を適用
            self.update_group_name_visibility()
            
            self.show()  # フラグ変更後に再表示
            
        except Exception as e:
            print(f"外観設定適用エラー: {e}")
            
    def get_current_settings(self):
        """現在の設定を取得"""
        if self.settings_manager:
            return self.settings_manager.get_appearance_settings()
        return {}