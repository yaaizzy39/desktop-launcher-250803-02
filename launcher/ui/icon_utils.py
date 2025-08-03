"""
IconUtils - アイコン取得と管理のユーティリティ
"""

import os
import sys
from PyQt6.QtCore import QFileInfo, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor
from PyQt6.QtWidgets import QFileIconProvider


class IconExtractor:
    """アイコン抽出クラス"""
    
    def __init__(self):
        self.icon_provider = QFileIconProvider()
        self.icon_cache = {}  # アイコンキャッシュ
        
    def get_file_icon(self, file_path, size=32):
        """ファイルのアイコンを取得"""
        try:
            # キャッシュをチェック
            cache_key = f"{file_path}_{size}"
            if cache_key in self.icon_cache:
                return self.icon_cache[cache_key]
                
            # QtのFileIconProviderを使用
            icon = self._get_qt_icon(file_path, size)
                
            # キャッシュに保存
            if not icon.isNull():
                self.icon_cache[cache_key] = icon
                
            return icon
            
        except Exception as e:
            print(f"アイコン取得エラー: {e}")
            return self._get_default_icon(file_path, size)
            
            
    def _get_qt_icon(self, file_path, size):
        """QtのFileIconProviderを使用してアイコンを取得"""
        try:
            file_info = QFileInfo(file_path)
            icon = self.icon_provider.icon(file_info)
            
            if not icon.isNull():
                # サイズを調整
                pixmap = icon.pixmap(size, size)
                return QIcon(pixmap)
            else:
                return self._get_default_icon(file_path, size)
                
        except Exception as e:
            print(f"Qtアイコン取得エラー: {e}")
            return self._get_default_icon(file_path, size)
        
    def _get_default_icon(self, file_path, size):
        """デフォルトアイコンを取得"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if os.path.isdir(file_path):
            # フォルダアイコン
            painter.setBrush(QBrush(QColor(255, 215, 0)))  # ゴールド色
            painter.drawRoundedRect(2, 4, size-4, size-8, 3, 3)
            painter.setBrush(QBrush(QColor(255, 235, 59)))  # 明るいゴールド
            painter.drawRoundedRect(2, 2, size-10, 6, 2, 2)
        elif file_path.lower().endswith('.exe'):
            # 実行ファイルアイコン
            painter.setBrush(QBrush(QColor(100, 150, 255)))  # 青色
            painter.drawRoundedRect(2, 2, size-4, size-4, 4, 4)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "⚡")
        elif file_path.lower().endswith('.lnk'):
            # ショートカットアイコン
            painter.setBrush(QBrush(QColor(128, 128, 255)))  # 薄青色
            painter.drawRoundedRect(2, 2, size-4, size-4, 4, 4)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🔗")
        else:
            # 一般ファイルアイコン
            painter.setBrush(QBrush(QColor(150, 150, 150)))  # グレー色
            painter.drawRoundedRect(2, 2, size-4, size-4, 3, 3)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "📄")
            
        painter.end()
        return QIcon(pixmap)
            
    def clear_cache(self):
        """アイコンキャッシュをクリア"""
        self.icon_cache.clear()


# グローバルアイコン抽出インスタンス
icon_extractor = IconExtractor()