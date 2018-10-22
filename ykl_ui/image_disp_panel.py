"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx


class ImageDispPanel(wx.Panel):
    def __init__(self, parent, idx, context, size=(100, 100)):
        super().__init__(parent, idx, size=size)
        self.context = context
        self.box = None
        self.ui_image = None
        self.create_widgets()

    def create_widgets(self):
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.box)
        image = wx.Image(str(self.context.ui_image_path / "ui_image.png"))
        bmp = image.ConvertToBitmap()
        self.box.Add(width=0, height=0, proportion=1)
        self.ui_image = wx.StaticBitmap(self, wx.ID_ANY, bmp)
        self.box.Add(self.ui_image, proportion=0, flag=wx.ALIGN_CENTER)
        self.box.Add(width=0, height=0, proportion=1)
        self.box.Layout()

    def update_panel(self):
        image = wx.Image(str(self.context.ui_image_path / "ui_image.png"))
        bmp = image.ConvertToBitmap()
        self.box.Clear(True)
        self.box.Add(width=0, height=0, proportion=1)
        self.ui_image = wx.StaticBitmap(self, wx.ID_ANY, bmp)
        self.box.Add(self.ui_image, proportion=1, flag=wx.ALIGN_CENTER)
        self.box.Add(width=0, height=0, proportion=1)
        self.box.Layout()
