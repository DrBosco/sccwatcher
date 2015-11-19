# -*- mode: python -*-
from os import getcwd
_CURDIR = getcwd()

a = Analysis(['sccwatcher.pyw'],
             pathex=[_CURDIR],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='sccwatcher_2.0.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon='../icons/logo.ico')
