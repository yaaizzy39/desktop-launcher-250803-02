"""
SettingsWindow - システム設定ウィンドウ
"""

import os
import winreg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QGroupBox, QCheckBox, QSpinBox, QSlider, QLabel,
                            QPushButton, QColorDialog, QComboBox, QLineEdit,
                            QFileDialog, QMessageBox, QFormLayout, QSpacerItem,
                            QSizePolicy, QFrame, QScrollArea, QKeySequenceEdit,
                            QTextEdit, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QStandardPaths
from PyQt6.QtGui import QFont, QColor, QPalette, QKeySequence
from data.settings_manager import SettingsManager


class AppearanceTab(QWidget):
    """外観設定タブ"""
    
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
        
        # グループアイコン設定
        icon_group = QGroupBox("グループアイコン設定")
        icon_layout = QFormLayout()
        
        # アイコンサイズ
        self.icon_size_spin = QSpinBox()
        self.icon_size_spin.setRange(50, 150)
        self.icon_size_spin.setSuffix(" px")
        self.icon_size_spin.valueChanged.connect(self.settings_changed.emit)
        icon_layout.addRow("アイコンサイズ:", self.icon_size_spin)
        
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
        
        # アイコン色
        self.color_button = QPushButton("色を選択")
        self.color_button.clicked.connect(self.choose_color)
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet("background-color: #6496ff; border: 1px solid #ccc;")
        
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        icon_layout.addRow("アイコン色:", color_layout)
        
        icon_group.setLayout(icon_layout)
        layout.addWidget(icon_group)
        
        # アニメーション設定
        animation_group = QGroupBox("アニメーション設定")
        animation_layout = QFormLayout()
        
        self.enable_animations = QCheckBox("アニメーションを有効にする")
        self.enable_animations.stateChanged.connect(self.settings_changed.emit)
        animation_layout.addRow(self.enable_animations)
        
        self.animation_speed = QSlider(Qt.Orientation.Horizontal)
        self.animation_speed.setRange(1, 10)
        self.animation_speed.valueChanged.connect(self.settings_changed.emit)
        animation_layout.addRow("アニメーション速度:", self.animation_speed)
        
        animation_group.setLayout(animation_layout)
        layout.addWidget(animation_group)
        
        # ウィンドウ設定
        window_group = QGroupBox("ウィンドウ設定")
        window_layout = QFormLayout()
        
        self.always_on_top = QCheckBox("常に最前面に表示")
        self.always_on_top.stateChanged.connect(self.settings_changed.emit)
        window_layout.addRow(self.always_on_top)
        
        self.auto_hide = QCheckBox("自動的に隠す")
        self.auto_hide.stateChanged.connect(self.settings_changed.emit)
        window_layout.addRow(self.auto_hide)
        
        self.hide_delay = QSpinBox()
        self.hide_delay.setRange(1, 10)
        self.hide_delay.setSuffix(" 秒")
        self.hide_delay.valueChanged.connect(self.settings_changed.emit)
        window_layout.addRow("自動非表示時間:", self.hide_delay)
        
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def update_opacity_label(self, value):
        """透明度ラベルを更新"""
        self.opacity_label.setText(f"{value}%")
        
    def choose_color(self):
        """色選択ダイアログ"""
        color = QColorDialog.getColor(QColor("#6496ff"), self)
        if color.isValid():
            self.color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #ccc;")
            self.settings_changed.emit()
            
    def load_settings(self):
        """設定を読み込み"""
        settings = self.settings_manager.get_appearance_settings()
        
        self.icon_size_spin.setValue(settings.get('icon_size', 80))
        self.opacity_slider.setValue(settings.get('opacity', 80))
        self.update_opacity_label(settings.get('opacity', 80))
        
        color = settings.get('icon_color', '#6496ff')
        self.color_preview.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
        
        self.enable_animations.setChecked(settings.get('enable_animations', True))
        self.animation_speed.setValue(settings.get('animation_speed', 5))
        self.always_on_top.setChecked(settings.get('always_on_top', True))
        self.auto_hide.setChecked(settings.get('auto_hide', True))
        self.hide_delay.setValue(settings.get('hide_delay', 3))
        
    def get_settings(self):
        """現在の設定を取得"""
        color_style = self.color_preview.styleSheet()
        color = color_style.split('background-color: ')[1].split(';')[0]
        
        return {
            'icon_size': self.icon_size_spin.value(),
            'opacity': self.opacity_slider.value(),
            'icon_color': color,
            'enable_animations': self.enable_animations.isChecked(),
            'animation_speed': self.animation_speed.value(),
            'always_on_top': self.always_on_top.isChecked(),
            'auto_hide': self.auto_hide.isChecked(),
            'hide_delay': self.hide_delay.value()
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
        
        # ホットキー設定
        hotkey_group = QGroupBox("ホットキー設定")
        hotkey_layout = QFormLayout()
        
        self.enable_hotkey = QCheckBox("グローバルホットキーを有効にする")
        self.enable_hotkey.stateChanged.connect(self.settings_changed.emit)
        hotkey_layout.addRow(self.enable_hotkey)
        
        self.show_hotkey = QKeySequenceEdit()
        self.show_hotkey.keySequenceChanged.connect(self.settings_changed.emit)
        hotkey_layout.addRow("表示/非表示:", self.show_hotkey)
        
        self.new_group_hotkey = QKeySequenceEdit()
        self.new_group_hotkey.keySequenceChanged.connect(self.settings_changed.emit)
        hotkey_layout.addRow("新規グループ作成:", self.new_group_hotkey)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        # ドラッグ&ドロップ設定
        dnd_group = QGroupBox("ドラッグ&ドロップ設定")
        dnd_layout = QFormLayout()
        
        self.confirm_before_add = QCheckBox("アイテム追加前に確認する")
        self.confirm_before_add.stateChanged.connect(self.settings_changed.emit)
        dnd_layout.addRow(self.confirm_before_add)
        
        self.auto_detect_type = QCheckBox("ファイルタイプを自動判別")
        self.auto_detect_type.stateChanged.connect(self.settings_changed.emit)
        dnd_layout.addRow(self.auto_detect_type)
        
        self.max_items_per_group = QSpinBox()
        self.max_items_per_group.setRange(5, 100)
        self.max_items_per_group.valueChanged.connect(self.settings_changed.emit)
        dnd_layout.addRow("グループ当たりの最大アイテム数:", self.max_items_per_group)
        
        dnd_group.setLayout(dnd_layout)
        layout.addWidget(dnd_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_settings(self):
        """設定を読み込み"""
        settings = self.settings_manager.get_behavior_settings()
        
        self.startup_with_windows.setChecked(settings.get('startup_with_windows', False))
        self.minimize_to_tray.setChecked(settings.get('minimize_to_tray', True))
        self.enable_hotkey.setChecked(settings.get('enable_hotkey', False))
        
        show_hotkey = settings.get('show_hotkey', 'Ctrl+Alt+L')
        self.show_hotkey.setKeySequence(QKeySequence(show_hotkey))
        
        new_group_hotkey = settings.get('new_group_hotkey', 'Ctrl+Alt+N')
        self.new_group_hotkey.setKeySequence(QKeySequence(new_group_hotkey))
        
        self.confirm_before_add.setChecked(settings.get('confirm_before_add', False))
        self.auto_detect_type.setChecked(settings.get('auto_detect_type', True))
        self.max_items_per_group.setValue(settings.get('max_items_per_group', 20))
        
    def get_settings(self):
        """現在の設定を取得"""
        return {
            'startup_with_windows': self.startup_with_windows.isChecked(),
            'minimize_to_tray': self.minimize_to_tray.isChecked(),
            'enable_hotkey': self.enable_hotkey.isChecked(),
            'show_hotkey': self.show_hotkey.keySequence().toString(),
            'new_group_hotkey': self.new_group_hotkey.keySequence().toString(),
            'confirm_before_add': self.confirm_before_add.isChecked(),
            'auto_detect_type': self.auto_detect_type.isChecked(),
            'max_items_per_group': self.max_items_per_group.value()
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
        
        # データ管理
        data_group = QGroupBox("データ管理")
        data_layout = QVBoxLayout()
        
        # バックアップ設定
        backup_layout = QFormLayout()
        
        self.auto_backup = QCheckBox("自動バックアップを有効にする")
        self.auto_backup.stateChanged.connect(self.settings_changed.emit)
        backup_layout.addRow(self.auto_backup)
        
        self.backup_interval = QSpinBox()
        self.backup_interval.setRange(1, 24)
        self.backup_interval.setSuffix(" 時間")
        self.backup_interval.valueChanged.connect(self.settings_changed.emit)
        backup_layout.addRow("バックアップ間隔:", self.backup_interval)
        
        self.max_backups = QSpinBox()
        self.max_backups.setRange(1, 50)
        self.max_backups.valueChanged.connect(self.settings_changed.emit)
        backup_layout.addRow("最大バックアップ数:", self.max_backups)
        
        data_layout.addLayout(backup_layout)
        
        # データ操作ボタン
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("設定をエクスポート")
        export_btn.clicked.connect(self.export_settings)
        button_layout.addWidget(export_btn)
        
        import_btn = QPushButton("設定をインポート")
        import_btn.clicked.connect(self.import_settings)
        button_layout.addWidget(import_btn)
        
        reset_btn = QPushButton("設定をリセット")
        reset_btn.clicked.connect(self.reset_settings)
        reset_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        button_layout.addWidget(reset_btn)
        
        data_layout.addLayout(button_layout)
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # パフォーマンス設定
        perf_group = QGroupBox("パフォーマンス設定")
        perf_layout = QFormLayout()
        
        self.low_memory_mode = QCheckBox("省メモリモード")
        self.low_memory_mode.stateChanged.connect(self.settings_changed.emit)
        perf_layout.addRow(self.low_memory_mode)
        
        self.cache_icons = QCheckBox("アイコンをキャッシュする")
        self.cache_icons.stateChanged.connect(self.settings_changed.emit)
        perf_layout.addRow(self.cache_icons)
        
        self.update_check_interval = QSpinBox()
        self.update_check_interval.setRange(0, 30)
        self.update_check_interval.setSuffix(" 日")
        self.update_check_interval.setSpecialValueText("無効")
        self.update_check_interval.valueChanged.connect(self.settings_changed.emit)
        perf_layout.addRow("アップデート確認間隔:", self.update_check_interval)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        # ログ設定
        log_group = QGroupBox("ログ設定")
        log_layout = QFormLayout()
        
        self.enable_logging = QCheckBox("ログを有効にする")
        self.enable_logging.stateChanged.connect(self.settings_changed.emit)
        log_layout.addRow(self.enable_logging)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["エラーのみ", "警告以上", "情報以上", "すべて"])
        self.log_level.currentTextChanged.connect(self.settings_changed.emit)
        log_layout.addRow("ログレベル:", self.log_level)
        
        self.max_log_size = QSpinBox()
        self.max_log_size.setRange(1, 100)
        self.max_log_size.setSuffix(" MB")
        self.max_log_size.valueChanged.connect(self.settings_changed.emit)
        log_layout.addRow("最大ログサイズ:", self.max_log_size)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_settings(self):
        """設定を読み込み"""
        settings = self.settings_manager.get_advanced_settings()
        
        self.auto_backup.setChecked(settings.get('auto_backup', True))
        self.backup_interval.setValue(settings.get('backup_interval', 6))
        self.max_backups.setValue(settings.get('max_backups', 10))
        self.low_memory_mode.setChecked(settings.get('low_memory_mode', False))
        self.cache_icons.setChecked(settings.get('cache_icons', True))
        self.update_check_interval.setValue(settings.get('update_check_interval', 7))
        self.enable_logging.setChecked(settings.get('enable_logging', True))
        
        log_levels = ["エラーのみ", "警告以上", "情報以上", "すべて"]
        log_level = settings.get('log_level', 'info')
        level_map = {'error': 0, 'warning': 1, 'info': 2, 'debug': 3}
        self.log_level.setCurrentIndex(level_map.get(log_level, 2))
        
        self.max_log_size.setValue(settings.get('max_log_size', 10))
        
    def get_settings(self):
        """現在の設定を取得"""
        level_map = {0: 'error', 1: 'warning', 2: 'info', 3: 'debug'}
        
        return {
            'auto_backup': self.auto_backup.isChecked(),
            'backup_interval': self.backup_interval.value(),
            'max_backups': self.max_backups.value(),
            'low_memory_mode': self.low_memory_mode.isChecked(),
            'cache_icons': self.cache_icons.isChecked(),
            'update_check_interval': self.update_check_interval.value(),
            'enable_logging': self.enable_logging.isChecked(),
            'log_level': level_map[self.log_level.currentIndex()],
            'max_log_size': self.max_log_size.value()
        }
        
    def export_settings(self):
        """設定をエクスポート"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "設定をエクスポート", 
            f"launcher_settings_{self.settings_manager.get_timestamp()}.json",
            "JSON Files (*.json)"
        )
        if file_path:
            if self.settings_manager.export_all_settings(file_path):
                QMessageBox.information(self, "成功", "設定がエクスポートされました。")
            else:
                QMessageBox.critical(self, "エラー", "設定のエクスポートに失敗しました。")
                
    def import_settings(self):
        """設定をインポート"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "設定をインポート", "",
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
                    QMessageBox.information(self, "成功", "設定がインポートされました。\nアプリケーションを再起動してください。")
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
                QMessageBox.information(self, "成功", "設定がリセットされました。\nアプリケーションを再起動してください。")
            else:
                QMessageBox.critical(self, "エラー", "設定のリセットに失敗しました。")


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
        self.setWindowTitle("ランチャー設定")
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        
    def setup_ui(self):
        """UI設定"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 各タブを作成
        self.appearance_tab = AppearanceTab(self.settings_manager)
        self.behavior_tab = BehaviorTab(self.settings_manager)
        self.advanced_tab = AdvancedTab(self.settings_manager)
        
        # タブを追加
        self.tab_widget.addTab(self.appearance_tab, "外観")
        self.tab_widget.addTab(self.behavior_tab, "動作")
        self.tab_widget.addTab(self.advanced_tab, "高度な設定")
        
        layout.addWidget(self.tab_widget)
        
        # ボタン
        button_layout = QHBoxLayout()
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
            advanced_settings = self.advanced_tab.get_settings()
            
            # 設定を保存
            self.settings_manager.save_appearance_settings(appearance_settings)
            self.settings_manager.save_behavior_settings(behavior_settings)
            self.settings_manager.save_advanced_settings(advanced_settings)
            
            # 全設定をまとめて通知
            all_settings = {
                'appearance': appearance_settings,
                'behavior': behavior_settings,
                'advanced': advanced_settings
            }
            
            self.settings_applied.emit(all_settings)
            
            self.changes_pending = False
            self.apply_btn.setEnabled(False)
            
            QMessageBox.information(self, "成功", "設定が適用されました。")
            
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