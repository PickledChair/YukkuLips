"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

from pathlib import Path
import json
import sys

class YKLAppSetting:
    def __init__(self):
        self.setting_path = Path.cwd() / "ykl_app_setting" / "app_setting.json"
        if getattr(sys, 'frozen', False):
            # frozen は PyInstaller でこのスクリプトが固められた時に sys に追加される属性
            # frozen が見つからない時は素の Python で実行している時なので False を返す
            bundle_dir = sys._MEIPASS
            self.setting_path = Path(bundle_dir) / "setting" / "app_setting.json"
        self.setting_dict = {
            "CopyDialog Next Check": True,
        }
        if not self.setting_path.exists():
            self.save()

    def load(self):
        with self.setting_path.open('r') as f:
            self.setting_dict = json.load(f)

    def save(self):
        with self.setting_path.open('w') as f:
            json.dump(self.setting_dict, f, indent=4, ensure_ascii=False)
