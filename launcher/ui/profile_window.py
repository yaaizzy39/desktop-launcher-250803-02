"""
ProfileWindow - プロファイル管理ウィンドウ
ユーザーがプロファイルの作成・切り替え・管理を行うUI
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QListWidget, QListWidgetItem, QLabel, QLineEdit,
                            QTextEdit, QMessageBox, QInputDialog, QGroupBox,
                            QSplitter, QWidget, QFileDialog, QMenu, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor, QFont, QAction
import os
from datetime import datetime


class ProfileWindow(QDialog):
    """プロファイル管理ウィンドウ"""
    
    # プロファイル切り替えのシグナル
    profile_switched = pyqtSignal(str)  # profile_name
    
    def __init__(self, profile_manager, settings_manager):
        super().__init__()
        self.profile_manager = profile_manager
        self.settings_manager = settings_manager
        
        self.setWindowTitle("プロファイル管理")
        self.setFixedSize(700, 500)
        
        # 現在選択されているプロファイル
        self.selected_profile = None
        
        self.setup_ui()
        self.apply_appearance_settings()
        self.load_profile_list()
        
    def setup_ui(self):
        """UIを設定"""
        layout = QVBoxLayout()
        
        # メインスプリッター
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側: プロファイル一覧
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # プロファイル一覧ラベル
        list_label = QLabel("プロファイル一覧")
        list_label.setFont(QFont("", 10, QFont.Weight.Bold))
        left_layout.addWidget(list_label)
        
        # プロファイルリスト
        self.profile_list = QListWidget()
        self.profile_list.currentItemChanged.connect(self.on_profile_selection_changed)
        self.profile_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.profile_list.customContextMenuRequested.connect(self.show_context_menu)
        left_layout.addWidget(self.profile_list)
        
        # プロファイル操作ボタン
        button_layout = QHBoxLayout()
        
        self.new_button = QPushButton("空のプロファイル作成")
        self.new_button.clicked.connect(self.create_new_profile)
        button_layout.addWidget(self.new_button)
        
        self.switch_button = QPushButton("切り替え")
        self.switch_button.clicked.connect(self.switch_profile)
        self.switch_button.setEnabled(False)
        button_layout.addWidget(self.switch_button)
        
        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_profile)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)
        
        left_layout.addLayout(button_layout)
        
        splitter.addWidget(left_widget)
        
        # 右側: プロファイル詳細
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # プロファイル詳細グループ
        details_group = QGroupBox("プロファイル詳細")
        details_layout = QVBoxLayout(details_group)
        
        # プロファイル名
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名前:"))
        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        name_layout.addWidget(self.name_edit)
        details_layout.addLayout(name_layout)
        
        # 説明
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("説明:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setReadOnly(True)
        desc_layout.addWidget(self.description_edit)
        details_layout.addLayout(desc_layout)
        
        # 作成日時・更新日時
        datetime_layout = QHBoxLayout()
        datetime_left = QVBoxLayout()
        datetime_left.addWidget(QLabel("作成:"))
        self.created_label = QLabel("-")
        self.created_label.setStyleSheet("color: #666;")
        datetime_left.addWidget(self.created_label)
        datetime_layout.addLayout(datetime_left)
        
        datetime_right = QVBoxLayout()
        datetime_right.addWidget(QLabel("更新:"))
        self.updated_label = QLabel("-")
        self.updated_label.setStyleSheet("color: #666;")
        datetime_right.addWidget(self.updated_label)
        datetime_layout.addLayout(datetime_right)
        details_layout.addLayout(datetime_layout)
        
        # グループ数
        groups_layout = QHBoxLayout()
        groups_layout.addWidget(QLabel("グループ数:"))
        self.groups_label = QLabel("-")
        groups_layout.addWidget(self.groups_label)
        groups_layout.addStretch()
        details_layout.addLayout(groups_layout)
        
        right_layout.addWidget(details_group)
        
        # 追加操作ボタン
        extra_button_layout = QVBoxLayout()
        
        self.rename_button = QPushButton("名前変更")
        self.rename_button.clicked.connect(self.rename_profile)
        self.rename_button.setEnabled(False)
        extra_button_layout.addWidget(self.rename_button)
        
        self.save_current_button = QPushButton("現在の状態を保存")
        self.save_current_button.clicked.connect(self.save_current_state)
        extra_button_layout.addWidget(self.save_current_button)
        
        # インポート/エクスポート
        import_export_layout = QHBoxLayout()
        
        self.import_button = QPushButton("インポート")
        self.import_button.clicked.connect(self.import_profile)
        import_export_layout.addWidget(self.import_button)
        
        self.export_button = QPushButton("エクスポート")
        self.export_button.clicked.connect(self.export_profile)
        self.export_button.setEnabled(False)
        import_export_layout.addWidget(self.export_button)
        
        extra_button_layout.addLayout(import_export_layout)
        extra_button_layout.addStretch()
        
        right_layout.addLayout(extra_button_layout)
        
        splitter.addWidget(right_widget)
        
        # スプリッターの比率を設定
        splitter.setSizes([300, 400])
        
        layout.addWidget(splitter)
        
        # 下部: 現在のプロファイル表示
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("現在のプロファイル:"))
        self.current_profile_label = QLabel("なし")
        self.current_profile_label.setFont(QFont("", 9, QFont.Weight.Bold))
        self.current_profile_label.setStyleSheet("color: #0066cc;")
        current_layout.addWidget(self.current_profile_label)
        current_layout.addStretch()
        
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.close)
        current_layout.addWidget(close_button)
        
        layout.addLayout(current_layout)
        
        self.setLayout(layout)
        
    def apply_appearance_settings(self):
        """外観設定を適用"""
        try:
            # アプリケーションアイコンを設定
            app_icon = QApplication.instance().windowIcon()
            if app_icon and not app_icon.isNull():
                self.setWindowIcon(app_icon)
        except Exception as e:
            print(f"プロファイルウィンドウのアイコン設定エラー: {e}")
            
    def load_profile_list(self):
        """プロファイル一覧を読み込み"""
        try:
            self.profile_list.clear()
            profiles = self.profile_manager.get_profile_list()
            
            for profile in profiles:
                item = QListWidgetItem()
                
                # プロファイル名の表示
                name = profile['name']
                if profile['is_current']:
                    name += " (現在使用中)"
                    
                item.setText(name)
                item.setData(Qt.ItemDataRole.UserRole, profile['name'])
                
                # 現在使用中のプロファイルは太字で表示
                if profile['is_current']:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    
                self.profile_list.addItem(item)
                
            # 現在のプロファイル名を更新
            current_name = self.profile_manager.get_current_profile_name()
            self.current_profile_label.setText(current_name if current_name else "なし")
            
        except Exception as e:
            print(f"プロファイル一覧読み込みエラー: {e}")
            QMessageBox.warning(self, "エラー", "プロファイル一覧の読み込みに失敗しました。")
            
    def on_profile_selection_changed(self, current, previous):
        """プロファイル選択変更時の処理"""
        if current:
            profile_name = current.data(Qt.ItemDataRole.UserRole)
            self.selected_profile = profile_name
            
            # プロファイル詳細を表示
            self.show_profile_details(profile_name)
            
            # ボタンの有効/無効を設定
            current_profile = self.profile_manager.get_current_profile_name()
            is_current = profile_name == current_profile
            
            self.switch_button.setEnabled(not is_current)
            self.delete_button.setEnabled(not is_current)
            self.rename_button.setEnabled(True)
            self.export_button.setEnabled(True)
            
        else:
            self.selected_profile = None
            self.clear_profile_details()
            
            # ボタンを無効にする
            self.switch_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.rename_button.setEnabled(False)
            self.export_button.setEnabled(False)
            
    def show_profile_details(self, profile_name):
        """プロファイル詳細を表示"""
        try:
            profile_info = self.profile_manager.get_profile_info(profile_name)
            if profile_info:
                self.name_edit.setText(profile_info.get('name', ''))
                self.description_edit.setText(profile_info.get('description', ''))
                
                # 日時をフォーマット
                created = profile_info.get('created', '')
                if created:
                    created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    self.created_label.setText(created_dt.strftime('%Y/%m/%d %H:%M'))
                else:
                    self.created_label.setText('-')
                    
                updated = profile_info.get('updated', '')
                if updated:
                    updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    self.updated_label.setText(updated_dt.strftime('%Y/%m/%d %H:%M'))
                else:
                    self.updated_label.setText('-')
                    
                # グループ数
                groups_count = profile_info.get('groups_count', 0)
                self.groups_label.setText(f"{groups_count}個")
                
        except Exception as e:
            print(f"プロファイル詳細表示エラー: {e}")
            self.clear_profile_details()
            
    def clear_profile_details(self):
        """プロファイル詳細をクリア"""
        self.name_edit.clear()
        self.description_edit.clear()
        self.created_label.setText('-')
        self.updated_label.setText('-')
        self.groups_label.setText('-')
        
    def create_new_profile(self):
        """新しい空のプロファイルを作成"""
        try:
            name, ok = QInputDialog.getText(
                self, 
                "新しいプロファイルを作成", 
                "プロファイル名を入力してください:",
                text=""
            )
            
            if not ok or not name.strip():
                return
                
            name = name.strip()
            
            # 説明も入力
            description, ok = QInputDialog.getText(
                self,
                "プロファイルの説明",
                "プロファイルの説明を入力してください（省略可）:",
                text=""
            )
            
            if not ok:
                description = ""
            
            # 空のプロファイルを作成（現在の状態ではなく空の状態）
            success, message = self.profile_manager.create_empty_profile(name, description)
            
            if success:
                QMessageBox.information(self, "成功", message)
                self.load_profile_list()
                
                # 新しく作成したプロファイルを選択
                for i in range(self.profile_list.count()):
                    item = self.profile_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == name:
                        self.profile_list.setCurrentItem(item)
                        break
            else:
                QMessageBox.warning(self, "エラー", message)
                
        except Exception as e:
            print(f"プロファイル作成エラー: {e}")
            QMessageBox.critical(self, "エラー", f"プロファイルの作成中にエラーが発生しました:\n{str(e)}")
            
    def switch_profile(self):
        """プロファイルを切り替え"""
        if not self.selected_profile:
            return
            
        try:
            reply = QMessageBox.question(
                self,
                "プロファイル切り替え",
                f"プロファイル '{self.selected_profile}' に切り替えますか？\n"
                "現在の状態は自動的に保存されます。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.profile_manager.switch_to_profile(self.selected_profile)
                
                if success:
                    QMessageBox.information(self, "成功", message)
                    # プロファイル切り替えシグナルを発信
                    self.profile_switched.emit(self.selected_profile)
                    self.load_profile_list()
                else:
                    QMessageBox.warning(self, "エラー", message)
                    
        except Exception as e:
            print(f"プロファイル切り替えエラー: {e}")
            QMessageBox.critical(self, "エラー", f"プロファイルの切り替え中にエラーが発生しました:\n{str(e)}")
            
    def delete_profile(self):
        """プロファイルを削除"""
        if not self.selected_profile:
            return
            
        try:
            reply = QMessageBox.question(
                self,
                "プロファイル削除",
                f"プロファイル '{self.selected_profile}' を削除しますか？\n"
                "この操作は取り消せません。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.profile_manager.delete_profile(self.selected_profile)
                
                if success:
                    QMessageBox.information(self, "成功", message)
                    self.load_profile_list()
                else:
                    QMessageBox.warning(self, "エラー", message)
                    
        except Exception as e:
            print(f"プロファイル削除エラー: {e}")
            QMessageBox.critical(self, "エラー", f"プロファイルの削除中にエラーが発生しました:\n{str(e)}")
            
    def rename_profile(self):
        """プロファイル名を変更"""
        if not self.selected_profile:
            return
            
        try:
            new_name, ok = QInputDialog.getText(
                self,
                "プロファイル名変更",
                f"'{self.selected_profile}' の新しい名前を入力してください:",
                text=self.selected_profile
            )
            
            if not ok or not new_name.strip():
                return
                
            new_name = new_name.strip()
            
            if new_name == self.selected_profile:
                return  # 変更なし
                
            success, message = self.profile_manager.rename_profile(self.selected_profile, new_name)
            
            if success:
                QMessageBox.information(self, "成功", message)
                old_selection = self.selected_profile
                self.load_profile_list()
                
                # 名前変更後のプロファイルを選択
                for i in range(self.profile_list.count()):
                    item = self.profile_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == new_name:
                        self.profile_list.setCurrentItem(item)
                        break
            else:
                QMessageBox.warning(self, "エラー", message)
                
        except Exception as e:
            print(f"プロファイル名変更エラー: {e}")
            QMessageBox.critical(self, "エラー", f"プロファイル名の変更中にエラーが発生しました:\n{str(e)}")
            
    def save_current_state(self):
        """現在の状態を新しいプロファイルとして保存"""
        try:
            name, ok = QInputDialog.getText(
                self, 
                "現在の状態を保存", 
                "保存するプロファイル名を入力してください:",
                text=""
            )
            
            if not ok or not name.strip():
                return
                
            name = name.strip()
            
            # 説明も入力
            description, ok = QInputDialog.getText(
                self,
                "プロファイルの説明",
                "プロファイルの説明を入力してください（省略可）:",
                text=""
            )
            
            if not ok:
                description = ""
            
            # 現在の状態をそのまま保存
            success, message = self.profile_manager.save_profile(name, description)
            
            if success:
                QMessageBox.information(self, "成功", f"現在の状態を '{name}' として保存しました")
                self.load_profile_list()
                
                # 新しく保存したプロファイルを選択
                for i in range(self.profile_list.count()):
                    item = self.profile_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == name:
                        self.profile_list.setCurrentItem(item)
                        break
            else:
                QMessageBox.warning(self, "エラー", message)
                
        except Exception as e:
            print(f"現在状態保存エラー: {e}")
            QMessageBox.critical(self, "エラー", f"現在の状態の保存中にエラーが発生しました:\n{str(e)}")
        
    def import_profile(self):
        """プロファイルをインポート"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "プロファイルをインポート",
                "",
                "JSON files (*.json);;All files (*.*)"
            )
            
            if not file_path:
                return
                
            success, message = self.profile_manager.import_profile(file_path)
            
            if success:
                QMessageBox.information(self, "成功", message)
                self.load_profile_list()
            else:
                QMessageBox.warning(self, "エラー", message)
                
        except Exception as e:
            print(f"プロファイルインポートエラー: {e}")
            QMessageBox.critical(self, "エラー", f"プロファイルのインポート中にエラーが発生しました:\n{str(e)}")
            
    def export_profile(self):
        """プロファイルをエクスポート"""
        if not self.selected_profile:
            return
            
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "プロファイルをエクスポート",
                f"{self.selected_profile}_profile.json",
                "JSON files (*.json);;All files (*.*)"
            )
            
            if not file_path:
                return
                
            success, message = self.profile_manager.export_profile(self.selected_profile, file_path)
            
            if success:
                QMessageBox.information(self, "成功", message)
            else:
                QMessageBox.warning(self, "エラー", message)
                
        except Exception as e:
            print(f"プロファイルエクスポートエラー: {e}")
            QMessageBox.critical(self, "エラー", f"プロファイルのエクスポート中にエラーが発生しました:\n{str(e)}")
            
    def show_context_menu(self, position):
        """プロファイルリストのコンテキストメニューを表示"""
        item = self.profile_list.itemAt(position)
        if not item:
            return
            
        profile_name = item.data(Qt.ItemDataRole.UserRole)
        current_profile = self.profile_manager.get_current_profile_name()
        is_current = profile_name == current_profile
        
        menu = QMenu(self)
        
        # 切り替えアクション
        switch_action = QAction("切り替え", self)
        switch_action.triggered.connect(self.switch_profile)
        switch_action.setEnabled(not is_current)
        menu.addAction(switch_action)
        
        menu.addSeparator()
        
        # 名前変更アクション
        rename_action = QAction("名前変更", self)
        rename_action.triggered.connect(self.rename_profile)
        menu.addAction(rename_action)
        
        # エクスポートアクション
        export_action = QAction("エクスポート", self)
        export_action.triggered.connect(self.export_profile)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        # 削除アクション
        delete_action = QAction("削除", self)
        delete_action.triggered.connect(self.delete_profile)
        delete_action.setEnabled(not is_current)
        menu.addAction(delete_action)
        
        menu.exec(self.profile_list.mapToGlobal(position))