"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

from copy import deepcopy

import wx
import wx.lib.agw.buttonpanel as BP
import wx.lib.newevent as NE

from .sozai_edit_dialog import YKLSozaiEditDialog
from media_utility.image_tool import get_thumbnail


YKLSozaiUpdate, EVT_YKL_SOZAI_UPDATE = NE.NewCommandEvent()

class YKLSozaiPanel(wx.Panel):
    def __init__(self, parent, idx, ctx):
        super().__init__(parent, idx)
        self.ctx = ctx
        vbox = wx.BoxSizer(wx.VERTICAL)
        button_panel = BP.ButtonPanel(self, wx.ID_ANY, "キャラ素材リスト")
        bp_art = button_panel.GetBPArt()
        bp_art.SetColour(BP.BP_BACKGROUND_COLOUR, wx.Colour(48, 48, 48))
        bp_art.SetColour(BP.BP_TEXT_COLOUR, wx.Colour(220, 220, 220))
        # キャラ素材編集ボタン
        self.edit_btn = wx.Button(button_panel, wx.ID_ANY, "素材編集")
        button_panel.AddControl(self.edit_btn)
        self.edit_btn.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.OnEditBtnClick, id=self.edit_btn.GetId())
        # キャラ素材追加ボタン
        add_btn = BP.ButtonInfo(button_panel, wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_OTHER, (16, 16)))
        button_panel.AddButton(add_btn)
        self.Bind(wx.EVT_BUTTON, self.OnAddBtnClick, id=add_btn.GetId())
        # キャラ素材削除ボタン
        self.remove_btn = BP.ButtonInfo(button_panel, wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_MINUS, wx.ART_OTHER, (16, 16)))
        button_panel.AddButton(self.remove_btn)
        self.Bind(wx.EVT_BUTTON, self.OnRemoveBtnClick, id=self.remove_btn.GetId())
        self.remove_btn.SetStatus("Disabled")
        vbox.Add(button_panel, flag=wx.EXPAND)

        self.il = wx.ImageList(100, 100)
        self.sozai_list = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT)
        self.sozai_list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        self.sozai_list.AppendColumn('プレビュー', width=120)
        self.sozai_list.AppendColumn('名前', width=150)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, id=self.sozai_list.GetId())
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, id=self.sozai_list.GetId())
        vbox.Add(self.sozai_list, 1, flag=wx.EXPAND | wx.ALL, border=1)
        self.SetSizer(vbox)

        button_panel.DoLayout()
        vbox.Layout()

    def set_context(self, ctx):
        self.ctx = ctx

    def OnItemSelected(self, event):
        self.remove_btn.SetStatus("Normal")
        self.edit_btn.Enable()
        self.Refresh()

    def OnItemDeselected(self, event):
        self.remove_btn.SetStatus("Disabled")
        self.edit_btn.Enable(False)
        self.Refresh()

    def OnAddBtnClick(self, event):
        with wx.DirDialog(self, "キャラ素材フォルダを選択") as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_CANCEL:
                return
            path = dir_dialog.GetPath()
            self.ctx.add_sozai(path)
            wx.PostEvent(self, YKLSozaiUpdate(self.GetId()))

    def OnEditBtnClick(self, event):
        block = self.ctx.get_current_sceneblock()
        idx = self.get_selected_idx()
        sozai = deepcopy(block.get_sozais()[idx])
        with YKLSozaiEditDialog(self, self.ctx, sozai) as e_dialog:
            ret = e_dialog.ShowModal()
            if not (ret == wx.ID_CANCEL or ret == wx.ID_CLOSE):
                self.ctx.set_new_sozai(idx, sozai)
                wx.PostEvent(self, YKLSozaiUpdate(self.GetId()))

    def OnRemoveBtnClick(self, event):
        idx = -1
        # キャラ素材リストの先頭から削除するため、
        # 後続の選択キャラ素材はインデックスが削除数ぶんずれる。
        rm_num = 0
        while True:
            idx = self.sozai_list.GetNextSelected(idx)
            if idx == -1:
                break
            self.ctx.remove_sozai(idx - rm_num)
            rm_num += 1
        wx.PostEvent(self, YKLSozaiUpdate(self.GetId()))

    def update_sozai_list(self):
        self.sozai_list.DeleteAllItems()
        self.il.RemoveAll()
        block = self.ctx.get_current_sceneblock()
        if block:
            for sozai in block.get_sozais():
                image = sozai.get_image()
                # image = image.resize((100, 100), Image.LANCZOS)
                image = get_thumbnail(image, size=100)
                bmp = wx.Bitmap.FromBufferRGBA(100, 100, image.tobytes())
                self.il.Add(bmp)
            for i, sozai in enumerate(block.get_sozais()):
                self.sozai_list.InsertItem(i, '', i)
                self.sozai_list.SetItem(i, 1, sozai.get_name())
        self.remove_btn.SetStatus("Disabled")

        self.Refresh()

    def get_selected_idx(self):
        for i in range(self.sozai_list.GetItemCount()):
            if self.sozai_list.IsSelected(i):
                return i
        return None

    def any_item_selected(self):
        return self.get_selected_idx() is not None
