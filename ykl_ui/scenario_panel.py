"""
YukkuLips

Copyright (c) 2018 - 2020 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

from copy import deepcopy
from pathlib import Path
import shutil
import os
import subprocess

import wx
import wx.lib.agw.buttonpanel as BP
import wx.lib.mixins.listctrl as listmix
import wx.lib.newevent as NE

from .scene_edit_dialog import YKLSceneEditDialog
from .roll_copy_dialog import YKLRollingCopyDialog


YKLScenarioUpdate, EVT_YKL_SCENARIO_UPDATE = NE.NewCommandEvent()


class YKLScenarioPanel(wx.Panel):
    def __init__(self, parent, idx, ctx):
        super().__init__(parent, idx)
        self.ctx = ctx
        vbox = wx.BoxSizer(wx.VERTICAL)

        button_panel = BP.ButtonPanel(self, wx.ID_ANY, "シーンブロックリスト")
        bp_art = button_panel.GetBPArt()
        bp_art.SetColour(BP.BP_BACKGROUND_COLOUR, wx.Colour(48, 48, 48))
        bp_art.SetColour(BP.BP_TEXT_COLOUR, wx.Colour(220, 220, 220))
        # シーンブロック編集ボタン
        self.edit_btn = wx.Button(button_panel, wx.ID_ANY, "シーンブロック編集")
        self.Bind(wx.EVT_BUTTON, self.OnEditBtnClick, id=self.edit_btn.GetId())
        button_panel.AddControl(self.edit_btn)
        self.edit_btn.Enable(False)
        # 動画の連結と保存ボタン
        self.save_btn = wx.Button(button_panel, wx.ID_ANY, "動画を連結して保存")
        self.Bind(wx.EVT_BUTTON, self.OnSaveBtnClick, id=self.save_btn.GetId())
        button_panel.AddControl(self.save_btn)
        self.save_btn.Enable(False)
        # ローリングコピーボタン
        self.copy_btn = wx.Button(button_panel, wx.ID_ANY, "コピーダイアログ")
        self.Bind(wx.EVT_BUTTON, self.OnCopyBtnClick, id=self.copy_btn.GetId())
        button_panel.AddControl(self.copy_btn)
        self.copy_btn.Enable(False)
        # シーンブロック追加ボタン
        add_btn = BP.ButtonInfo(button_panel, wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_OTHER, (16, 16)))
        button_panel.AddButton(add_btn)
        self.Bind(wx.EVT_BUTTON, self.OnAddBtnClick, id=add_btn.GetId())
        # シーンブロック削除ボタン
        self.remove_btn = BP.ButtonInfo(button_panel, wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_MINUS, wx.ART_OTHER, (16, 16)))
        button_panel.AddButton(self.remove_btn)
        self.Bind(wx.EVT_BUTTON, self.OnRemoveBtnClick, id=self.remove_btn.GetId())
        self.remove_btn.SetStatus("Disabled")
        vbox.Add(button_panel, flag=wx.EXPAND)

        self.sceneblock_list = ScenarioListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, id=self.sceneblock_list.GetId())
        vbox.Add(self.sceneblock_list, 1, flag=wx.EXPAND | wx.ALL, border=1)

        self.SetSizer(vbox)

        button_panel.DoLayout()
        vbox.Layout()

    def OnEditBtnClick(self, event):
        block = deepcopy(self.ctx.get_current_sceneblock())
        with YKLSceneEditDialog(self, self.ctx, block) as e_dialog:
            ret = e_dialog.ShowModal()
            if not (ret == wx.ID_CANCEL or ret == wx.ID_CLOSE):
                self.ctx.set_new_sceneblock(block)
                wx.PostEvent(self, YKLScenarioUpdate(self.GetId()))

    def OnSaveBtnClick(self, event):
        checked_list = [self.sceneblock_list.IsItemChecked(i) for i in range(self.sceneblock_list.GetItemCount())]
        blocks = self.ctx.get_sceneblocks()
        if any(checked_list):
            blocks = [block for block, checked in zip(blocks, checked_list) if checked]
        if not all([block.movie_generated for block in blocks]):
            if wx.MessageBox("動画未生成のシーンブロックがあります。\n"
                             "続行する場合は未生成分を自動生成します。"
                             "続行しますか？",
                             "確認", wx.ICON_QUESTION | wx.YES_NO,
                             self) == wx.NO:
                return
            for block in blocks:
                if not block.movie_generated:
                    block.generate_movie()
        with wx.FileDialog(
                self, "動画を連結して保存", "", self.ctx.get_project_name(),
                wildcard="MP4 files (*.mp4)|*.mp4", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            movie_path = fileDialog.GetPath()
        self.ctx.concat_movies(movie_path, checked_list)
        wx.PostEvent(self, YKLScenarioUpdate(self.GetId()))
        p = subprocess.Popen(["open", "-a", "QuickTime Player", str(movie_path)])
        p.wait()

    def OnCopyBtnClick(self, event):
        with YKLRollingCopyDialog(self, self.ctx) as e_dialog:
            e_dialog.ShowModal()
            wx.PostEvent(self, YKLScenarioUpdate(self.GetId()))

    def set_context(self, ctx):
        self.ctx = ctx

    def OnAddBtnClick(self, event):
        self.ctx.add_sceneblock()
        wx.PostEvent(self, YKLScenarioUpdate(self.GetId()))

    def OnRemoveBtnClick(self, event):
        checked_list = [self.sceneblock_list.IsItemChecked(i) for i in range(self.sceneblock_list.GetItemCount())]
        if not any(checked_list):
            self.ctx.remove_sceneblock()
        else:
            self.ctx.remove_sceneblocks_list(checked_list)
        wx.PostEvent(self, YKLScenarioUpdate(self.GetId()))

    def OnItemSelected(self, event):
        self.ctx.set_current_sceneblock(event.Index)
        wx.PostEvent(self, YKLScenarioUpdate(self.GetId()))

    def update_sceneblock_list(self):
        self.sceneblock_list.ClearAll()
        if self.ctx.get_current_sceneblock():
            first_sozais = self.ctx.get_sceneblocks()[0].get_sozais()
            sozais_num = len(first_sozais)
            for i in range(sozais_num+2):
                if i == 0:
                    self.sceneblock_list.AppendColumn('', format=wx.LIST_FORMAT_RIGHT, width=80)
                elif i == sozais_num+1:
                    self.sceneblock_list.AppendColumn('動画生成', format=wx.LIST_FORMAT_CENTER, width=80)
                    if 0 < sozais_num < 4:
                        w = int(1000 / sozais_num)
                        self.sceneblock_list.AppendColumn('', width=w)
                else:
                    name = first_sozais[i-1].get_name()
                    self.sceneblock_list.AppendColumn(name, width=280)
            for i, block in enumerate(self.ctx.get_sceneblocks()):
                self.sceneblock_list.InsertItem(i, str(i))
                for j, sozai in enumerate(block.get_sozais()):
                    self.sceneblock_list.SetItem(i, j+1, sozai.speech_content)
                status = "済" if block.movie_generated else "未"
                self.sceneblock_list.SetItem(i, sozais_num+1, status)
            idx = self.ctx.get_sceneblocks().index(self.ctx.get_current_sceneblock())
            self.sceneblock_list.SetItemBackgroundColour(idx, wx.Colour(135, 206, 250))
            if sozais_num == 0:
                self.remove_btn.SetStatus("Disabled")
                self.edit_btn.Enable(False)
                self.save_btn.Enable(False)
                self.copy_btn.Enable(False)
            else:
                self.remove_btn.SetStatus("Normal")
                self.edit_btn.Enable()
                if len(self.ctx.get_sceneblocks()) > 1:
                    self.save_btn.Enable()
                else:
                    self.save_btn.Enable(False)
                self.copy_btn.Enable()
        else:
            self.remove_btn.SetStatus("Disabled")
            self.edit_btn.Enable(False)
            self.save_btn.Enable(False)

        self.Refresh()

class ScenarioListCtrl(wx.ListCtrl):
    def __init__(self, parent, idx, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, idx, pos, size, style)
        # listmix.CheckListCtrlMixin.__init__(self)
        # listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.EnableCheckBoxes(True)
