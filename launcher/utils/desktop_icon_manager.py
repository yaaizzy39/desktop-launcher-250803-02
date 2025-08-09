"""
DesktopIconManager - デスクトップアイコンの表示/非表示を制御するクラス
既存機能とは完全に独立して動作します。
"""

import ctypes
from ctypes import wintypes
import json
import os


class DesktopIconManager:
    """デスクトップアイコンの表示/非表示制御クラス"""
    
    def __init__(self):
        """初期化"""
        self.desktop_icons_visible = True  # デスクトップアイコンの表示状態
        self.desktop_window_handle = None  # デスクトップウィンドウのハンドル
        self.listview_handle = None       # アイコンリストビューのハンドル
        
        # Windows APIの準備
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # デスクトップアイコンの初期状態を確認
        self._initialize_desktop_handles()
        self._check_initial_state()
        
    def _initialize_desktop_handles(self):
        """デスクトップウィンドウのハンドルを取得"""
        try:
            # デスクトップウィンドウを取得
            self.desktop_window_handle = self.user32.GetDesktopWindow()
            
            # "SHELLDLL_DefView"ウィンドウを検索
            def enum_child_proc(hwnd, lparam):
                class_name = ctypes.create_unicode_buffer(256)
                self.user32.GetClassNameW(hwnd, class_name, 256)
                if class_name.value == "SHELLDLL_DefView":
                    # その子ウィンドウ("SysListView32")を検索
                    def enum_grandchild_proc(hwnd_child, lparam_child):
                        child_class_name = ctypes.create_unicode_buffer(256)
                        self.user32.GetClassNameW(hwnd_child, child_class_name, 256)
                        if child_class_name.value == "SysListView32":
                            self.listview_handle = hwnd_child
                            return False  # 見つけたので列挙停止
                        return True
                    
                    EnumChildProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
                    enum_grandchild_callback = EnumChildProc(enum_grandchild_proc)
                    self.user32.EnumChildWindows(hwnd, enum_grandchild_callback, 0)
                    
                    if self.listview_handle:
                        return False  # 見つけたので列挙停止
                return True
            
            # コールバック関数の型定義
            EnumChildProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            enum_child_callback = EnumChildProc(enum_child_proc)
            
            # "Progman"ウィンドウの子ウィンドウを列挙
            progman_handle = self.user32.FindWindowW("Progman", None)
            if progman_handle:
                self.user32.EnumChildWindows(progman_handle, enum_child_callback, 0)
            
            # まだ見つからない場合は、"WorkerW"ウィンドウも確認
            if not self.listview_handle:
                def enum_worker_proc(hwnd, lparam):
                    class_name = ctypes.create_unicode_buffer(256)
                    self.user32.GetClassNameW(hwnd, class_name, 256)
                    if class_name.value == "WorkerW":
                        # WorkerWの子ウィンドウを確認
                        self.user32.EnumChildWindows(hwnd, enum_child_callback, 0)
                        if self.listview_handle:
                            return False  # 見つけたので停止
                    return True
                
                EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
                enum_worker_callback = EnumWindowsProc(enum_worker_proc)
                self.user32.EnumWindows(enum_worker_callback, 0)
            
            print(f"[DesktopIconManager] デスクトップハンドル初期化:")
            print(f"  Desktop Window: {self.desktop_window_handle}")
            print(f"  ListView Handle: {self.listview_handle}")
            
        except Exception as e:
            print(f"[DesktopIconManager] ハンドル初期化エラー: {e}")
            self.listview_handle = None
    
    def _check_initial_state(self):
        """デスクトップアイコンの初期表示状態をチェック"""
        try:
            if self.listview_handle:
                # ウィンドウが表示されているかチェック
                is_visible = self.user32.IsWindowVisible(self.listview_handle)
                self.desktop_icons_visible = bool(is_visible)
                print(f"[DesktopIconManager] 初期状態: {'表示' if self.desktop_icons_visible else '非表示'}")
            else:
                print(f"[DesktopIconManager] 警告: デスクトップアイコンのハンドルが取得できませんでした")
                self.desktop_icons_visible = True  # デフォルトで表示状態とする
                
        except Exception as e:
            print(f"[DesktopIconManager] 初期状態確認エラー: {e}")
            self.desktop_icons_visible = True
    
    def toggle_desktop_icons(self):
        """デスクトップアイコンの表示/非表示を切り替え"""
        try:
            print(f"[DesktopIconManager] デスクトップアイコン切り替え開始")
            print(f"  現在の状態: {'表示' if self.desktop_icons_visible else '非表示'}")
            
            if not self.listview_handle:
                print(f"[DesktopIconManager] エラー: デスクトップアイコンのハンドルが無効です")
                return False
            
            # 新しい状態を決定
            new_state = not self.desktop_icons_visible
            
            # ウィンドウの表示/非表示を切り替え
            if new_state:
                # 表示
                result = self.user32.ShowWindow(self.listview_handle, 1)  # SW_SHOWNORMAL
                print(f"  ShowWindow(表示) 結果: {result}")
            else:
                # 非表示
                result = self.user32.ShowWindow(self.listview_handle, 0)  # SW_HIDE
                print(f"  ShowWindow(非表示) 結果: {result}")
            
            # 状態を更新
            self.desktop_icons_visible = new_state
            
            # デスクトップを更新
            self.user32.UpdateWindow(self.desktop_window_handle)
            self.user32.RedrawWindow(self.desktop_window_handle, None, None, 0x0001 | 0x0004)  # RDW_INVALIDATE | RDW_UPDATENOW
            
            print(f"  新しい状態: {'表示' if self.desktop_icons_visible else '非表示'}")
            print(f"[DesktopIconManager] デスクトップアイコン切り替え完了")
            
            return True
            
        except Exception as e:
            print(f"[DesktopIconManager] デスクトップアイコン切り替えエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def show_desktop_icons(self):
        """デスクトップアイコンを表示"""
        if not self.desktop_icons_visible:
            return self.toggle_desktop_icons()
        return True
    
    def hide_desktop_icons(self):
        """デスクトップアイコンを非表示"""
        if self.desktop_icons_visible:
            return self.toggle_desktop_icons()
        return True
    
    def is_desktop_icons_visible(self):
        """デスクトップアイコンが表示されているかを返す"""
        return self.desktop_icons_visible
    
    def get_status_info(self):
        """状態情報を取得（デバッグ用）"""
        return {
            'desktop_icons_visible': self.desktop_icons_visible,
            'desktop_window_handle': self.desktop_window_handle,
            'listview_handle': self.listview_handle,
            'handles_valid': self.listview_handle is not None
        }


# テスト用コード
if __name__ == "__main__":
    print("=== DesktopIconManager テスト ===")
    
    manager = DesktopIconManager()
    
    print(f"\n状態情報:")
    info = manager.get_status_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print(f"\n現在の状態: {'表示' if manager.is_desktop_icons_visible() else '非表示'}")
    
    # 切り替えテスト
    input("Enterキーを押すと切り替えテストを実行します...")
    
    print("\n=== 切り替えテスト 1回目 ===")
    manager.toggle_desktop_icons()
    
    input("Enterキーを押すと2回目の切り替えを実行します...")
    
    print("\n=== 切り替えテスト 2回目 ===")
    manager.toggle_desktop_icons()
    
    print("\n=== テスト完了 ===")