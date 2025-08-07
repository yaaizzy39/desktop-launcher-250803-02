# -*- mode: python ; coding: utf-8 -*-

# version.pyからバージョン情報を読み込み
import sys
import os
sys.path.append(os.path.dirname(__file__))
from version import __version__

# バージョン文字列を解析
version_parts = __version__.split('.')
major = int(version_parts[0])
minor = int(version_parts[1]) if len(version_parts) > 1 else 0
patch = int(version_parts[2]) if len(version_parts) > 2 else 0

# Windows用バージョン情報
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(major, minor, patch, 0),
    prodvers=(major, minor, patch, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u''),
        StringStruct(u'FileDescription', u'iconLaunch - デスクトップランチャー'),
        StringStruct(u'FileVersion', __version__),
        StringStruct(u'InternalName', u'iconLaunch'),
        StringStruct(u'LegalCopyright', u''),
        StringStruct(u'OriginalFilename', u'iconLaunch.exe'),
        StringStruct(u'ProductName', u'iconLaunch'),
        StringStruct(u'ProductVersion', __version__)])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1041, 1200])])
  ]
)