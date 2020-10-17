# -*- mode: python -*-

block_cipher = None


a = Analysis(['YukkuLips.py'],
             pathex=['.'],
             binaries=[],
             datas=[("ffmpeg/ffmpeg", "ffmpeg"),
                    ("ykl_app_setting/app_setting.json", "setting"),
                    ("images/icon.png", "images"),
                    ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='YukkuLips',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='YukkuLips')
app = BUNDLE(coll,
             name='YukkuLips.app',
             icon='AppIcon.icns',
             bundle_identifier=None,
             info_plist={
                'CFBundleShortVersionString': '0.2.4',
                'NSHumanReadableCopyright': 'Copyright © 2018 - 2020, SuitCase\nAll rights reserved.',
                'NSHighResolutionCapable': 'True',
                'NSRequiresAquaSystemAppearance': 'No',
             })
