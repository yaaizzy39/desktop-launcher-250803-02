"""
DragDropHandler - ドラッグ＆ドロップ処理のユーティリティ
"""

import os
from PyQt6.QtCore import QMimeData, QUrl
from PyQt6.QtGui import QDrag


class DragDropUtils:
    """ドラッグ＆ドロップ関連のユーティリティクラス"""
    
    @staticmethod
    def is_valid_file_drop(mime_data):
        """有効なファイルドロップかチェック"""
        if not mime_data.hasUrls():
            return False
            
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path and os.path.exists(file_path):
                return True
        return False
        
    @staticmethod
    def get_dropped_files(mime_data):
        """ドロップされたファイルのパスリストを取得"""
        file_paths = []
        if mime_data.hasUrls():
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if file_path and os.path.exists(file_path):
                    file_paths.append(file_path)
        return file_paths
        
    @staticmethod
    def is_executable_file(file_path):
        """実行可能ファイルかチェック"""
        if not os.path.isfile(file_path):
            return False
            
        # Windows実行ファイルの拡張子
        executable_extensions = ['.exe', '.bat', '.cmd', '.com', '.scr', '.lnk']
        _, ext = os.path.splitext(file_path.lower())
        return ext in executable_extensions
        
    @staticmethod
    def is_folder(file_path):
        """フォルダかチェック"""
        return os.path.isdir(file_path)
        
    @staticmethod
    def get_file_info(file_path):
        """ファイル情報を取得"""
        if not os.path.exists(file_path):
            return None
            
        return {
            'path': file_path,
            'name': os.path.basename(file_path),
            'type': 'folder' if os.path.isdir(file_path) else 'file',
            'is_executable': DragDropUtils.is_executable_file(file_path),
            'size': os.path.getsize(file_path) if os.path.isfile(file_path) else 0,
            'modified': os.path.getmtime(file_path)
        }
        
    @staticmethod
    def filter_supported_files(file_paths):
        """サポートされているファイルのみをフィルタリング"""
        supported_files = []
        for file_path in file_paths:
            if (os.path.isdir(file_path) or 
                DragDropUtils.is_executable_file(file_path) or
                file_path.lower().endswith('.lnk')):  # ショートカットファイル
                supported_files.append(file_path)
        return supported_files
        
    @staticmethod
    def create_file_mime_data(file_paths):
        """ファイルパスからMimeDataを作成"""
        mime_data = QMimeData()
        urls = []
        for file_path in file_paths:
            if os.path.exists(file_path):
                urls.append(QUrl.fromLocalFile(file_path))
        mime_data.setUrls(urls)
        return mime_data


class DropValidator:
    """ドロップ検証用クラス"""
    
    def __init__(self, accept_folders=True, accept_executables=True, accept_shortcuts=True):
        self.accept_folders = accept_folders
        self.accept_executables = accept_executables
        self.accept_shortcuts = accept_shortcuts
        
    def validate_drop(self, mime_data):
        """ドロップデータを検証"""
        if not DragDropUtils.is_valid_file_drop(mime_data):
            return False, "有効なファイルがありません"
            
        file_paths = DragDropUtils.get_dropped_files(mime_data)
        valid_files = []
        
        for file_path in file_paths:
            if os.path.isdir(file_path) and self.accept_folders:
                valid_files.append(file_path)
            elif DragDropUtils.is_executable_file(file_path) and self.accept_executables:
                valid_files.append(file_path)
            elif file_path.lower().endswith('.lnk') and self.accept_shortcuts:
                valid_files.append(file_path)
                
        if not valid_files:
            return False, "対応していないファイル形式です"
            
        return True, valid_files
        
    def get_error_message(self, file_paths):
        """エラーメッセージを取得"""
        if not file_paths:
            return "ファイルが見つかりません"
            
        unsupported = []
        for file_path in file_paths:
            if not (os.path.isdir(file_path) or 
                   DragDropUtils.is_executable_file(file_path) or
                   file_path.lower().endswith('.lnk')):
                unsupported.append(os.path.basename(file_path))
                
        if unsupported:
            return f"対応していないファイル: {', '.join(unsupported[:3])}"
            
        return "不明なエラー"