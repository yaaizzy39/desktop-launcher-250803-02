"""
DataManager - アプリケーションデータの保存・読み込み管理
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path


class DataManager:
    """データ管理クラス"""
    
    def __init__(self):
        self.app_name = "DesktopLauncher"
        self.config_dir = self.get_config_directory()
        self.config_file = os.path.join(self.config_dir, "groups.json")
        self.backup_dir = os.path.join(self.config_dir, "backups")
        
        # 設定ディレクトリを作成
        self.ensure_config_directory()
        
    def get_config_directory(self):
        """設定ディレクトリのパスを取得"""
        # Windows の場合は %APPDATA% を使用
        if os.name == 'nt':
            appdata = os.environ.get('APPDATA')
            if appdata:
                return os.path.join(appdata, self.app_name)
        
        # フォールバック: ユーザーホームディレクトリ
        home = Path.home()
        return os.path.join(home, f".{self.app_name.lower()}")
        
    def ensure_config_directory(self):
        """設定ディレクトリとバックアップディレクトリを作成"""
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def save_groups(self, groups_data):
        """グループデータを保存"""
        try:
            # バックアップ作成
            self.create_backup()
            
            # データに追加情報を付加
            save_data = {
                'version': '1.0',
                'created': datetime.now().isoformat(),
                'groups': groups_data
            }
            
            # 一時ファイルに保存してから本ファイルに移動（安全な保存）
            temp_file = self.config_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
                
            # 元ファイルと置き換え
            shutil.move(temp_file, self.config_file)
            
            return True
            
        except Exception as e:
            print(f"グループデータの保存に失敗: {e}")
            # 一時ファイルが残っていたら削除
            temp_file = self.config_file + '.tmp'
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False
            
    def load_groups(self):
        """グループデータを読み込み"""
        try:
            if not os.path.exists(self.config_file):
                return []
                
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # バージョンチェック
            if isinstance(data, dict) and 'groups' in data:
                return data['groups']
            elif isinstance(data, list):
                # 古い形式の場合はそのまま返す
                return data
            else:
                print("不正なデータ形式です")
                return []
                
        except json.JSONDecodeError as e:
            print(f"設定ファイルの読み込みエラー (JSON): {e}")
            # バックアップから復元を試行
            return self.restore_from_backup()
        except Exception as e:
            print(f"設定ファイルの読み込みエラー: {e}")
            return []
            
    def create_backup(self):
        """現在の設定ファイルのバックアップを作成"""
        try:
            if os.path.exists(self.config_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(self.backup_dir, f"groups_{timestamp}.json")
                shutil.copy2(self.config_file, backup_file)
                
                # 古いバックアップを削除（5個まで保持）
                self.cleanup_old_backups()
                
        except Exception as e:
            print(f"バックアップ作成エラー: {e}")
            
    def cleanup_old_backups(self, max_backups=5):
        """古いバックアップファイルを削除"""
        try:
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("groups_") and filename.endswith(".json"):
                    file_path = os.path.join(self.backup_dir, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
                    
            # 作成日時でソート
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 古いファイルを削除
            for file_path, _ in backup_files[max_backups:]:
                os.remove(file_path)
                
        except Exception as e:
            print(f"バックアップクリーンアップエラー: {e}")
            
    def restore_from_backup(self):
        """バックアップから復元"""
        try:
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("groups_") and filename.endswith(".json"):
                    file_path = os.path.join(self.backup_dir, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
                    
            if not backup_files:
                print("利用可能なバックアップがありません")
                return []
                
            # 最新のバックアップを選択
            backup_files.sort(key=lambda x: x[1], reverse=True)
            latest_backup = backup_files[0][0]
            
            print(f"バックアップから復元中: {latest_backup}")
            
            with open(latest_backup, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, dict) and 'groups' in data:
                return data['groups']
            elif isinstance(data, list):
                return data
            else:
                return []
                
        except Exception as e:
            print(f"バックアップからの復元エラー: {e}")
            return []
            
    def export_settings(self, export_path):
        """設定をファイルにエクスポート"""
        try:
            if not os.path.exists(self.config_file):
                return False
                
            shutil.copy2(self.config_file, export_path)
            return True
            
        except Exception as e:
            print(f"設定のエクスポートエラー: {e}")
            return False
            
    def import_settings(self, import_path):
        """設定をファイルからインポート"""
        try:
            # バックアップを作成
            self.create_backup()
            
            # インポートファイルを検証
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # データが有効かチェック
            if isinstance(data, dict) and 'groups' in data:
                groups = data['groups']
            elif isinstance(data, list):
                groups = data
            else:
                return False
                
            # 各グループのデータを検証
            for group in groups:
                if not isinstance(group, dict) or 'name' not in group:
                    return False
                    
            # 設定ファイルをコピー
            shutil.copy2(import_path, self.config_file)
            return True
            
        except Exception as e:
            print(f"設定のインポートエラー: {e}")
            return False
            
    def get_config_info(self):
        """設定情報を取得"""
        info = {
            'config_dir': self.config_dir,
            'config_file': self.config_file,
            'backup_dir': self.backup_dir,
            'config_exists': os.path.exists(self.config_file),
            'backup_count': 0
        }
        
        try:
            if os.path.exists(self.backup_dir):
                backup_files = [f for f in os.listdir(self.backup_dir) 
                               if f.startswith("groups_") and f.endswith(".json")]
                info['backup_count'] = len(backup_files)
        except:
            pass
            
        return info
        
    def reset_settings(self):
        """設定をリセット"""
        try:
            # バックアップを作成
            self.create_backup()
            
            # 設定ファイルを削除
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                
            return True
            
        except Exception as e:
            print(f"設定リセットエラー: {e}")
            return False