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
from PyQt6.QtSvg import QSvgRenderer
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
        self.is_dragging = False  # ドラッグ中かどうかを追跡
        self.settings_manager = settings_manager
        self.main_app = main_app  # メインアプリケーションへの参照
        self.last_click_time = 0  # ダブルクリック検出用
        self.custom_icon_path = None  # カスタムアイコンのパス
        self.list_window = None  # 対応するリストウィンドウへの参照
        
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
        self.text_label.setFixedWidth(50)  # アイコンの横幅と合わせる
        self.text_label.setFixedHeight(18)  # テキストサイズに合わせて低めに設定
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
        if self.custom_icon_path:
            from ui.icon_selector_dialog import write_debug_log
            write_debug_log(f"update_display: カスタムアイコンパスあり、display_custom_icon()を呼び出し")
            self.display_custom_icon()
        else:
            from ui.icon_selector_dialog import write_debug_log
            write_debug_log(f"update_display: カスタムアイコンなし、display_item_count()を呼び出し")
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
            from ui.icon_selector_dialog import resolve_icon_path, write_debug_log
            write_debug_log(f"display_custom_icon: custom_icon_path = {self.custom_icon_path}")
            
            # アイコンパスを解決
            resolved_path = resolve_icon_path(self.custom_icon_path)
            
            write_debug_log(f"display_custom_icon: resolved_path = {resolved_path}")
            
            if not resolved_path:
                # パスが解決できない場合はアイテム数表示にフォールバック
                write_debug_log(f"display_custom_icon: パスが解決できないため、アイテム数表示にフォールバック")
                self.display_item_count()
                return
            
            # SVGファイルかどうかを判定
            is_svg = resolved_path.lower().endswith('.svg')
            write_debug_log(f"display_custom_icon: is_svg = {is_svg}")
            
            if is_svg:
                # SVGファイルの場合はQSvgRendererを使用
                svg_renderer = QSvgRenderer(resolved_path)
                if svg_renderer.isValid():
                    write_debug_log(f"display_custom_icon: SVGファイル読み込み成功")
                    # アイコンサイズに合わせてピクスマップを作成
                    icon_size = self.icon_label.width()
                    target_size = icon_size - 4
                    
                    pixmap = QPixmap(target_size, target_size)
                    pixmap.fill(Qt.GlobalColor.transparent)
                    
                    painter = QPainter(pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    svg_renderer.render(painter)
                    painter.end()
                    
                    # SVGを円形にマスク
                    write_debug_log(f"display_custom_icon: SVGピクスマップに円形マスクを適用")
                    circular_pixmap = self.create_circular_pixmap(pixmap, target_size)
                    self.icon_label.setPixmap(circular_pixmap)
                    write_debug_log(f"display_custom_icon: SVGピクスマップを設定完了")
                else:
                    write_debug_log(f"display_custom_icon: SVGファイル読み込み失敗")
                    self.display_item_count()
                    return
            else:
                # 通常の画像ファイル
                pixmap = QPixmap(resolved_path)
                write_debug_log(f"display_custom_icon: pixmap.isNull() = {pixmap.isNull()}")
                if not pixmap.isNull():
                    write_debug_log(f"display_custom_icon: アイコン読み込み成功、表示中...")
                    # アイコンサイズに合わせてスケール
                    icon_size = self.icon_label.width()
                    target_size = icon_size - 4
                    scaled_pixmap = pixmap.scaled(target_size, target_size, 
                                                Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation)
                    
                    # 円形にマスクされたピクスマップを作成
                    circular_pixmap = self.create_circular_pixmap(scaled_pixmap, target_size)
                    self.icon_label.setPixmap(circular_pixmap)
                    write_debug_log(f"display_custom_icon: ピクスマップを設定完了")
                else:
                    # 読み込み失敗時はアイテム数表示にフォールバック
                    write_debug_log(f"display_custom_icon: 画像ファイル読み込み失敗")
                    self.display_item_count()
                    return
                    
            # 背景スタイルを設定（アイコン用）
            icon_size = self.icon_label.width()
            border_radius = icon_size // 2
            self.icon_label.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba(255, 255, 255, 200);
                    border-radius: {border_radius}px;
                    border: 2px solid rgba(200, 200, 200, 150);
                }}
            """)
            write_debug_log(f"display_custom_icon: スタイル設定完了")
            
            # テキストをクリア（数字表示を消去）
            self.icon_label.setText("")
            write_debug_log(f"display_custom_icon: テキストをクリア")
            
            # 強制的に更新を実行
            self.icon_label.update()
            self.update()
            write_debug_log(f"display_custom_icon: 更新処理完了")
        except Exception as e:
            from ui.icon_selector_dialog import write_debug_log
            write_debug_log(f"display_custom_icon: エラー = {e}")
            self.display_item_count()
            
    def create_circular_pixmap(self, source_pixmap, size):
        """ピクスマップを円形にマスクする"""
        from ui.icon_selector_dialog import write_debug_log
        
        write_debug_log(f"create_circular_pixmap: source_pixmap.isNull() = {source_pixmap.isNull()}")
        write_debug_log(f"create_circular_pixmap: size = {size}")
        write_debug_log(f"create_circular_pixmap: source_pixmap size = {source_pixmap.width()}x{source_pixmap.height()}")
        
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
        write_debug_log(f"create_circular_pixmap: 描画位置 = ({x}, {y})")
        painter.drawPixmap(x, y, source_pixmap)
        
        painter.end()
        
        write_debug_log(f"create_circular_pixmap: 完成したピクスマップ.isNull() = {circular_pixmap.isNull()}")
        return circular_pixmap
            
    def display_item_count(self):
        """アイテム数を表示（カスタムアイコンがない場合のみ）"""
        # カスタムアイコンがある場合は何もしない
        if self.custom_icon_path:
            from ui.icon_selector_dialog import write_debug_log
            write_debug_log(f"display_item_count: カスタムアイコンがあるため処理をスキップ")
            return
            
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
            self.is_dragging = False  # ドラッグフラグをリセット
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())
            
    def mouseMoveEvent(self, event):
        """マウス移動イベント（ドラッグ処理）"""
        if (event.buttons() & Qt.MouseButton.LeftButton and 
            self.drag_start_position is not None):
            
            # ドラッグ距離をチェック
            distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
            if distance >= QApplication.startDragDistance():
                self.is_dragging = True  # ドラッグ開始をマーク
                # ウィンドウを移動
                new_position = self.mapToGlobal(event.position().toPoint() - self.drag_start_position)
                self.move(new_position)
                
                # リストウィンドウが表示されている場合は一緒に移動
                self.update_list_position()
                
    def mouseReleaseEvent(self, event):
        """マウスリリースイベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drag_start_position is not None:
                if not self.is_dragging:
                    # ドラッグしていない場合のみクリックとして処理
                    # ダブルクリック検出
                    current_time = time.time()
                    if current_time - self.last_click_time < 0.3:  # 300ms以内ならダブルクリック
                        self.double_clicked.emit(self)
                    else:
                        # シングルクリックとして処理
                        self.clicked.emit(self)
                    
                    self.last_click_time = current_time
                else:
                    # ドラッグ終了として処理 - clickedシグナルは発生させない
                    self.position_changed.emit()
                    
                # フラグをリセット
                self.drag_start_position = None
                self.is_dragging = False
                
    def show_context_menu(self, position):
        """コンテキストメニューを表示"""
        menu = QMenu(self)
        
        # 新しいグループを作成
        new_group_action = QAction("新しいグループを作成", self)
        new_group_action.triggered.connect(self.create_new_group)
        menu.addAction(new_group_action)
        
        menu.addSeparator()
        
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
        
    def create_new_group(self):
        """新しいグループを作成"""
        if self.main_app:
            self.main_app.create_new_group()
        else:
            QMessageBox.warning(
                self, "エラー", 
                "新しいグループを作成できません。\nメインアプリケーションとの接続に問題があります。"
            )
        
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
        from ui.icon_selector_dialog import IconSelectorDialog, get_relative_icon_path
        
        dialog = IconSelectorDialog(self, self.custom_icon_path)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_icon = dialog.get_selected_icon()
            # 相対パスで保存
            self.custom_icon_path = get_relative_icon_path(selected_icon) if selected_icon else None
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
            # メインアプリケーションにグループ削除を通知
            if self.main_app:
                try:
                    self.main_app.remove_group(self)
                except Exception as e:
                    print(f"グループ削除通知エラー: {e}")
            
            # リストウィンドウがある場合は閉じる
            if hasattr(self, 'list_window') and self.list_window:
                try:
                    self.list_window.close()
                    self.list_window.deleteLater()
                except Exception as e:
                    print(f"リストウィンドウ削除エラー: {e}")
            
            # 自身を削除
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
            'original_path': file_path,  # 元のパス（ショートカットの場合のため）
            'checked': True  # デフォルトでチェック状態
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
            
            # テキストラベルの横幅をアイコンラベルと合わせる
            self.text_label.setFixedWidth(icon_label_size)
            # テキストラベルの高さをテキストサイズに合わせて固定
            self.text_label.setFixedHeight(18)
            
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
    
    def update_list_position(self):
        """リストウィンドウの位置を更新"""
        if self.list_window and self.list_window.isVisible():
            icon_pos = self.pos()
            icon_size = self.size()
            list_size = self.list_window.size()
            
            # 画面サイズを取得
            try:
                from PyQt6.QtWidgets import QApplication
                screen = QApplication.primaryScreen()
                screen_geometry = screen.availableGeometry()
                screen_width = screen_geometry.width()
                screen_x = screen_geometry.x()
            except Exception as e:
                print(f"画面サイズ取得エラー: {e}")
                # フォールバック値
                screen_width = 1920
                screen_x = 0
            
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
                list_x = int(icon_pos.x() - list_size.width() - target_gap)
                print(f"リストを左側に配置: アイコン中心={icon_center_x}, 画面中心={screen_center_x}")
            else:
                # アイコンが画面左半分にある場合：右側にリストを配置
                list_x = int(icon_pos.x() + icon_size.width() + target_gap)
                print(f"リストを右側に配置: アイコン中心={icon_center_x}, 画面中心={screen_center_x}")
            
            # 垂直位置の調整（初期表示時と同じロジック）
            default_y = icon_pos.y()
            screen_height = screen_geometry.height()
            screen_y = screen_geometry.y()
            list_height = list_size.height()
            
            # リストが画面下部を超える場合は上側に配置
            if default_y + list_height > screen_y + screen_height:
                list_y = icon_pos.y() + icon_size.height() - list_height
                # 上側にもはみ出る場合は画面内に収まる位置に調整
                if list_y < screen_y:
                    list_y = max(screen_y, icon_pos.y() + icon_size.height() // 2 - list_height // 2)
                print(f"リストを上側に配置: Y={list_y} (画面下部超過)")
            else:
                list_y = default_y
                print(f"リストを通常位置に配置: Y={list_y}")
            
            # 最終的に画面境界内に収める
            final_x = max(screen_x, min(list_x, screen_x + screen_width - list_size.width()))
            final_y = max(screen_y, min(list_y, screen_y + screen_height - list_height))
            
            self.list_window.move(final_x, final_y)