"""
YukkuLips

Copyright (c) 2018 - 2020 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx
import wx.lib.agw.buttonpanel as BP
import wx.lib.newevent as NE

from copy import deepcopy

from .layout_edit_dialog import YKLLauoutEditDialog
from media_utility.image_tool import get_scene_image, get_rescaled_image


YKLLauoutUpdate, EVT_YKL_LAYOUT_UPDATE = NE.NewCommandEvent()

class YKLLayoutPanel(wx.Panel):
    def __init__(self, parent, idx, ctx):
        super().__init__(parent, idx)
        self.ctx = ctx
        vbox = wx.BoxSizer(wx.VERTICAL)
        button_panel = BP.ButtonPanel(self, wx.ID_ANY, "レイアウトプレビュー")
        bp_art = button_panel.GetBPArt()
        bp_art.SetColour(BP.BP_BACKGROUND_COLOUR, wx.Colour(48, 48, 48))
        bp_art.SetColour(BP.BP_TEXT_COLOUR, wx.Colour(220, 220, 220))
        # レイアウト編集ボタン
        self.edit_btn = wx.Button(button_panel, wx.ID_ANY, "レイアウト編集")
        button_panel.AddControl(self.edit_btn)
        self.edit_btn.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.OnEditBtnClick, id=self.edit_btn.GetId())
        vbox.Add(button_panel, flag=wx.EXPAND)
        # シーンイメージプレビューパネル
        if self.ctx:
            current_sceneblock = self.ctx.get_current_sceneblock()
            if current_sceneblock:
                scene_image = current_sceneblock.scene_image
                _, h = scene_image.size
                scene_image = get_rescaled_image(scene_image, 380/h)
                self.edit_btn.Enable()
            else:
                scene_image = get_scene_image([], [], [])
                _, h = scene_image.size
                scene_image = get_rescaled_image(scene_image, 380/h)
        else:
            scene_image = get_scene_image([], [], [])
            _, h = scene_image.size
            scene_image = get_rescaled_image(scene_image, 380/h)
        self.ppanel = PreviewPanel(self, wx.ID_ANY, scene_image)
        vbox.Add(self.ppanel, 1, flag=wx.EXPAND)
        vbox.Layout()
        self.SetSizer(vbox)

    def OnEditBtnClick(self, event):
        block = deepcopy(self.ctx.get_current_sceneblock())
        with YKLLauoutEditDialog(self, self.ctx, block) as e_dialog:
            ret = e_dialog.ShowModal()
            if not (ret == wx.ID_CANCEL or ret == wx.ID_CLOSE):
                block.movie_generated = False
                self.ctx.set_new_sceneblock(block)
                wx.PostEvent(self, YKLLauoutUpdate(self.GetId()))

    def update_layoutpreview(self):
        current_sceneblock = self.ctx.get_current_sceneblock()
        if current_sceneblock:
            scene_image = current_sceneblock.scene_image
            _, h = scene_image.size
            scene_image = get_rescaled_image(scene_image, 380/h)
            self.edit_btn.Enable()
        else:
            scene_image = get_scene_image([], [], [])
            _, h = scene_image.size
            scene_image = get_rescaled_image(scene_image, 380/h)
            self.edit_btn.Enable(False)
        self.ppanel.set_image(scene_image)

    def set_context(self, ctx):
        self.ctx = ctx


class PreviewPanel(wx.ScrolledWindow):
    def __init__(self, parent, idx, image):
        super().__init__(parent, idx)
        self.max_width = image.size[0]
        self.max_height = image.size[1]
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        bmp = wx.Bitmap.FromBufferRGBA(*image.size, image.tobytes())
        self.sbmp = wx.StaticBitmap(self, wx.ID_ANY, bmp)
        hbox.Add(self.sbmp)
        hbox.Layout()
        self.SetSizer(hbox)
        self.SetVirtualSize(self.max_width, self.max_height)
        self.SetScrollRate(20, 20)

    def set_image(self, image):
        bmp = wx.Bitmap.FromBufferRGBA(*image.size, image.tobytes())
        self.sbmp.SetBitmap(bmp)
        size = bmp.GetSize()
        self.max_width = size.Width
        self.max_height = size.Height
        self.SetVirtualSize(self.max_width, self.max_height)
        self.Refresh()
