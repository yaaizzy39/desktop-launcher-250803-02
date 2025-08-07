"""
HotkeySelector - ホットキー選択ダイアログ
ユーザーがプロファイルに割り当てるホットキーを選択できるUI
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QGroupBox, QMessageBox, QCheckBox,
                            QDialogButtonBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class HotkeySelector(QDialog):
    """ホットキー選択ダイアログ"""
    
    def __init__(self, parent=None, used_hotkeys=None, current_hotkey=None):
        super().__init__(parent)
        self.used_hotkeys = used_hotkeys or {}  # {hotkey_string: profile_name}
        self.current_hotkey = current_hotkey
        self.selected_hotkey = None
        
        self.setWindowTitle("ホットキー選択")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        self.setup_ui()
        
    def setup_ui(self):
        """UIを設定"""
        layout = QVBoxLayout()
        
        # 説明ラベル
        info_label = QLabel("このプロファイルに割り当てるホットキーを選択してください。")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # ホットキー選択グループ
        hotkey_group = QGroupBox("ホットキー設定")
        hotkey_layout = QVBoxLayout(hotkey_group)
        
        # 有効/無効チェックボックス
        self.enable_hotkey = QCheckBox("ホットキーを設定する")
        self.enable_hotkey.stateChanged.connect(self.on_enable_changed)
        hotkey_layout.addWidget(self.enable_hotkey)
        
        # ホットキー選択部分
        self.hotkey_widget = self.create_hotkey_widget()
        hotkey_layout.addWidget(self.hotkey_widget)
        
        layout.addWidget(hotkey_group)
        
        # 使用中ホットキー表示
        if self.used_hotkeys:
            used_group = QGroupBox("現在使用中のホットキー")
            used_layout = QVBoxLayout(used_group)
            
            used_text = ""
            for hotkey, profile in self.used_hotkeys.items():
                if hotkey != self.current_hotkey:  # 現在編集中のプロファイルは除外
                    used_text += f"{hotkey}: {profile}\\n"
            
            if used_text:
                used_label = QLabel(used_text.strip())
                used_label.setStyleSheet("color: #666; font-size: 9px;")
                used_layout.addWidget(used_label)
            else:
                used_label = QLabel("なし")
                used_label.setStyleSheet("color: #666; font-size: 9px;")
                used_layout.addWidget(used_label)
                
            layout.addWidget(used_group)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_selection)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # 初期状態を設定
        if self.current_hotkey:
            self.enable_hotkey.setChecked(True)
            self.set_current_hotkey(self.current_hotkey)
        else:
            self.enable_hotkey.setChecked(True)  # デフォルトで有効に
            
        # 初期状態に応じてUI制御
        self.on_enable_changed(self.enable_hotkey.checkState())
            
    def create_hotkey_widget(self):
        """ホットキー選択ウィジェットを作成"""
        widget = QGroupBox()
        layout = QVBoxLayout(widget)
        
        # 修飾キー選択
        modifier_layout = QHBoxLayout()
        modifier_layout.addWidget(QLabel("修飾キー:"))
        
        self.modifier_combo = QComboBox()
        self.modifier_combo.addItems([
            "Ctrl+Shift",
            "Ctrl+Alt", 
            "Alt+Shift",
            "Win+Shift",
            "Ctrl",
            "Alt",
            "Shift"
        ])
        modifier_layout.addWidget(self.modifier_combo)
        modifier_layout.addStretch()
        layout.addLayout(modifier_layout)
        
        # ファンクションキー選択
        fkey_layout = QHBoxLayout()
        fkey_layout.addWidget(QLabel("ファンクションキー:"))
        
        self.fkey_combo = QComboBox()
        f_keys = [f"F{i}" for i in range(1, 13)]
        self.fkey_combo.addItems(f_keys)
        fkey_layout.addWidget(self.fkey_combo)
        fkey_layout.addStretch()
        layout.addLayout(fkey_layout)
        
        # プレビュー
        self.preview_label = QLabel("ホットキー: Ctrl+Shift+F1")
        self.preview_label.setFont(QFont("", 10, QFont.Weight.Bold))
        self.preview_label.setStyleSheet("color: #0066cc; padding: 5px; border: 1px solid #ccc; background: #f9f9f9;")
        layout.addWidget(self.preview_label)
        
        # イベント接続
        self.modifier_combo.currentTextChanged.connect(self.update_preview)
        self.fkey_combo.currentTextChanged.connect(self.update_preview)
        
        self.update_preview()
        return widget
        
    def on_enable_changed(self, state):
        """ホットキー有効/無効切り替え"""
        enabled = state == Qt.CheckState.Checked
        if hasattr(self, 'modifier_combo'):
            self.modifier_combo.setEnabled(enabled)
        if hasattr(self, 'fkey_combo'):
            self.fkey_combo.setEnabled(enabled)
        if hasattr(self, 'preview_label'):
            self.preview_label.setEnabled(enabled)
        
    def update_preview(self):
        """プレビューを更新"""
        if not hasattr(self, 'modifier_combo') or not hasattr(self, 'fkey_combo'):
            return
            
        modifier = self.modifier_combo.currentText()
        fkey = self.fkey_combo.currentText()
        hotkey = f"{modifier}+{fkey}"
        
        self.preview_label.setText(f"ホットキー: {hotkey}")
        
        # 競合チェック
        if hotkey in self.used_hotkeys and hotkey != self.current_hotkey:
            self.preview_label.setStyleSheet("color: #cc0000; padding: 5px; border: 1px solid #cc0000; background: #ffe6e6;")
            self.preview_label.setText(f"ホットキー: {hotkey} (競合: {self.used_hotkeys[hotkey]})")
        else:
            self.preview_label.setStyleSheet("color: #0066cc; padding: 5px; border: 1px solid #ccc; background: #f9f9f9;")
            self.preview_label.setText(f"ホットキー: {hotkey}")
            
    def set_current_hotkey(self, hotkey_string):
        """現在のホットキーを設定"""
        try:
            parts = hotkey_string.split('+')
            if len(parts) < 2:
                return
                
            fkey = parts[-1]  # 最後がファンクションキー
            modifier = '+'.join(parts[:-1])  # それ以外が修飾キー
            
            # 修飾キーを設定
            modifier_index = self.modifier_combo.findText(modifier)
            if modifier_index >= 0:
                self.modifier_combo.setCurrentIndex(modifier_index)
                
            # ファンクションキーを設定
            fkey_index = self.fkey_combo.findText(fkey)
            if fkey_index >= 0:
                self.fkey_combo.setCurrentIndex(fkey_index)
                
        except Exception as e:
            print(f"ホットキー設定エラー: {e}")
            
    def accept_selection(self):
        """選択を確定"""
        if not self.enable_hotkey.isChecked():
            # ホットキーなし
            self.selected_hotkey = None
            self.accept()
            return
            
        modifier = self.modifier_combo.currentText()
        fkey = self.fkey_combo.currentText()
        hotkey = f"{modifier}+{fkey}"
        
        # 競合チェック
        if hotkey in self.used_hotkeys and hotkey != self.current_hotkey:
            QMessageBox.warning(
                self,
                "ホットキー競合",
                f"ホットキー '{hotkey}' は既にプロファイル '{self.used_hotkeys[hotkey]}' で使用されています。\\n"
                "別のホットキーを選択してください。"
            )
            return
            
        # ホットキー情報を作成
        self.selected_hotkey = {
            'hotkey_string': hotkey,
            'modifier': modifier,
            'fkey': fkey
        }
        
        self.accept()
        
    def get_selected_hotkey(self):
        """選択されたホットキー情報を取得"""
        return self.selected_hotkey