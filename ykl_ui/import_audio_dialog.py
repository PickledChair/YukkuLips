"""
YukkuLips

Copyright (c) 2018 - 2020 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

from pathlib import Path

import wx


class YKLImportAudioDialog(wx.Dialog):
    def __init__(self, parent, ctx):
        super().__init__(parent, title="音声ファイルパスをインポート", size=(450, 150), style=wx.CAPTION | wx.CLOSE_BOX)
        self.ctx = ctx

        choices = ["全てのキャラ素材",] + [sozai.get_name() for sozai in self.ctx.get_sceneblocks()[0].get_sozais()]

        box = wx.BoxSizer(wx.VERTICAL)
        chara_box = wx.BoxSizer(wx.HORIZONTAL)
        self.chara_choice = wx.Choice(self, wx.ID_ANY, choices=choices)
        chara_box.Add(self.chara_choice, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=10)
        chara_text = wx.StaticText(self, wx.ID_ANY, "に")
        chara_box.Add(chara_text, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=10)
        box.Add(chara_box)

        place_box = wx.BoxSizer(wx.HORIZONTAL)
        self.place = wx.DirPickerCtrl(self, wx.ID_ANY, message="場所を選択", style=wx.DIRP_SMALL | wx.DIRP_USE_TEXTCTRL)
        place_box.Add(self.place, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=10)
        place_text = wx.StaticText(self, wx.ID_ANY, "内の音声ファイルをインポート")
        place_box.Add(place_text, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=10)
        box.Add(place_box)

        btns = wx.BoxSizer(wx.HORIZONTAL)

        cancel_btn = wx.Button(self, wx.ID_CANCEL, "キャンセル")
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=cancel_btn.GetId())
        btns.Add(cancel_btn, flag=wx.ALL, border=5)
        ok_btn = wx.Button(self, wx.ID_OK, "適用して閉じる")
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=ok_btn.GetId())
        btns.Add(ok_btn, flag=wx.ALL, border=5)
        # btns.Layout()

        box.Add(btns, 0, flag=wx.RIGHT | wx.TOP | wx.ALIGN_RIGHT, border=5)
        box.Layout()
        self.SetSizer(box)

    def OnBtnClick(self, event):
        if event.GetId() == wx.ID_OK:
            place = Path(self.place.GetPath())
            if place.exists():
                paths = [path for path in sorted(place.iterdir()) if path.suffix.lower() in [".mp3", ".wav"]]
                idx = 0
                finish = False
                sel_name = self.chara_choice.GetString(self.chara_choice.GetSelection())
                for block in self.ctx.get_sceneblocks():
                    for sozai in block.get_sozais():
                        if idx == len(paths):
                            finish = True
                            break
                        if sel_name == "全てのキャラ素材" or sel_name == sozai.get_name():
                            if len(sozai.speech_content) > 0:
                                sozai.anime_audio_path = str(paths[idx])
                                sozai.movie_audio_path = str(paths[idx])
                                idx += 1
                            else:
                                sozai.anime_audio_path = ""
                                sozai.movie_audio_path = ""
                    if finish:
                        break
        self.ctx.unsaved_check()
        self.EndModal(event.GetId())
