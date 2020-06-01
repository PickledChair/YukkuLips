"""
YukkuLips

Copyright (c) 2018 - 2020 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx


class YKLProjectEditDialog(wx.Dialog):
    def __init__(self, parent, ctx):
        super().__init__(parent, title="プロジェクト設定", size=(400, 160))
        self.ctx = ctx
        self.resolutions = {
            "1080p": (1920, 1080),
            "720p": (1280, 720),
            }
        box = wx.BoxSizer(wx.VERTICAL)
        # 解像度設定
        resolution_box = wx.BoxSizer(wx.HORIZONTAL)
        res_lbl = wx.StaticText(self, wx.ID_ANY, "動画解像度：")
        resolution_box.Add(res_lbl, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.res_choice = wx.Choice(self, wx.ID_ANY, choices=list(self.resolutions.keys()))
        current_idx = self.get_res_idx()
        if current_idx:
            self.res_choice.SetSelection(current_idx)
        resolution_box.Add(self.res_choice, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)

        box.Add(resolution_box, flag=wx.ALIGN_CENTER)

        # 背景色設定
        bgcolor_box = wx.BoxSizer(wx.HORIZONTAL)
        bg_lbl = wx.StaticText(self, wx.ID_ANY, "背景色：")
        bgcolor_box.Add(bg_lbl, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.cp_ctrl = wx.ColourPickerCtrl(self, wx.ID_ANY, colour=wx.Colour(*tuple(self.ctx.bg_color)))
        bgcolor_box.Add(self.cp_ctrl, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)

        box.Add(bgcolor_box, flag=wx.ALIGN_CENTER)

        # ボタン
        btns = wx.BoxSizer(wx.HORIZONTAL)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "キャンセル")
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=cancel_btn.GetId())
        btns.Add(cancel_btn, flag=wx.ALL, border=5)
        ok_btn = wx.Button(self, wx.ID_OK, "適用して閉じる")
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=ok_btn.GetId())
        btns.Add(ok_btn, flag=wx.ALL, border=5)
        btns.Layout()

        box.Add(btns, 0, flag=wx.RIGHT | wx.TOP | wx.ALIGN_RIGHT, border=5)
        self.SetSizer(box)

    def OnBtnClick(self, event):
        if event.GetId() == wx.ID_OK:
            self.ctx.resolution = self.get_res_value()
            self.ctx.bg_color = self.cp_ctrl.GetColour().Get(includeAlpha=True)
        self.EndModal(event.GetId())

    def get_res_idx(self):
        idx = 0
        for k, v in self.resolutions.items():
            if v == self.ctx.resolution:
                return idx
            idx += 1
        return None

    def get_res_value(self):
        return self.resolutions[
            self.res_choice.GetString(self.res_choice.GetSelection())
            ]


