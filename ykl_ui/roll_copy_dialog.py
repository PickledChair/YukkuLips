"""
YukkuLips

Copyright (c) 2018 - 2020 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import shutil
import subprocess
from pathlib import Path

import wx

from media_utility.image_tool import get_thumbnail


class YKLRollingCopyDialog(wx.Dialog):
    def __init__(self, parent, ctx):
        super().__init__(parent, title="コピーダイアログ", size=(580, 390))
        self.ctx = ctx
        idx = self.ctx.get_sceneblocks().index(self.ctx.get_current_sceneblock())
        self.block_idx = idx
        self.MAX_BLOCK_IDX = len(self.ctx.get_sceneblocks()) - 1
        self.chara_idx = 0
        self.MAX_CHARA_IDX = len(self.ctx.get_sceneblocks()[0].get_sozais()) - 1

        self.temp_dir = self.ctx.get_project_path() / "temp"
        if not self.temp_dir.exists():
            self.temp_dir.mkdir()

        box = wx.BoxSizer(wx.VERTICAL)
        self.content_panel = CopyContentPanel(self, wx.ID_ANY, self.get_current_chara(), self.block_idx, self.temp_dir, size=(580, 300))
        box.Add(self.content_panel)

        self.next_check = wx.CheckBox(self, wx.ID_ANY, "コピー操作時に次のセリフに移る")
        self.next_check.SetValue(self.ctx.app_setting.setting_dict["CopyDialog Next Check"])
        self.Bind(wx.EVT_CHECKBOX, self.OnCheck, id=self.next_check.GetId())
        box.Add(self.next_check, flag=wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, border=10)

        btns = wx.BoxSizer(wx.HORIZONTAL)
        myv_btn = wx.Button(self, wx.ID_ANY, "MYukkuriVoiceに受け渡す")
        self.Bind(wx.EVT_BUTTON, self.OnMyvBtnClick, id=myv_btn.GetId())
        btns.Add(myv_btn, flag=wx.ALL, border=5)
        copy_btn = wx.Button(self, wx.ID_ANY, "コピー")
        self.Bind(wx.EVT_BUTTON, self.OnCopyBtnClick, id=copy_btn.GetId())
        btns.Add(copy_btn, flag=wx.ALL, border=5)
        prev_btn = wx.Button(self, wx.ID_ANY, "戻る")
        self.Bind(wx.EVT_BUTTON, self.OnPrevBtnClick, id=prev_btn.GetId())
        btns.Add(prev_btn, flag=wx.ALL, border=5)
        next_btn = wx.Button(self, wx.ID_ANY, "進む")
        self.Bind(wx.EVT_BUTTON, self.OnNextBtnClick, id=next_btn.GetId())
        btns.Add(next_btn, flag=wx.ALL, border=5)
        btns.Layout()

        box.Add(btns, 0, flag=wx.RIGHT | wx.ALIGN_RIGHT, border=5)

        box.Layout()

        self.SetSizer(box)

        if self.get_current_chara().speech_content == "":
            self.content_increment()
        else:
            self.save_temp_txt()

        self.Bind(wx.EVT_CLOSE, self.OnClose, id=self.GetId())

    def OnCheck(self, event):
        self.ctx.app_setting.setting_dict["CopyDialog Next Check"] = self.next_check.GetValue()
        self.ctx.app_setting.save()

    def OnPrevBtnClick(self, event):
        self.content_decrement()

    def OnNextBtnClick(self, event):
        self.content_increment()

    def OnCopyBtnClick(self, event):
        self.content_panel.copy_speech_content()
        # next_checkフラグが立っている時はcontent_incrementを呼ぶ
        if self.next_check.IsChecked():
            self.content_increment()

    def OnMyvBtnClick(self, event):
        self.send_to_myukkurivoice()
        if self.next_check.IsChecked():
            self.content_increment()

    def send_to_myukkurivoice(self):
        txt_path = self.temp_dir / "serifu.txt"
        try:
            p = subprocess.Popen(["open", "-a", "MYukkuriVoice", str(txt_path)])
            p.wait()
        except OSError:
            wx.MessageBox("MYukkuriVoice.appはアプリケーションフォルダ内に"
                          "ある必要があります",
                          "MYukkuriVoiceを開けませんでした",
                          wx.ICON_EXCLAMATION | wx.OK)

    def OnClose(self, event):
        self.ctx.unsaved_check()
        if self.temp_dir.exists():
            shutil.rmtree(str(self.temp_dir))
        event.Skip()

    def get_current_chara(self):
        return self.ctx.get_sceneblocks()[self.block_idx].get_sozais()[self.chara_idx]

    def save_temp_txt(self):
        txt_path = self.temp_dir / "serifu.txt"
        with txt_path.open('w') as f:
            f.write(self.get_current_chara().speech_content)

    def content_increment(self):
        def increment():
            if self.chara_idx == self.MAX_CHARA_IDX:
                self.chara_idx = 0
                if self.block_idx == self.MAX_BLOCK_IDX:
                    self.block_idx = 0
                else:
                    self.block_idx += 1
            else:
                self.chara_idx += 1
        increment()
        while self.get_current_chara().speech_content == "":
            increment()
        # 現在のキャラ素材のセリフを表示領域にセットする
        self.content_panel.set_charasozai(self.get_current_chara(), self.block_idx)
        # また、一時ファイルにセリフを保存する
        self.save_temp_txt()

    def content_decrement(self):
        def decrement():
            if self.chara_idx == 0:
                self.chara_idx = self.MAX_CHARA_IDX
                if self.block_idx == 0:
                    self.block_idx = self.MAX_BLOCK_IDX
                else:
                    self.block_idx -= 1
            else:
                self.chara_idx -= 1
        decrement()
        while self.get_current_chara().speech_content == "":
            decrement()
        # 現在のキャラ素材のセリフを表示領域にセットする
        self.content_panel.set_charasozai(self.get_current_chara(), self.block_idx)
        # また、一時ファイルにセリフを保存する
        self.save_temp_txt()


class CopyContentPanel(wx.Panel):
    def __init__(self, parent, idx, chara, block_num, temp_dir, size):
        super().__init__(parent, idx, size=size)
        self.chara = chara
        self.temp_dir = temp_dir
        box = wx.BoxSizer(wx.VERTICAL)
        image = chara.get_image()
        image = get_thumbnail(image, size=200)
        bmp = wx.Bitmap.FromBufferRGBA(*image.size, image.tobytes())
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.sbmp = wx.StaticBitmap(self, wx.ID_ANY, bmp)
        hbox.Add(self.sbmp, flag=wx.ALL, border=10)

        txt_content_box = wx.BoxSizer(wx.VERTICAL)
        name_box = wx.BoxSizer(wx.HORIZONTAL)
        self.name_tctrl = wx.TextCtrl(self, wx.ID_ANY, chara.get_name(), size=(100, -1))
        self.name_tctrl.SetEditable(False)
        name_box.Add(self.name_tctrl, flag=wx.ALIGN_CENTER_VERTICAL)
        name_stlbl = wx.StaticText(self, wx.ID_ANY, "＠シーンブロック")
        name_box.Add(name_stlbl, flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.blocknum_tctrl = wx.TextCtrl(self, wx.ID_ANY, str(block_num), size=(60, -1))
        self.blocknum_tctrl.SetEditable(False)
        name_box.Add(self.blocknum_tctrl, flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=10)
        txt_content_box.Add(name_box, flag=wx.ALL, border=10)
        self.serifu_tctrl = wx.TextCtrl(self, wx.ID_ANY, chara.speech_content, size=(300, 180))
        txt_content_box.Add(self.serifu_tctrl, flag=wx.LEFT | wx.RIGHT | wx.EXPAND, border=10)
        hbox.Add(txt_content_box, flag=wx.TOP | wx.BOTTOM | wx.EXPAND, border=10)
        box.Add(hbox, flag=wx.EXPAND)

        path_box = wx.BoxSizer(wx.HORIZONTAL)
        path_lbl = wx.StaticText(self, wx.ID_ANY, "音声ファイルパス：")
        path_box.Add(path_lbl, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.path_tctrl = wx.TextCtrl(self, wx.ID_ANY, chara.anime_audio_path, size=(350, -1))
        path_droptarget = PathDropTarget(self.path_tctrl)
        self.path_tctrl.SetDropTarget(path_droptarget)
        self.Bind(wx.EVT_TEXT, self.OnPathChange, id=self.path_tctrl.GetId())
        path_box.Add(self.path_tctrl, flag=wx.TOP | wx.BOTTOM, border=10)
        box.Add(path_box, flag=wx.ALIGN_CENTER_HORIZONTAL)
        box.Layout()
        self.SetSizer(box)

    def OnPathChange(self, event):
        path = self.path_tctrl.GetValue()
        if Path(path).exists():
            if path != self.chara.anime_audio_path:
                self.chara.anime_audio_path = path
                self.chara.movie_audio_path = path

    def set_charasozai(self, chara, block_num):
        self.chara = chara
        image = chara.get_image()
        image = get_thumbnail(image, size=200)
        bmp = wx.Bitmap.FromBufferRGBA(*image.size, image.tobytes())
        self.sbmp.SetBitmap(bmp)
        self.name_tctrl.SetValue(chara.get_name())
        self.blocknum_tctrl.SetValue(str(block_num))
        self.serifu_tctrl.SetValue(chara.speech_content)
        self.path_tctrl.SetValue(chara.anime_audio_path)
        self.Refresh()

    # def get_speech_content(self):
    #     return self.serifu_tctrl.GetValue()

    def copy_speech_content(self):
        # フォーカスしないとSelectAllメソッドが機能しない
        self.serifu_tctrl.SetFocus()
        # 選択しないとCopyメソッドが機能しない
        self.serifu_tctrl.SelectAll()
        self.serifu_tctrl.Copy()


class PathDropTarget(wx.FileDropTarget):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        if filenames[0][-4:].lower() in [".mp3", ".wav"]:
            self.window.SetValue(filenames[0])
        return True

