"""
YukkuLips

Copyright (c) 2018 - 2020 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx
from pathlib import Path

class YKLCreateProjectDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="新規プロジェクト")
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        flexgrid = wx.FlexGridSizer(rows=2, cols=2, gap=(0, 0))

        proj_label = wx.StaticText(self, wx.ID_ANY, 'プロジェクト名：')
        flexgrid.Add(proj_label, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.proj_text = wx.TextCtrl(self, wx.ID_ANY)
        flexgrid.Add(self.proj_text, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTRE_VERTICAL, border=5)

        loc_label = wx.StaticText(self, wx.ID_ANY, '保存場所：')
        flexgrid.Add(loc_label, flag=wx.ALL | wx.ALIGN_CENTRE_VERTICAL, border=5)
        self.dir_ctrl = wx.DirPickerCtrl(self, wx.ID_ANY, message="場所を選択", style=wx.DIRP_SMALL | wx.DIRP_USE_TEXTCTRL)
        flexgrid.Add(self.dir_ctrl, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTRE_VERTICAL)
        vbox1.Add(flexgrid, 1, flag=wx.EXPAND | wx.ALL, border=5)

        btns = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK)
        cancel_btn = wx.Button(self, wx.ID_CANCEL)
        btns.AddButton(ok_btn)
        btns.AddButton(cancel_btn)
        btns.Realize()
        vbox1.Add(btns, 0, flag=wx.EXPAND | wx.ALL, border=5)

        vbox1.SetSizeHints(self)

        self.Bind(wx.EVT_BUTTON, self.OnBtnClick)

        self.SetSizer(vbox1)
        self.Centre()

    def OnBtnClick(self, event):
        if event.GetId() == wx.ID_OK:
            proj_name = self.proj_text.GetValue()
            dir_path = self.dir_ctrl.GetPath()
            proj_path = Path(dir_path) / proj_name
            if len(proj_name) == 0 or len(dir_path) == 0:
                wx.MessageBox("プロジェクト名もしくは保存場所が不正です。\n"
                              "もう一度やり直してください。", "確認",
                              wx.ICON_EXCLAMATION | wx.OK)
                return
            if proj_path.exists():
                wx.MessageBox("同じ保存場所にすでに同名のフォルダがあります。\n"
                              "もう一度やり直してください。", "確認",
                              wx.ICON_EXCLAMATION | wx.OK)
                return
        event.Skip()

    def get_path(self):
        return Path(self.dir_ctrl.GetPath()) / self.proj_text.GetValue()
