"""
YukkuLips

Copyright (c) 2018 - 2020 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx

class YKLWelcomeDialog(wx.Dialog):
    def __init__(self, parent, ids, img_dir):
        super().__init__(parent, title='YukkuLipsへようこそ！', size=(500, 320))

        panel = wx.Panel(self, wx.ID_ANY)
        box = wx.BoxSizer(wx.VERTICAL)
        bmp = wx.Bitmap()
        bmp.LoadFile(str(img_dir / "icon.png"))
        sbmp = wx.StaticBitmap(self, wx.ID_ANY, bmp)
        box.Add(sbmp, flag=wx.ALIGN_CENTER)
        panel.SetSizer(box)

        btns = wx.BoxSizer(wx.HORIZONTAL)

        pre_btn = wx.Button(self, ids[0], '既存のプロジェクトを探す')
        btns.Add(pre_btn, flag=wx.ALL, border=5)
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=pre_btn.GetId())
        # his_btn = wx.Button(self, ids[1], '履歴から開く')
        # btns.Add(his_btn, flag=wx.ALL, border=5)
        # self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=his_btn.GetId())
        new_btn = wx.Button(self, ids[1], '新規作成')
        btns.Add(new_btn, flag=wx.ALL, border=5)
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=new_btn.GetId())
        btns.Layout()

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(panel, 1, flag=wx.EXPAND | wx.ALL, border=5)
        vbox.Add(btns, 0, flag=wx.ALIGN_CENTRE)
        vbox.Layout()
        self.SetSizer(vbox)
        self.Centre()

    def OnBtnClick(self, event):
        self.EndModal(event.GetId())
