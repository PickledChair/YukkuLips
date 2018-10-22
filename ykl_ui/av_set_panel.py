"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx
import os
from pathlib import Path


class AVSetPanel(wx.Panel):
    def __init__(self, parent, idx, context, size=(100, 100)):
        super().__init__(parent, idx, size=size, style=wx.BORDER_SUNKEN)
        self.context = context
        self.audio_list = None
        self.is_silent_check = None
        self.silent_second = None
        self.folder_btn = None
        self.interval_spin = None
        self.blink_choice = None
        self.blink_spin = None
        self.proj_name_text = None
        self.create_widgets()

    def create_widgets(self):
        box_for_all = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(box_for_all)

        audio_box = wx.BoxSizer(wx.VERTICAL)

        audio_lbl = wx.StaticText(self, wx.ID_ANY, label="オーディオファイル：")
        self.audio_list = wx.ListCtrl(self, wx.ID_ANY, size=(250, 80))
        a_btn_box = wx.BoxSizer(wx.HORIZONTAL)
        self.folder_btn = wx.Button(self, wx.ID_ANY, label="フォルダ指定")
        self.Bind(wx.EVT_BUTTON, self.set_audio_dir, id=self.folder_btn.GetId())
        self.is_silent_check = wx.CheckBox(self, wx.ID_ANY, label="無音動画")
        self.Bind(wx.EVT_CHECKBOX, self.is_silent_switcher, id=self.is_silent_check.GetId())
        self.silent_second = wx.SpinCtrlDouble(self, wx.ID_ANY, size=(50, 20))
        self.Bind(wx.EVT_SPINCTRLDOUBLE, self.update_spin_ctrl, id=self.silent_second.GetId())
        self.silent_second.Enable(False)
        ss_lbl = wx.StaticText(self, wx.ID_ANY, label="秒")
        a_btn_box.Add(self.folder_btn, flag=wx.ALL, border=5)
        a_btn_box.Add(self.is_silent_check, flag=wx.TOP, border=5)
        a_btn_box.Add(self.silent_second, flag=wx.LEFT | wx.TOP, border=5)
        a_btn_box.Add(ss_lbl, flag=wx.LEFT | wx.TOP, border=5)

        audio_box.Add(audio_lbl, flag=wx.ALL, border=5)
        audio_box.Add(self.audio_list, flag=wx.LEFT | wx.RIGHT | wx.EXPAND, border=5)
        audio_box.Add(a_btn_box)

        setting_box = wx.BoxSizer(wx.VERTICAL)

        audio_set_lbl = wx.StaticText(self, wx.ID_ANY, label="オーディオ設定：")
        interval_box = wx.BoxSizer(wx.HORIZONTAL)
        interval_lbl1 = wx.StaticText(self, wx.ID_ANY, label="音声間の間隔：")
        self.interval_spin = wx.SpinCtrlDouble(self, wx.ID_ANY, size=(50, 20))
        self.interval_spin.SetValue(self.context.voice_interval)
        self.Bind(wx.EVT_SPINCTRLDOUBLE, self.update_spin_ctrl, id=self.interval_spin.GetId())
        interval_lbl2 = wx.StaticText(self, wx.ID_ANY, label="秒")
        interval_box.Add(interval_lbl1)
        interval_box.Add(self.interval_spin)
        interval_box.Add(interval_lbl2)

        setting_box.Add(audio_set_lbl, flag=wx.ALL, border=5)
        setting_box.Add(interval_box, flag=wx.LEFT, border=20)

        anime_set_lbl = wx.StaticText(self, wx.ID_ANY, label="アニメーション設定：")
        blink_type_box = wx.BoxSizer(wx.HORIZONTAL)
        blink_type_lbl = wx.StaticText(self, wx.ID_ANY, label="目パチのタイプ：")
        self.blink_choice = wx.Choice(self, wx.ID_ANY, choices=self.context.blink_types)
        self.Bind(wx.EVT_CHOICE, self.select_blink_type, id=self.blink_choice.GetId())
        blink_type_box.Add(blink_type_lbl, flag=wx.LEFT, border=20)
        blink_type_box.Add(self.blink_choice)
        blink_box = wx.BoxSizer(wx.HORIZONTAL)
        blink_title = wx.StaticText(self, wx.ID_ANY, label="定期往復：")
        self.blink_spin = wx.SpinCtrlDouble(self, wx.ID_ANY, size=(50, 20))
        self.blink_spin.SetValue(self.context.blink_interval)
        self.Bind(wx.EVT_SPINCTRLDOUBLE, self.update_spin_ctrl, id=self.blink_spin.GetId())
        blink_lbl = wx.StaticText(self, wx.ID_ANY, label="秒ごと")
        blink_box.Add(blink_title, flag=wx.LEFT, border=20)
        blink_box.Add(self.blink_spin)
        blink_box.Add(blink_lbl)

        setting_box.Add(anime_set_lbl, flag=wx.ALL, border=5)
        setting_box.Add(blink_type_box, flag=wx.BOTTOM, border=5)
        setting_box.Add(blink_box)

        project_box = wx.BoxSizer(wx.VERTICAL)

        project_lbl = wx.StaticText(self, wx.ID_ANY, label="プロジェクト：")
        proj_name_box = wx.BoxSizer(wx.HORIZONTAL)
        proj_name_lbl = wx.StaticText(self, wx.ID_ANY, label="プロジェクト名：")
        self.proj_name_text = wx.TextCtrl(self, wx.ID_ANY, size=(160, 20))
        self.Bind(wx.EVT_TEXT, self.update_proj_name, id=self.proj_name_text.GetId())
        proj_name_box.Add(proj_name_lbl, flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=20)
        proj_name_box.Add(self.proj_name_text, flag=wx.EXPAND)
        proj_btn_box = wx.BoxSizer(wx.HORIZONTAL)
        proj_save_btn = wx.Button(self, wx.ID_ANY, label="保存")
        self.Bind(wx.EVT_BUTTON, self.save_as, id=proj_save_btn.GetId())
        proj_write_btn = wx.Button(self, wx.ID_ANY, label="上書き保存")
        self.Bind(wx.EVT_BUTTON, self.save, id=proj_write_btn.GetId())
        proj_open_btn = wx.Button(self, wx.ID_ANY, label="開く")
        self.Bind(wx.EVT_BUTTON, self.open_project, id=proj_open_btn.GetId())
        proj_btn_box.Add(proj_save_btn)
        proj_btn_box.Add(proj_write_btn, flag=wx.LEFT, border=5)
        proj_btn_box.Add(proj_open_btn, flag=wx.LEFT, border=5)

        video_output_btn = wx.Button(self, wx.ID_ANY, label="動画出力")
        self.Bind(wx.EVT_BUTTON, self.output_video, id=video_output_btn.GetId())

        project_box.Add(project_lbl, flag=wx.ALL, border=5)
        project_box.Add(proj_name_box, flag=wx.BOTTOM | wx.EXPAND, border=5)
        project_box.Add(proj_btn_box, flag=wx.LEFT, border=20)
        project_box.Add(width=0, height=20, proportion=1)
        project_box.Add(video_output_btn, flag=wx.ALL | wx.ALIGN_CENTER, border=5)

        box_for_all.Add(audio_box, flag=wx.ALL, border=5)
        box_for_all.Add(setting_box, flag=wx.ALL, border=5)
        box_for_all.Add(project_box, flag=wx.ALL, border=5)
        box_for_all.Layout()

    def update_proj_name(self, event):
        update_name = event.GetString()
        if len(update_name) < 1:
            update_name = "Untitled_Project"
        self.context.proj_name = update_name
        self.GetParent().GetParent().disp_unsaved()

    def is_silent_switcher(self, event):
        if event.GetInt():
            self.context.is_silent_movie = True
            self.silent_second.Enable(True)
            self.folder_btn.Enable(False)
        else:
            self.context.is_silent_movie = False
            self.silent_second.Enable(False)
            self.folder_btn.Enable(True)
        self.GetParent().GetParent().disp_unsaved()

    def update_spin_ctrl(self, event):
        if event.GetId() == self.interval_spin.GetId():
            self.context.voice_interval = event.GetValue()
        elif event.GetId() == self.blink_spin.GetId():
            self.context.blink_interval = event.GetValue()
        elif event.GetId() == self.silent_second.GetId():
            self.context.silent_interval = event.GetValue()
        self.GetParent().GetParent().disp_unsaved()

    def setting_audio_from_context(self):
        self.is_silent_check.SetValue(self.context.is_silent_movie)
        self.silent_second.SetValue(self.context.silent_interval)
        if not self.context.is_silent_movie:
            self.silent_second.Enable(False)
            self.folder_btn.Enable(True)
        else:
            self.silent_second.Enable(True)
            self.folder_btn.Enable(False)
        self.interval_spin.SetValue(self.context.voice_interval)

    def setting_anime_from_context(self):
        self.blink_choice.SetSelection(self.context.blink_types.index(self.context.blink_type))
        self.blink_spin.SetValue(self.context.blink_interval)

    def select_blink_type(self, event):
        self.context.blink_type = self.context.blink_types[event.GetSelection()]
        self.GetParent().GetParent().disp_unsaved()

    def set_audio_dir(self, _event):
        with wx.DirDialog(self, "オーディオフォルダを選択", defaultPath=str(self.context.proj_audio_dir)) as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = dir_dialog.GetPath()
        self.context.proj_audio_dir = Path(pathname)
        self.setting_audio_list()
        self.GetParent().GetParent().disp_unsaved()

    def setting_audio_list(self):
        sound_files = sorted(sorted(self.context.proj_audio_dir.glob("*.wav"))
                             + sorted(self.context.proj_audio_dir.glob("*.WAV")))
        self.audio_list.ClearAll()
        if len(sound_files) > 0:
            for sound_file in sound_files:
                self.audio_list.Append([str(sound_file.name), ])

    def output_video(self, _event):
        if not Path(self.context.ffmpeg_path).exists():
            wx.MessageBox("ffmpeg実行ファイルが指定の場所にありません。\n"
                          "「始めにお読みください.pdf」の説明をご参考に\n"
                          "ffmpeg実行ファイルを配置してください", "エラー", wx.ICON_QUESTION | wx.OK, None)
            return
        if self.context.sozai is None:
            wx.MessageBox("キャラ素材が指定されていません", "エラー", wx.ICON_QUESTION | wx.OK, None)
            return
        with wx.FileDialog(
                self, "動画を保存", "", self.context.proj_name,
                wildcard="MP4 files (*.mp4)|*.mp4", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            if Path(pathname).exists():
                os.remove(pathname)
        self.context.gen_movie(file_path=Path(pathname))

    def save_as(self, _event):
        self.GetParent().GetParent().save_as()

    def save(self, _event):
        self.GetParent().GetParent().save()

    def open_project(self, _event):
        self.GetParent().GetParent().open_project()

    def setting_project_from_context(self):
        self.proj_name_text.SetValue(self.context.proj_name)

    def setting_panel(self):
        self.setting_audio_list()
        self.setting_audio_from_context()
        self.setting_anime_from_context()
        self.setting_project_from_context()
