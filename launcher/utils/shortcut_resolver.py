"""
ShortcutResolver - Windowsショートカットファイルのリンク先を解決
"""

import os
import sys
from pathlib import Path

def resolve_shortcut(file_path):
    """
    ショートカットファイル(.lnk)のリンク先を取得
    
    Args:
        file_path (str): ショートカットファイルのパス
        
    Returns:
        str: リンク先のパス（ショートカットでない場合は元のパスを返す）
    """
    if not file_path.lower().endswith('.lnk'):
        return file_path
        
    # 方法1: subprocess経由でPowerShellを使用（最も確実）
    try:
        import subprocess
        
        # PowerShellスクリプトでショートカットを解決
        ps_script = f"""
        try {{
            $shell = New-Object -ComObject WScript.Shell
            $shortcut = $shell.CreateShortcut('{file_path}')
            Write-Output $shortcut.TargetPath
        }} catch {{
            Write-Output "{file_path}"
        }}
        """
        
        # ウィンドウを表示しないようにcreationflagsを設定
        import subprocess
        creationflags = 0
        if sys.platform == 'win32':
            creationflags = subprocess.CREATE_NO_WINDOW
        
        result = subprocess.run(['powershell', '-Command', ps_script], 
                              capture_output=True, text=True, timeout=10,
                              creationflags=creationflags)
        
        if result.returncode == 0:
            target_path = result.stdout.strip()
            if target_path and target_path != file_path and os.path.exists(target_path):
                print(f"ショートカット解決: {file_path} -> {target_path}")
                return target_path
                
    except Exception as e:
        print(f"PowerShell方法でのショートカット解決エラー: {e}")
        
    # 方法2: win32comを使用（フォールバック）
    try:
        import win32com.client
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(file_path)
        target_path = shortcut.Targetpath
        
        # リンク先が存在するかチェック
        if target_path and os.path.exists(target_path):
            print(f"ショートカット解決(COM): {file_path} -> {target_path}")
            return target_path
            
    except ImportError:
        print("win32comライブラリが利用できません")
    except Exception as e:
        print(f"win32comでのショートカット解決エラー: {e}")
        
    # 方法3: 代替方法
    alternative_result = _resolve_shortcut_alternative(file_path)
    if alternative_result != file_path:
        return alternative_result
        
    # すべて失敗した場合は元のパスを返す
    print(f"ショートカット解決に失敗、元のパスを使用: {file_path}")
    return file_path

def _resolve_shortcut_alternative(file_path):
    """
    代替方法でショートカットを解決（簡易版）
    """
    try:
        # バイナリ読み込みによる簡易解決
        with open(file_path, 'rb') as f:
            content = f.read()
            
        # .lnkファイルの構造から文字列を抽出（簡易版）
        # 実際のターゲットパスの抽出は複雑なので、基本的な場合のみ対応
        content_str = content.decode('utf-16le', errors='ignore')
        
        # よくあるパターンを検索
        for line in content_str.split('\x00'):
            if line.endswith('.exe') and os.path.exists(line):
                return line
                
        return file_path
        
    except Exception:
        return file_path

def is_shortcut_file(file_path):
    """
    ファイルがショートカットかどうかを判定
    
    Args:
        file_path (str): ファイルパス
        
    Returns:
        bool: ショートカットファイルの場合True
    """
    return file_path.lower().endswith('.lnk')

def get_display_name(file_path):
    """
    表示用のファイル名を取得（ショートカットの場合は.lnkを除く）
    
    Args:
        file_path (str): ファイルパス
        
    Returns:
        str: 表示用ファイル名
    """
    base_name = os.path.basename(file_path)
    if base_name.lower().endswith('.lnk'):
        return base_name[:-4]  # .lnkを除去
    return base_name