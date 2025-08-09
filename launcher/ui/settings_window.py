"""
SettingsWindow - システム設定ウィンドウ
"""

import os
import winreg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QGroupBox, QCheckBox, QSpinBox, QSlider, QLabel,
                            QPushButton, QComboBox, QLineEdit,
                            QFileDialog, QMessageBox, QFormLayout, QSpacerItem,
                            QSizePolicy, QFrame, QScrollArea,
                            QTextEdit, QDialogButtonBox, QKeySequenceEdit, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QStandardPaths, QTimer
from PyQt6.QtGui import QFont, QPalette, QKeySequence
from data.settings_manager import SettingsManager


class ExportConfirmDialog(QDialog):
    """エクスポート確認ダイアログ"""
    
    def __init__(self, default_filename, parent=None):
        super().__init__(parent)
        self.default_filename = default_filename
        self.setup_ui()
        
    def setup_ui(self):
        """UI設定"""
        self.setWindowTitle("設定をエクスポート")
        self.setModal(True)
        self.resize(400, 150)
        
        layout = QVBoxLayout(self)
        
        # ファイル名入力
        filename_layout = QFormLayout()
        self.filename_edit = QLineEdit(self.default_filename)
        self.filename_edit.selectAll()
        filename_layout.addRow("ファイル名:", self.filename_edit)
        layout.addLayout(filename_layout)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # OKボタンのテキストを変更
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("エクスポート")
        
        # キャンセルボタンのテキストを変更
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("キャンセル")
        
    def get_filename(self):
        """入力されたファイル名を取得"""
        filename = self.filename_edit.text().strip()
        if not filename.endswith('.json'):
            filename += '.json'
        return filename


class HotkeyTab(QWidget):
    """ホットキー設定タブ"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # ホットキー設定
        hotkey_group = QGroupBox("ホットキー設定")
        hotkey_layout = QFormLayout()
        
        # 表示/非表示切り替えホットキー
        self.toggle_hotkey = QKeySequenceEdit()
        self.toggle_hotkey.keySequenceChanged.connect(self.settings_changed.emit)
        
        # 説明ラベル
        help_label = QLabel("アイコンの表示/非表示を切り替えるホットキーを設定します")
        help_label.setStyleSheet("color: #666; font-size: 11px;")
        
        # 最前面表示切り替えホットキー
        self.always_on_top_hotkey = QKeySequenceEdit()
        self.always_on_top_hotkey.keySequenceChanged.connect(self.settings_changed.emit)
        
        # 最前面表示の説明ラベル
        always_on_top_help_label = QLabel("最前面表示のON/OFFを切り替えるホットキーを設定します")
        always_on_top_help_label.setStyleSheet("color: #666; font-size: 11px;")
        
        # デスクトップアイコン切り替えホットキー
        self.desktop_icons_hotkey = QKeySequenceEdit()
        self.desktop_icons_hotkey.keySequenceChanged.connect(self.settings_changed.emit)
        
        # デスクトップアイコンの説明ラベル
        desktop_icons_help_label = QLabel("Windowsデスクトップアイコンの表示/非表示を切り替えるホットキーを設定します")
        desktop_icons_help_label.setStyleSheet("color: #666; font-size: 11px;")
        
        hotkey_layout.addRow("表示/非表示切り替え:", self.toggle_hotkey)
        hotkey_layout.addRow("", help_label)
        hotkey_layout.addRow("最前面表示切り替え:", self.always_on_top_hotkey)
        hotkey_layout.addRow("", always_on_top_help_label)
        hotkey_layout.addRow("デスクトップアイコン切り替え:", self.desktop_icons_hotkey)
        hotkey_layout.addRow("", desktop_icons_help_label)
        
        hotkey_group.setLayout(hotkey_layout)
        
        # 推奨ホットキー
        recommended_group = QGroupBox("推奨ホットキー")
        recommended_layout = QVBoxLayout()
        
        recommended_text = QLabel("""
推奨されるホットキーの組み合わせ：

【表示/非表示切り替え】
• Ctrl+Shift+Z（推奨、デフォルト）
• Ctrl+Alt+L（Launcher）
• Ctrl+Shift+D（Desktop）
• Ctrl+Alt+H（Hide/Show）
• Win+Shift+L

【最前面表示切り替え】
• Ctrl+Shift+A（推奨、デフォルト）
• Ctrl+Alt+T（Top）
• Win+Shift+A

【デスクトップアイコン切り替え】
• Ctrl+Shift+F12（推奨、デフォルト）
• Ctrl+Alt+D（Desktop）
• Win+Shift+D

他のアプリケーションと競合しないキーを選択してください。
        """)
        recommended_text.setStyleSheet("color: #555; font-size: 11px; padding: 10px;")
        recommended_text.setWordWrap(True)
        
        recommended_layout.addWidget(recommended_text)
        recommended_group.setLayout(recommended_layout)
        
        # レイアウト構成
        layout.addWidget(hotkey_group)
        layout.addWidget(recommended_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def load_settings(self):
        """設定を読み込み"""
        settings = self.settings_manager.get_hotkey_settings()
        
        # ホットキー設定
        hotkey_str = settings.get('toggle_visibility', 'Ctrl+Shift+Z')
        self.toggle_hotkey.setKeySequence(QKeySequence(hotkey_str))
        
        # 最前面表示切り替えホットキー設定
        always_on_top_str = settings.get('toggle_always_on_top', 'Ctrl+Shift+A')
        self.always_on_top_hotkey.setKeySequence(QKeySequence(always_on_top_str))
        
        # デスクトップアイコン切り替えホットキー設定
        desktop_icons_str = settings.get('toggle_desktop_icons', 'Ctrl+Shift+F12')
        self.desktop_icons_hotkey.setKeySequence(QKeySequence(desktop_icons_str))
        
    def get_settings(self):
        """現在の設定を取得"""
        return {
            'toggle_visibility': self.toggle_hotkey.keySequence().toString(),
            'toggle_always_on_top': self.always_on_top_hotkey.keySequence().toString(),
            'toggle_desktop_icons': self.desktop_icons_hotkey.keySequence().toString()
        }


class AppearanceTab(QWidget):
    """外観設定タブ"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        # self.current_color を削除（アイコン色機能削除のため）
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # グループアイコン設定
        icon_group = QGroupBox("グループアイコン設定")
        icon_layout = QFormLayout()
        
        # アイコンサイズ
        self.icon_size_spin = QSpinBox()
        self.icon_size_spin.setRange(50, 150)
        self.icon_size_spin.setSuffix(" px")
        self.icon_size_spin.valueChanged.connect(self.settings_changed.emit)
        icon_layout.addRow("アイコンサイズ (50-150px):", self.icon_size_spin)
        
        # 透明度
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        self.opacity_slider.valueChanged.connect(self.settings_changed.emit)
        
        self.opacity_label = QLabel("80%")
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        icon_layout.addRow("透明度:", opacity_layout)
        
        # アイコンフォルダを開くボタン
        self.open_icons_folder_btn = QPushButton("アイコンフォルダを開く")
        self.open_icons_folder_btn.clicked.connect(self.open_icons_folder)
        icon_layout.addRow("アイコン管理:", self.open_icons_folder_btn)
        
        # アイコン色機能を削除（デフォルトアイコンがアプリアイコンになったため）
        
        icon_group.setLayout(icon_layout)
        layout.addWidget(icon_group)
        
        # ウィンドウ設定
        window_group = QGroupBox("ウィンドウ設定")
        window_layout = QFormLayout()
        
        self.always_on_top = QCheckBox("常に最前面に表示")
        self.always_on_top.stateChanged.connect(self.settings_changed.emit)
        window_layout.addRow(self.always_on_top)
        
        self.show_group_names = QCheckBox("グループ名を表示")
        self.show_group_names.stateChanged.connect(self.settings_changed.emit)
        window_layout.addRow(self.show_group_names)
        
        self.show_file_paths = QCheckBox("リスト内でファイルパスを表示")
        self.show_file_paths.stateChanged.connect(self.settings_changed.emit)
        window_layout.addRow(self.show_file_paths)
        
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def update_opacity_label(self, value):
        """透明度ラベルを更新"""
        self.opacity_label.setText(f"{value}%")
        
    def open_icons_folder(self):
        """アイコンフォルダをエクスプローラーで開く"""
        try:
            # icon_selector_dialog.pyからget_icons_directory関数をインポート
            import sys
            import os
            
            # 他のモジュールのパスを追加
            current_dir = os.path.dirname(__file__)
            parent_dir = os.path.dirname(current_dir)
            sys.path.insert(0, parent_dir)
            
            from ui.icon_selector_dialog import ensure_user_icons_directory
            
            # アイコンフォルダのパスを取得（フォルダが存在しない場合は作成）
            icons_dir = ensure_user_icons_directory()
            
            # Windowsエクスプローラーでフォルダを開く
            if os.name == 'nt':  # Windows
                os.startfile(icons_dir)
            else:  # その他のOS（一応対応）
                import subprocess
                if sys.platform.startswith('darwin'):  # macOS
                    subprocess.run(['open', icons_dir])
                else:  # Linux
                    subprocess.run(['xdg-open', icons_dir])
                    
        except Exception as e:
            QMessageBox.critical(
                self, "エラー", 
                f"アイコンフォルダを開けませんでした:\n{str(e)}"
            )
        
    # choose_color メソッドを削除（アイコン色機能削除のため）
            
    def load_settings(self):
        """設定を読み込み"""
        settings = self.settings_manager.get_appearance_settings()
        
        self.icon_size_spin.setValue(settings.get('icon_size', 80))
        self.opacity_slider.setValue(settings.get('opacity', 80))
        self.update_opacity_label(settings.get('opacity', 80))
        
        # アイコン色設定を削除
        
        self.always_on_top.setChecked(settings.get('always_on_top', True))
        self.show_group_names.setChecked(settings.get('show_group_names', True))
        self.show_file_paths.setChecked(settings.get('show_file_paths', True))
        
    def get_settings(self):
        """現在の設定を取得"""
        return {
            'icon_size': self.icon_size_spin.value(),
            'opacity': self.opacity_slider.value(),
            # 'icon_color': アイコン色機能を削除
            'always_on_top': self.always_on_top.isChecked(),
            'show_group_names': self.show_group_names.isChecked(),
            'show_file_paths': self.show_file_paths.isChecked()
        }


class BehaviorTab(QWidget):
    """動作設定タブ"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 起動設定
        startup_group = QGroupBox("起動設定")
        startup_layout = QFormLayout()
        
        self.startup_with_windows = QCheckBox("Windows起動時に自動実行")
        self.startup_with_windows.stateChanged.connect(self.settings_changed.emit)
        startup_layout.addRow(self.startup_with_windows)
        
        self.minimize_to_tray = QCheckBox("起動時にシステムトレイに最小化")
        self.minimize_to_tray.stateChanged.connect(self.settings_changed.emit)
        startup_layout.addRow(self.minimize_to_tray)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # 全て起動設定
        launch_group = QGroupBox("全て起動設定")
        launch_layout = QFormLayout()
        
        # 起動間隔設定
        self.launch_interval_spin = QSpinBox()
        self.launch_interval_spin.setRange(1, 30)
        self.launch_interval_spin.setSuffix(" 秒")
        self.launch_interval_spin.valueChanged.connect(self.settings_changed.emit)
        
        # 説明ラベル
        interval_help_label = QLabel("各アプリケーションの起動間隔を設定します（1〜30秒）")
        interval_help_label.setStyleSheet("color: #666; font-size: 11px;")
        
        launch_layout.addRow("起動間隔:", self.launch_interval_spin)
        launch_layout.addRow("", interval_help_label)
        
        launch_group.setLayout(launch_layout)
        layout.addWidget(launch_group)
        
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_settings(self):
        """設定を読み込み"""
        settings = self.settings_manager.get_behavior_settings()
        
        self.startup_with_windows.setChecked(settings.get('startup_with_windows', False))
        self.minimize_to_tray.setChecked(settings.get('minimize_to_tray', True))
        self.launch_interval_spin.setValue(settings.get('launch_interval', 3))
        
    def get_settings(self):
        """現在の設定を取得"""
        return {
            'startup_with_windows': self.startup_with_windows.isChecked(),
            'minimize_to_tray': self.minimize_to_tray.isChecked(),
            'launch_interval': self.launch_interval_spin.value()
        }


class AdvancedTab(QWidget):
    """高度な設定タブ"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 設定管理
        settings_group = QGroupBox("設定管理")
        settings_layout = QVBoxLayout()
        
        # エクスポート・インポートボタン
        export_import_layout = QHBoxLayout()
        
        export_btn = QPushButton("エクスポート")
        export_btn.clicked.connect(self.export_settings)
        export_import_layout.addWidget(export_btn)
        
        import_btn = QPushButton("インポート")
        import_btn.clicked.connect(self.import_settings)
        export_import_layout.addWidget(import_btn)
        
        settings_layout.addLayout(export_import_layout)
        
        # 設定管理の説明
        settings_help_label = QLabel("アプリケーションの全データ（設定値+グループ+アイテム）を\nファイルに保存・復元します。")
        settings_help_label.setStyleSheet("color: #666; font-size: 11px; margin: 5px 0px;")
        settings_help_label.setWordWrap(True)
        
        settings_layout.addWidget(settings_help_label)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 自動バックアップ
        backup_group = QGroupBox("自動バックアップ")
        backup_layout = QVBoxLayout()
        
        # 最大バックアップ数設定
        backup_settings_layout = QFormLayout()
        
        self.max_backups = QSpinBox()
        self.max_backups.setRange(1, 50)
        self.max_backups.valueChanged.connect(self.settings_changed.emit)
        backup_settings_layout.addRow("最大バックアップ数:", self.max_backups)
        
        backup_layout.addLayout(backup_settings_layout)
        
        # 設定リセットボタン
        reset_layout = QHBoxLayout()
        
        reset_btn = QPushButton("設定をリセット")
        reset_btn.clicked.connect(self.reset_settings)
        reset_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        reset_layout.addWidget(reset_btn)
        reset_layout.addStretch()
        
        backup_layout.addLayout(reset_layout)
        
        # 自動バックアップの説明
        backup_help_label = QLabel("設定変更時に自動作成される設定ファイルのバックアップ保持数と、\n設定値のリセットを管理します。グループ・アイテムには影響しません。")
        backup_help_label.setStyleSheet("color: #666; font-size: 11px; margin: 5px 0px;")
        backup_help_label.setWordWrap(True)
        
        backup_layout.addWidget(backup_help_label)
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_settings(self):
        """設定を読み込み"""
        settings = self.settings_manager.get_advanced_settings()
        
        self.max_backups.setValue(settings.get('max_backups', 10))
        
    def get_settings(self):
        """現在の設定を取得"""
        return {
            'max_backups': self.max_backups.value()
        }
        
    def export_settings(self):
        """設定をエクスポート"""
        default_filename = self.settings_manager.get_default_export_filename()
        dialog = ExportConfirmDialog(default_filename, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            filename = dialog.get_filename()
            exported_path = self.settings_manager.export_all_settings(filename=filename)
            if exported_path:
                QMessageBox.information(
                    self, "成功", 
                    f"設定がエクスポートされました。\n保存先: {exported_path}"
                )
            else:
                QMessageBox.critical(self, "エラー", "設定のエクスポートに失敗しました。")
                
    def import_settings(self):
        """設定をインポート"""
        # エクスポートフォルダを初期ディレクトリとして設定
        export_dir = self.settings_manager.get_export_dir()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "設定をインポート", export_dir,
            "JSON Files (*.json)"
        )
        if file_path:
            reply = QMessageBox.question(
                self, "確認", 
                "現在の設定が上書きされます。続行しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if self.settings_manager.import_all_settings(file_path):
                    restart_reply = QMessageBox.question(
                        self, "再起動", 
                        "設定がインポートされました。\n変更を反映するためにアプリケーションを再起動しますか？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    if restart_reply == QMessageBox.StandardButton.Yes:
                        # メインアプリケーションの再起動機能を呼び出し
                        self._request_application_restart()
                    else:
                        QMessageBox.information(self, "完了", "設定がインポートされました。\n手動でアプリケーションを再起動してください。")
                else:
                    QMessageBox.critical(self, "エラー", "設定のインポートに失敗しました。")
                    
    def reset_settings(self):
        """設定をリセット"""
        reply = QMessageBox.question(
            self, "確認", 
            "すべての設定がデフォルト値にリセットされます。\nこの操作は元に戻せません。続行しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.settings_manager.reset_all_settings():
                restart_reply = QMessageBox.question(
                    self, "再起動", 
                    "設定がリセットされました。\n変更を反映するためにアプリケーションを再起動しますか？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if restart_reply == QMessageBox.StandardButton.Yes:
                    # メインアプリケーションの再起動機能を呼び出し
                    self._request_application_restart()
                else:
                    QMessageBox.information(self, "完了", "設定がリセットされました。\n手動でアプリケーションを再起動してください。")
            else:
                QMessageBox.critical(self, "エラー", "設定のリセットに失敗しました。")
                
    def _request_application_restart(self):
        """メインアプリケーションに再起動を要求（共通メソッド）"""
        try:
            # QApplicationインスタンスからメインアプリを取得
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if hasattr(app, 'restart_application'):
                # 設定ウィンドウを閉じてから再起動
                # 親ウィジェットを辿ってSettingsWindowを見つける
                settings_window = self
                while settings_window.parent():
                    settings_window = settings_window.parent()
                    if hasattr(settings_window, 'close'):
                        break
                        
                if hasattr(settings_window, 'close'):
                    settings_window.close()
                    
                # 少し待機してから再起動（ウィンドウクローズの完了を待つ）
                QTimer.singleShot(200, app.restart_application)
            else:
                QMessageBox.warning(self, "エラー", "再起動機能が見つかりません。\n手動でアプリケーションを再起動してください。")
        except Exception as e:
            print(f"再起動要求エラー: {e}")
            QMessageBox.critical(self, "エラー", f"再起動要求中にエラーが発生しました:\n{str(e)}")


class SettingsWindow(QWidget):
    """設定ウィンドウ"""
    
    settings_applied = pyqtSignal(dict)
    
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.setup_ui()
        self.setup_window()
        
    def setup_window(self):
        """ウィンドウ設定"""
        self.setWindowTitle("iconLaunch 設定")
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        
        # アプリケーションアイコンを設定
        self.load_and_set_app_icon()
        
    def setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 各タブを作成
        self.appearance_tab = AppearanceTab(self.settings_manager)
        self.behavior_tab = BehaviorTab(self.settings_manager)
        self.hotkey_tab = HotkeyTab(self.settings_manager)
        self.advanced_tab = AdvancedTab(self.settings_manager)
        
        # タブを追加
        self.tab_widget.addTab(self.appearance_tab, "外観")
        self.tab_widget.addTab(self.behavior_tab, "動作")
        self.tab_widget.addTab(self.hotkey_tab, "ホットキー")
        self.tab_widget.addTab(self.advanced_tab, "高度な設定")
        
        layout.addWidget(self.tab_widget)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        # プロファイル管理ボタンを左側に配置
        self.profile_btn = QPushButton("プロファイル管理")
        self.profile_btn.clicked.connect(self.show_profile_manager)
        button_layout.addWidget(self.profile_btn)
        
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("適用")
        self.apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("キャンセル")
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 変更検知
        self.appearance_tab.settings_changed.connect(self.on_settings_changed)
        self.behavior_tab.settings_changed.connect(self.on_settings_changed)
        self.advanced_tab.settings_changed.connect(self.on_settings_changed)
        
        self.changes_pending = False
        
    def on_settings_changed(self):
        """設定変更時"""
        self.changes_pending = True
        self.apply_btn.setEnabled(True)
        
    def apply_settings(self):
        """設定を適用"""
        try:
            # 各タブから設定を取得
            appearance_settings = self.appearance_tab.get_settings()
            behavior_settings = self.behavior_tab.get_settings()
            hotkey_settings = self.hotkey_tab.get_settings()
            advanced_settings = self.advanced_tab.get_settings()
            
            # 設定を保存
            self.settings_manager.save_appearance_settings(appearance_settings)
            self.settings_manager.save_behavior_settings(behavior_settings)
            self.settings_manager.save_hotkey_settings(hotkey_settings)
            self.settings_manager.save_advanced_settings(advanced_settings)
            
            # 全設定をまとめて通知
            all_settings = {
                'appearance': appearance_settings,
                'behavior': behavior_settings,
                'hotkey': hotkey_settings,
                'advanced': advanced_settings
            }
            
            self.settings_applied.emit(all_settings)
            
            self.changes_pending = False
            self.apply_btn.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"設定の適用に失敗しました:\n{str(e)}")
            
    def accept_settings(self):
        """設定を適用して閉じる"""
        if self.changes_pending:
            self.apply_settings()
        self.close()
        
    def closeEvent(self, event):
        """ウィンドウクローズ時"""
        if self.changes_pending:
            reply = QMessageBox.question(
                self, "確認", 
                "未保存の変更があります。保存しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.apply_settings()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
            
    def load_and_set_app_icon(self):
        """アプリケーションアイコンを読み込んで設定"""
        try:
            import os
            # 設定ウィンドウのファイルパスから2階層上がプロジェクトルート
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            icon_path = os.path.join(project_root, "app_icon.ico")
            
            if os.path.exists(icon_path):
                from PyQt6.QtGui import QIcon
                icon = QIcon(icon_path)
                if not icon.isNull():
                    self.setWindowIcon(icon)
                    print(f"設定ウィンドウアイコン設定完了: {icon_path}")
        except Exception as e:
            print(f"設定ウィンドウアイコン設定エラー: {e}")
            
    def request_application_restart(self):
        """メインアプリケーションに再起動を要求"""
        try:
            # QApplicationインスタンスからメインアプリを取得
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if hasattr(app, 'restart_application'):
                # 設定ウィンドウを閉じてから再起動
                self.close()
                # 少し待機してから再起動（ウィンドウクローズの完了を待つ）
                QTimer.singleShot(200, app.restart_application)
            else:
                QMessageBox.warning(self, "エラー", "再起動機能が見つかりません。\n手動でアプリケーションを再起動してください。")
        except Exception as e:
            print(f"再起動要求エラー: {e}")
            QMessageBox.critical(self, "エラー", f"再起動要求中にエラーが発生しました:\n{str(e)}")
            
    def show_profile_manager(self):
        """プロファイル管理ウィンドウを表示"""
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if hasattr(app, 'show_profile_manager'):
                app.show_profile_manager()
            else:
                QMessageBox.warning(self, "エラー", "プロファイル管理機能が見つかりません。")
        except Exception as e:
            print(f"プロファイル管理ウィンドウ表示エラー: {e}")
            QMessageBox.critical(self, "エラー", f"プロファイル管理ウィンドウの表示中にエラーが発生しました:\n{str(e)}")