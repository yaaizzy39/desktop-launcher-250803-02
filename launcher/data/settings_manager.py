"""
SettingsManager - アプリケーション設定の管理
"""

import os
import json
import winreg
import shutil
from datetime import datetime
from pathlib import Path


class SettingsManager:
    """設定管理クラス"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.app_name = "iconLaunch"
        self.old_app_name = "DesktopLauncher"  # マイグレーション用
        self.config_dir = data_manager.config_dir
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        
        # デフォルト設定
        self.default_settings = {
            'appearance': {
                'icon_size': 80,
                'opacity': 80,
                'icon_color': '#6496ff',
                'always_on_top': True,
                'show_group_names': True,
                'show_file_paths': True
            },
            'behavior': {
                'startup_with_windows': False,
                'minimize_to_tray': True,
                'launch_interval': 3
            },
            'hotkey': {
                'toggle_visibility': 'Ctrl+Alt+L'
            },
            'advanced': {
                'max_backups': 10
            }
        }
        
        # 設定を読み込み
        self.settings = self.load_settings()
        
        # レジストリキーのマイグレーション
        self.migrate_registry_key()
        
    def load_settings(self):
        """設定ファイルを読み込み"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # メタデータ構造から設定データを取得
                if isinstance(data, dict) and 'settings' in data:
                    # 新しい形式（メタデータ付き）
                    settings_data = data['settings']
                else:
                    # 旧形式（設定データ直接）
                    settings_data = data
                    
                # デフォルト設定とマージ
                settings = self.default_settings.copy()
                if isinstance(settings_data, dict):
                    for category, values in settings_data.items():
                        if category in settings and isinstance(values, dict):
                            settings[category].update(values)
                            
                return settings
            else:
                # 初回起動時はデフォルト設定を保存
                self.save_all_settings(self.default_settings)
                return self.default_settings.copy()
                
        except Exception as e:
            print(f"設定ファイルの読み込みエラー: {e}")
            return self.default_settings.copy()
            
    def save_all_settings(self, settings=None):
        """全設定を保存"""
        try:
            if settings is None:
                settings = self.settings
                
            # バックアップ作成
            self.create_settings_backup()
            
            # 設定にメタデータを追加
            save_data = {
                'version': '1.0',
                'created': datetime.now().isoformat(),
                'settings': settings
            }
            
            # 一時ファイルに保存してから本ファイルに移動
            temp_file = self.settings_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
                
            shutil.move(temp_file, self.settings_file)
            return True
            
        except Exception as e:
            print(f"設定保存エラー: {e}")
            return False
            
    def get_appearance_settings(self):
        """外観設定を取得"""
        return self.settings.get('appearance', {}).copy()
        
    def get_behavior_settings(self):
        """動作設定を取得"""
        return self.settings.get('behavior', {}).copy()
        
    def get_hotkey_settings(self):
        """ホットキー設定を取得"""
        return self.settings.get('hotkey', {}).copy()
        
    def get_advanced_settings(self):
        """高度な設定を取得"""
        return self.settings.get('advanced', {}).copy()
        
    def save_appearance_settings(self, appearance_settings):
        """外観設定を保存"""
        self.settings['appearance'].update(appearance_settings)
        return self.save_all_settings()
        
    def save_behavior_settings(self, behavior_settings):
        """動作設定を保存"""
        # Windows起動設定を処理
        if 'startup_with_windows' in behavior_settings:
            self.set_startup_with_windows(behavior_settings['startup_with_windows'])
            
        self.settings['behavior'].update(behavior_settings)
        return self.save_all_settings()
        
    def save_hotkey_settings(self, hotkey_settings):
        """ホットキー設定を保存"""
        self.settings['hotkey'].update(hotkey_settings)
        return self.save_all_settings()
        
    def save_advanced_settings(self, advanced_settings):
        """高度な設定を保存"""
        self.settings['advanced'].update(advanced_settings)
        return self.save_all_settings()
        
    def set_startup_with_windows(self, enable):
        """Windows起動時の自動実行設定"""
        try:
            key_path = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
            
            if enable:
                # 現在の実行ファイルパスを取得
                import sys
                exe_path = sys.executable
                if getattr(sys, 'frozen', False):
                    # PyInstallerでコンパイルされた場合
                    exe_path = sys.executable
                else:
                    # スクリプト実行の場合
                    script_path = os.path.abspath(__file__)
                    launcher_path = os.path.join(os.path.dirname(script_path), '..', 'main.py')
                    exe_path = f'python "{launcher_path}"'
                    
                # レジストリに登録
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, exe_path)
                    
                print(f"起動時自動実行を有効にしました: {exe_path}")
            else:
                # レジストリから削除
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, self.app_name)
                    print("起動時自動実行を無効にしました")
                except FileNotFoundError:
                    # 既に削除されている場合
                    pass
                    
            return True
            
        except Exception as e:
            print(f"起動設定エラー: {e}")
            return False
            
    def is_startup_enabled(self):
        """起動時自動実行が有効かチェック"""
        try:
            key_path = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                try:
                    winreg.QueryValueEx(key, self.app_name)
                    return True
                except FileNotFoundError:
                    return False
        except Exception:
            return False
            
    def create_settings_backup(self):
        """設定ファイルのバックアップを作成"""
        try:
            if os.path.exists(self.settings_file):
                backup_dir = os.path.join(self.config_dir, "settings_backups")
                os.makedirs(backup_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(backup_dir, f"settings_{timestamp}.json")
                shutil.copy2(self.settings_file, backup_file)
                
                # 古いバックアップを削除（設定値に従って）
                max_backups = self.settings.get('advanced', {}).get('max_backups', 10)
                self.cleanup_old_settings_backups(backup_dir, max_backups)
                
        except Exception as e:
            print(f"設定バックアップエラー: {e}")
            
    def cleanup_old_settings_backups(self, backup_dir, max_backups):
        """古い設定バックアップを削除"""
        try:
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.startswith("settings_") and filename.endswith(".json"):
                    file_path = os.path.join(backup_dir, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
                    
            # 作成日時でソート
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 古いファイルを削除
            for file_path, _ in backup_files[max_backups:]:
                os.remove(file_path)
                
        except Exception as e:
            print(f"設定バックアップクリーンアップエラー: {e}")
            
    def export_all_settings(self, export_dir=None, filename=None):
        """全設定をエクスポート"""
        try:
            # エクスポートディレクトリが指定されていない場合、デフォルトのexportsフォルダを作成
            if export_dir is None:
                export_dir = os.path.join(self.config_dir, "exports")
            
            # エクスポートディレクトリを作成
            os.makedirs(export_dir, exist_ok=True)
            
            # エクスポートファイル名を生成
            if filename is None:
                timestamp = self.get_timestamp()
                export_filename = f"launcher_settings_{timestamp}.json"
            else:
                export_filename = filename
                if not export_filename.endswith('.json'):
                    export_filename += '.json'
            
            export_path = os.path.join(export_dir, export_filename)
            
            # プロファイルデータも含める
            profile_data = self.export_all_profiles()
            
            export_data = {
                'version': '1.0',
                'exported': datetime.now().isoformat(),
                'app_name': self.app_name,
                'settings': self.settings,
                'groups': self.data_manager.load_groups(),  # グループデータも含める
                'profiles': profile_data  # プロファイルデータを追加
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            return export_path  # エクスポートされたファイルのパスを返す
            
        except Exception as e:
            print(f"設定エクスポートエラー: {e}")
            return None
            
    def import_all_settings(self, import_path):
        """全設定をインポート"""
        try:
            # バックアップ作成
            self.create_settings_backup()
            self.data_manager.create_backup()
            
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # データ検証
            if not isinstance(data, dict) or 'settings' not in data:
                return False
                
            # 設定をインポート
            imported_settings = data['settings']
            if isinstance(imported_settings, dict):
                # デフォルト設定とマージ
                new_settings = self.default_settings.copy()
                for category, values in imported_settings.items():
                    if category in new_settings and isinstance(values, dict):
                        new_settings[category].update(values)
                        
                self.settings = new_settings
                self.save_all_settings()
                
            # グループデータもインポート（存在する場合）
            if 'groups' in data and isinstance(data['groups'], list):
                self.data_manager.save_groups(data['groups'])
                
            # プロファイルデータもインポート（存在する場合）
            if 'profiles' in data and isinstance(data['profiles'], dict):
                self.import_all_profiles(data['profiles'])
                
            return True
            
        except Exception as e:
            print(f"設定インポートエラー: {e}")
            return False
            
    def reset_all_settings(self):
        """全設定をリセット"""
        try:
            # バックアップ作成
            self.create_settings_backup()
            
            # デフォルト設定を適用
            self.settings = self.default_settings.copy()
            
            # 起動時自動実行を無効化
            self.set_startup_with_windows(False)
            
            return self.save_all_settings()
            
        except Exception as e:
            print(f"設定リセットエラー: {e}")
            return False
            
    def get_setting(self, category, key, default=None):
        """特定の設定値を取得"""
        return self.settings.get(category, {}).get(key, default)
        
    def set_setting(self, category, key, value):
        """特定の設定値を設定"""
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value
        return self.save_all_settings()
        
    def get_timestamp(self):
        """タイムスタンプを取得"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def get_export_dir(self):
        """エクスポートディレクトリのパスを取得"""
        return os.path.join(self.config_dir, "exports")
        
    def get_default_export_filename(self):
        """デフォルトのエクスポートファイル名を取得"""
        timestamp = self.get_timestamp()
        return f"launcher_settings_{timestamp}.json"
        
    def export_all_profiles(self):
        """全プロファイルデータをエクスポート用に取得"""
        try:
            # プロファイル管理システムが利用可能かチェック
            if not hasattr(self, 'profile_manager') or self.profile_manager is None:
                return None
                
            profiles_data = {}
            profile_list = self.profile_manager.get_profile_list()
            
            for profile_info in profile_list:
                profile_name = profile_info['name']
                
                # プロファイルの完全なデータを取得
                profile_dir = os.path.join(self.profile_manager.profiles_dir, profile_name)
                profile_file = os.path.join(profile_dir, "profile.json")
                groups_file = os.path.join(profile_dir, "groups.json")
                
                profile_export_data = {
                    'info': profile_info,
                    'profile_data': None,
                    'groups_data': None
                }
                
                # プロファイル情報を読み込み
                if os.path.exists(profile_file):
                    try:
                        with open(profile_file, 'r', encoding='utf-8') as f:
                            profile_export_data['profile_data'] = json.load(f)
                    except Exception as e:
                        print(f"プロファイル '{profile_name}' の読み込みエラー: {e}")
                
                # グループデータを読み込み
                if os.path.exists(groups_file):
                    try:
                        with open(groups_file, 'r', encoding='utf-8') as f:
                            profile_export_data['groups_data'] = json.load(f)
                    except Exception as e:
                        print(f"プロファイル '{profile_name}' のグループデータ読み込みエラー: {e}")
                
                profiles_data[profile_name] = profile_export_data
                
            # 現在のプロファイル情報も含める
            if hasattr(self.profile_manager, 'current_profile_name'):
                profiles_data['current_profile'] = self.profile_manager.current_profile_name
                
            return profiles_data
            
        except Exception as e:
            print(f"プロファイルデータエクスポートエラー: {e}")
            return None
            
    def import_all_profiles(self, profiles_data):
        """全プロファイルデータをインポート"""
        try:
            # プロファイル管理システムが利用可能かチェック
            if not hasattr(self, 'profile_manager') or self.profile_manager is None:
                print("プロファイル管理システムが利用できません")
                return False
                
            # 現在のプロファイル情報を保存
            current_profile_backup = getattr(self.profile_manager, 'current_profile_name', None)
            
            # 各プロファイルを復元
            for profile_name, profile_export_data in profiles_data.items():
                if profile_name == 'current_profile':
                    continue  # 現在のプロファイル情報は後で処理
                    
                if not isinstance(profile_export_data, dict):
                    continue
                    
                # プロファイルディレクトリを作成
                profile_dir = os.path.join(self.profile_manager.profiles_dir, profile_name)
                os.makedirs(profile_dir, exist_ok=True)
                
                # プロファイル情報を復元
                if 'profile_data' in profile_export_data and profile_export_data['profile_data']:
                    profile_file = os.path.join(profile_dir, "profile.json")
                    with open(profile_file, 'w', encoding='utf-8') as f:
                        json.dump(profile_export_data['profile_data'], f, indent=2, ensure_ascii=False)
                
                # グループデータを復元
                if 'groups_data' in profile_export_data and profile_export_data['groups_data']:
                    groups_file = os.path.join(profile_dir, "groups.json")
                    with open(groups_file, 'w', encoding='utf-8') as f:
                        json.dump(profile_export_data['groups_data'], f, indent=2, ensure_ascii=False)
                
                print(f"プロファイル '{profile_name}' をインポートしました")
            
            # 現在のプロファイル情報を復元
            if 'current_profile' in profiles_data and profiles_data['current_profile']:
                # エクスポート時の現在プロファイルが存在するかチェック
                exported_current = profiles_data['current_profile']
                if exported_current in profiles_data and exported_current != 'current_profile':
                    self.profile_manager.current_profile_name = exported_current
                    # current_profile.json を更新
                    try:
                        current_profile_data = {
                            'current_profile': exported_current,
                            'updated': datetime.now().isoformat()
                        }
                        with open(self.profile_manager.current_profile_file, 'w', encoding='utf-8') as f:
                            json.dump(current_profile_data, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        print(f"現在のプロファイル情報更新エラー: {e}")
            
            return True
            
        except Exception as e:
            print(f"プロファイルデータインポートエラー: {e}")
            return False

    def get_settings_info(self):
        """設定情報を取得"""
        info = {
            'settings_file': self.settings_file,
            'settings_exists': os.path.exists(self.settings_file),
            'startup_enabled': self.is_startup_enabled(),
            'config_dir': self.config_dir
        }
        
        # バックアップ数
        try:
            backup_dir = os.path.join(self.config_dir, "settings_backups")
            if os.path.exists(backup_dir):
                backup_files = [f for f in os.listdir(backup_dir) 
                               if f.startswith("settings_") and f.endswith(".json")]
                info['settings_backup_count'] = len(backup_files)
            else:
                info['settings_backup_count'] = 0
        except:
            info['settings_backup_count'] = 0
            
        return info
        
    def migrate_registry_key(self):
        """旧レジストリキーから新レジストリキーへのマイグレーション"""
        try:
            # 新しいレジストリキーが既に存在する場合はマイグレーション不要
            if self.is_startup_enabled():
                print("新しいレジストリキーが存在するため、マイグレーションをスキップ")
                return
                
            # 旧レジストリキーをチェック
            if self.is_old_startup_enabled():
                print("旧レジストリキーが見つかりました。マイグレーション開始")
                
                # 新しいキーで自動起動を有効化
                if self.set_startup_with_windows(True):
                    print("新しいレジストリキーでWindows起動時自動実行を有効化しました")
                    
                    # 旧キーを削除
                    if self.remove_old_startup_key():
                        print("旧レジストリキーを削除しました")
                    else:
                        print("旧レジストリキーの削除に失敗しました（手動削除が必要）")
                else:
                    print("新しいレジストリキーの設定に失敗しました")
                    
        except Exception as e:
            print(f"レジストリキーマイグレーションエラー: {e}")
            
    def is_old_startup_enabled(self):
        """旧レジストリキーで起動時自動実行が有効かチェック"""
        try:
            key_path = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                try:
                    winreg.QueryValueEx(key, self.old_app_name)
                    return True
                except FileNotFoundError:
                    return False
        except Exception:
            return False
            
    def remove_old_startup_key(self):
        """旧レジストリキーを削除"""
        try:
            key_path = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                try:
                    winreg.DeleteValue(key, self.old_app_name)
                    return True
                except FileNotFoundError:
                    return True  # 既に削除されている場合も成功とみなす
        except Exception as e:
            print(f"旧レジストリキー削除エラー: {e}")
            return False