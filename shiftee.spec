# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Shiftee GUI application.

Windows에서 폴더 형태로 배포 가능한 .exe를 생성합니다.
"""

import sys
from pathlib import Path

block_cipher = None

# 프로젝트 루트
project_root = Path('.').absolute()
src_path = project_root / 'src'

a = Analysis(
    [str(src_path / 'shiftee' / 'gui_main.py')],
    pathex=[str(src_path)],
    binaries=[],
    datas=[
        # Playwright 브라우저 바이너리 포함 (Windows 빌드 시)
        # Playwright는 자동으로 브라우저를 포함하지만, 명시적으로 지정 가능
    ],
    hiddenimports=[
        'pydantic',
        'pydantic_settings',
        'pydantic.fields',
        'pydantic.main',
        'playwright',
        'playwright.sync_api',
        'playwright.async_api',
        'playwright._impl._driver',
        'pandas',
        'numpy',
        'openpyxl',
        'openpyxl.cell',
        'openpyxl.styles',
        'dateutil',
        'requests',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        '_tkinter',
        'shiftee',
        'shiftee.settings',
        'shiftee.login',
        'shiftee.attendance',
        'shiftee.cli',
        'shiftee.gui_login',
        'shiftee.gui_main',
        'shiftee.html_report',
        # Kakao/Slack 모듈 (선택사항)
        'kakao_send',
        'slack_send',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ShifteeAnalyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 콘솔 창 표시 (로그 출력 확인용)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 원하는 경우 .ico 파일 경로 지정
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ShifteeAnalyzer',
)
