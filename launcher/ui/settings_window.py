"""
SettingsWindow - システム設定ウィンドウ
"""

import os
import winreg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QGroupBox, QCheckBox, QSpinBox, QSlider, QLabel,
                            QPushButton, QColorDialog, QComboBox, QLineEdit,
                            QFileDialog, QMessageBox, QFormLayout, QSpacerItem,
                            QSizePolicy, QFrame, QScrollArea,
                            QTextEdit, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QStandardPaths
from PyQt6.QtGui import QFont, QColor, QPalette
from data.settings_manager import SettingsManager


class AppearanceTab(QWidget):
    """外観設定タブ"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.current_color = '#6496ff'  # デフォルト色を保存
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
        
        # ウィンドウ設定
        window_group = QGroupBox("ウィンドウ設定")
        window_layout = QFormLayout()
        
        self.always_on_top = QCheckBox("常に最前面に表示")
        self.always_on_top.stateChanged.connect(self.settings_changed.emit)
        window_layout.addRow(self.always_on_top)
        
        self.show_group_names = QCheckBox("グループ名を表示")
        self.show_group_names.stateChanged.connect(self.settings_changed.emit)
        window_layout.addRow(self.show_group_names)
        
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def update_opacity_label(self, value):
        """透明度ラベルを更新"""
        self.opacity_label.setText(f"{value}%")
        
    def choose_color(self):
        """色選択ダイアログ"""
        current_color = QColor(self.current_color)
        color = QColorDialog.getColor(current_color, self)
        if color.isValid():
            self.current_color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.current_color}; border: 1px solid #ccc;")
            self.settings_changed.emit()
            
    def load_settings(self):
        """設定を読み込み"""
        settings = self.settings_manager.get_appearance_settings()
        
        self.icon_size_spin.setValue(settings.get('icon_size', 80))
        self.opacity_slider.setValue(settings.get('opacity', 80))
        self.update_opacity_label(settings.get('opacity', 80))
        
        self.current_color = settings.get('icon_color', '#6496ff')
        self.color_preview.setStyleSheet(f"background-color: {self.current_color}; border: 1px solid #ccc;")
        
        self.always_on_top.setChecked(settings.get('always_on_top', True))
        self.show_group_names.setChecked(settings.get('show_group_names', True))
        
    def get_settings(self):
        """現在の設定を取得"""
        return {
            'icon_size': self.icon_size_spin.value(),
            'opacity': self.opacity_slider.value(),
            'icon_color': self.current_color,
            'always_on_top': self.always_on_top.isChecked(),
            'show_group_names': self.show_group_names.isChecked()
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
        
        
        layout.addStretch()
        self.setLayout(layout)
        
    def load_settings(self):
        """設定を読み込み"""
        settings = self.settings_manager.get_behavior_settings()
        
        self.startup_with_windows.setChecked(settings.get('startup_with_windows', False))
        self.minimize_to_tray.setChecked(settings.get('minimize_to_tray', True))
        
    def get_settings(self):
        """現在の設定を取得"""
        return {
            'startup_with_windows': self.startup_with_windows.isChecked(),
            'minimize_to_tray': self.minimize_to_tray.isChecked()
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