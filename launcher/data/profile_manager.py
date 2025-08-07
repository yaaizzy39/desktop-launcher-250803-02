"""
ProfileManager - プロファイル（状態）管理システム
ユーザーが名前を付けてアプリの状態を保存・切り替え可能にする
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path


class ProfileManager:
    """プロファイル管理クラス"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.config_dir = data_manager.config_dir
        self.profiles_dir = os.path.join(self.config_dir, "profiles")
        self.current_profile_file = os.path.join(self.config_dir, "current_profile.json")
        
        # プロファイルディレクトリを作成
        self.ensure_profiles_directory()
        
        # 現在のプロファイル情報
        self.current_profile_name = None
        self.load_current_profile_info()
        
    def ensure_profiles_directory(self):
        """プロファイルディレクトリを作成"""
        os.makedirs(self.profiles_dir, exist_ok=True)
        
    def save_profile(self, profile_name, description="", hotkey_info=None):
        """現在の状態をプロファイルとして保存"""
        try:
            if not profile_name or not profile_name.strip():
                return False, "プロファイル名が空です"
                
            profile_name = profile_name.strip()
            
            # 無効な文字をチェック
            invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
            if any(char in profile_name for char in invalid_chars):
                return False, "プロファイル名に無効な文字が含まれています"
            
            # プロファイルフォルダを作成
            profile_dir = os.path.join(self.profiles_dir, profile_name)
            os.makedirs(profile_dir, exist_ok=True)
            
            # 現在のグループデータを取得
            current_groups = self.data_manager.load_groups()
            
            # プロファイルデータを作成
            profile_data = {
                'name': profile_name,
                'description': description,
                'created': datetime.now().isoformat(),
                'updated': datetime.now().isoformat(),
                'version': '1.0',
                'groups': current_groups,
                'hotkey': hotkey_info  # ホットキー情報を追加
            }
            
            # プロファイルファイルに保存
            profile_file = os.path.join(profile_dir, "profile.json")
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
                
            print(f"プロファイル '{profile_name}' を保存しました")
            return True, f"プロファイル '{profile_name}' を保存しました"
            
        except Exception as e:
            error_msg = f"プロファイル保存エラー: {e}"
            print(error_msg)
            return False, error_msg
            
    def create_empty_profile(self, profile_name, description="", hotkey_info=None):
        """空のプロファイルを作成"""
        try:
            if not profile_name or not profile_name.strip():
                return False, "プロファイル名が空です"
                
            profile_name = profile_name.strip()
            
            # 無効な文字をチェック
            invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
            if any(char in profile_name for char in invalid_chars):
                return False, "プロファイル名に無効な文字が含まれています"
            
            # プロファイルフォルダを作成
            profile_dir = os.path.join(self.profiles_dir, profile_name)
            os.makedirs(profile_dir, exist_ok=True)
            
            # 空のプロファイルデータを作成
            profile_data = {
                'name': profile_name,
                'description': description,
                'created': datetime.now().isoformat(),
                'updated': datetime.now().isoformat(),
                'version': '1.0',
                'groups': [],  # 空のグループリスト
                'hotkey': hotkey_info  # ホットキー情報を追加
            }
            
            # プロファイルファイルに保存
            profile_file = os.path.join(profile_dir, "profile.json")
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
                
            print(f"空のプロファイル '{profile_name}' を作成しました")
            return True, f"空のプロファイル '{profile_name}' を作成しました"
            
        except Exception as e:
            error_msg = f"空プロファイル作成エラー: {e}"
            print(error_msg)
            return False, error_msg
            
    def load_profile(self, profile_name):
        """プロファイルを読み込み"""
        try:
            if not self.profile_exists(profile_name):
                return False, f"プロファイル '{profile_name}' が見つかりません"
                
            profile_dir = os.path.join(self.profiles_dir, profile_name)
            profile_file = os.path.join(profile_dir, "profile.json")
            
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                
            # プロファイルのグループデータを取得
            groups_data = profile_data.get('groups', [])
            
            return True, groups_data
            
        except Exception as e:
            error_msg = f"プロファイル読み込みエラー: {e}"
            print(error_msg)
            return False, error_msg
            
    def switch_to_profile(self, profile_name):
        """プロファイルに切り替え"""
        try:
            success, result = self.load_profile(profile_name)
            if not success:
                return False, result
                
            groups_data = result
            
            # 現在の状態をバックアップ（自動保存）
            if self.current_profile_name:
                self.save_profile(self.current_profile_name, "自動保存")
            
            # 新しいプロファイルのデータを適用
            self.data_manager.save_groups(groups_data)
            
            # 現在のプロファイル情報を更新
            self.current_profile_name = profile_name
            self.save_current_profile_info()
            
            print(f"プロファイル '{profile_name}' に切り替えました")
            return True, f"プロファイル '{profile_name}' に切り替えました"
            
        except Exception as e:
            error_msg = f"プロファイル切り替えエラー: {e}"
            print(error_msg)
            return False, error_msg
            
    def delete_profile(self, profile_name):
        """プロファイルを削除"""
        try:
            if not self.profile_exists(profile_name):
                return False, f"プロファイル '{profile_name}' が見つかりません"
                
            # 現在使用中のプロファイルは削除できない
            if profile_name == self.current_profile_name:
                return False, "現在使用中のプロファイルは削除できません"
                
            profile_dir = os.path.join(self.profiles_dir, profile_name)
            shutil.rmtree(profile_dir)
            
            print(f"プロファイル '{profile_name}' を削除しました")
            return True, f"プロファイル '{profile_name}' を削除しました"
            
        except Exception as e:
            error_msg = f"プロファイル削除エラー: {e}"
            print(error_msg)
            return False, error_msg
            
    def get_profile_list(self):
        """プロファイル一覧を取得"""
        try:
            profiles = []
            
            if not os.path.exists(self.profiles_dir):
                return profiles
                
            for item in os.listdir(self.profiles_dir):
                profile_dir = os.path.join(self.profiles_dir, item)
                if os.path.isdir(profile_dir):
                    profile_file = os.path.join(profile_dir, "profile.json")
                    if os.path.exists(profile_file):
                        try:
                            with open(profile_file, 'r', encoding='utf-8') as f:
                                profile_data = json.load(f)
                                
                            profiles.append({
                                'name': profile_data.get('name', item),
                                'description': profile_data.get('description', ''),
                                'created': profile_data.get('created', ''),
                                'updated': profile_data.get('updated', ''),
                                'is_current': item == self.current_profile_name
                            })
                        except Exception as e:
                            print(f"プロファイル '{item}' の読み込みエラー: {e}")
                            
            # 作成日時でソート
            profiles.sort(key=lambda x: x.get('created', ''), reverse=True)
            return profiles
            
        except Exception as e:
            print(f"プロファイル一覧取得エラー: {e}")
            return []
            
    def profile_exists(self, profile_name):
        """プロファイルが存在するかチェック"""
        profile_dir = os.path.join(self.profiles_dir, profile_name)
        profile_file = os.path.join(profile_dir, "profile.json")
        return os.path.exists(profile_file)
        
    def get_profile_info(self, profile_name):
        """プロファイル情報を取得"""
        try:
            if not self.profile_exists(profile_name):
                return None
                
            profile_dir = os.path.join(self.profiles_dir, profile_name)
            profile_file = os.path.join(profile_dir, "profile.json")
            
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                
            # グループ数を追加
            groups_count = len(profile_data.get('groups', []))
            profile_data['groups_count'] = groups_count
            profile_data['is_current'] = profile_name == self.current_profile_name
            
            return profile_data
            
        except Exception as e:
            print(f"プロファイル情報取得エラー: {e}")
            return None
            
    def save_current_profile_info(self):
        """現在のプロファイル情報を保存"""
        try:
            current_info = {
                'current_profile': self.current_profile_name,
                'updated': datetime.now().isoformat()
            }
            
            with open(self.current_profile_file, 'w', encoding='utf-8') as f:
                json.dump(current_info, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"現在プロファイル情報保存エラー: {e}")
            
    def load_current_profile_info(self):
        """現在のプロファイル情報を読み込み"""
        try:
            if os.path.exists(self.current_profile_file):
                with open(self.current_profile_file, 'r', encoding='utf-8') as f:
                    current_info = json.load(f)
                    
                self.current_profile_name = current_info.get('current_profile')
                
                # プロファイルが実際に存在するかチェック
                if self.current_profile_name and not self.profile_exists(self.current_profile_name):
                    self.current_profile_name = None
                    
        except Exception as e:
            print(f"現在プロファイル情報読み込みエラー: {e}")
            self.current_profile_name = None
            
    def get_current_profile_name(self):
        """現在のプロファイル名を取得"""
        return self.current_profile_name
        
    def rename_profile(self, old_name, new_name):
        """プロファイル名を変更"""
        try:
            if not self.profile_exists(old_name):
                return False, f"プロファイル '{old_name}' が見つかりません"
                
            if self.profile_exists(new_name):
                return False, f"プロファイル '{new_name}' は既に存在します"
                
            # 無効な文字をチェック
            invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
            if any(char in new_name for char in invalid_chars):
                return False, "プロファイル名に無効な文字が含まれています"
            
            old_dir = os.path.join(self.profiles_dir, old_name)
            new_dir = os.path.join(self.profiles_dir, new_name)
            
            # ディレクトリ名を変更
            shutil.move(old_dir, new_dir)
            
            # プロファイルファイル内の名前も更新
            profile_file = os.path.join(new_dir, "profile.json")
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                
            profile_data['name'] = new_name
            profile_data['updated'] = datetime.now().isoformat()
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            # 現在のプロファイルの場合、情報を更新
            if self.current_profile_name == old_name:
                self.current_profile_name = new_name
                self.save_current_profile_info()
                
            print(f"プロファイル '{old_name}' を '{new_name}' に変更しました")
            return True, f"プロファイル名を '{new_name}' に変更しました"
            
        except Exception as e:
            error_msg = f"プロファイル名変更エラー: {e}"
            print(error_msg)
            return False, error_msg
            
    def export_profile(self, profile_name, export_path):
        """プロファイルをエクスポート"""
        try:
            if not self.profile_exists(profile_name):
                return False, f"プロファイル '{profile_name}' が見つかりません"
                
            profile_info = self.get_profile_info(profile_name)
            if not profile_info:
                return False, "プロファイル情報を取得できませんでした"
                
            # エクスポートデータを作成
            export_data = {
                'export_version': '1.0',
                'exported': datetime.now().isoformat(),
                'app_name': 'iconLaunch',
                'profile': profile_info
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            return True, f"プロファイル '{profile_name}' をエクスポートしました"
            
        except Exception as e:
            error_msg = f"プロファイルエクスポートエラー: {e}"
            print(error_msg)
            return False, error_msg
            
    def import_profile(self, import_path):
        """プロファイルをインポート"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
                
            if 'profile' not in import_data:
                return False, "無効なプロファイルファイルです"
                
            profile_data = import_data['profile']
            profile_name = profile_data.get('name', 'Imported Profile')
            
            # 既存のプロファイルと重複する場合は名前を変更
            original_name = profile_name
            counter = 1
            while self.profile_exists(profile_name):
                profile_name = f"{original_name} ({counter})"
                counter += 1
                
            # プロファイルを保存
            profile_data['name'] = profile_name
            profile_data['updated'] = datetime.now().isoformat()
            
            profile_dir = os.path.join(self.profiles_dir, profile_name)
            os.makedirs(profile_dir, exist_ok=True)
            
            profile_file = os.path.join(profile_dir, "profile.json")
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
                
            return True, f"プロファイル '{profile_name}' をインポートしました"
            
        except Exception as e:
            error_msg = f"プロファイルインポートエラー: {e}"
            print(error_msg)
            return False, error_msg
            
    def update_profile_hotkey(self, profile_name, hotkey_info):
        """プロファイルのホットキー設定を更新"""
        try:
            if not self.profile_exists(profile_name):
                return False, f"プロファイル '{profile_name}' が見つかりません"
                
            profile_dir = os.path.join(self.profiles_dir, profile_name)
            profile_file = os.path.join(profile_dir, "profile.json")
            
            # 既存のプロファイルデータを読み込み
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # ホットキー情報を更新
            profile_data['hotkey'] = hotkey_info
            profile_data['updated'] = datetime.now().isoformat()
            
            # プロファイルファイルに保存
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
                
            print(f"プロファイル '{profile_name}' のホットキーを更新しました")
            return True, f"プロファイル '{profile_name}' のホットキーを更新しました"
            
        except Exception as e:
            error_msg = f"プロファイルホットキー更新エラー: {e}"
            print(error_msg)
            return False, error_msg