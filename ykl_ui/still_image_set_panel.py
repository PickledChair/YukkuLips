"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx
from pathlib import Path
from .parts_edit_dialog import PartsEditDialog
from .movie_image_edit_dialog import MovieImageEditDialog


class StillImageSetPanel(wx.Panel):
    def __init__(self, parent, idx, context, size=(100, 100)):
        super().__init__(parent, idx, size=size, style=wx.BORDER_SUNKEN)
        self.context = context
        self.sozai_dir_tctrl = None
        self.parts_li = None
        self.edit_btn = None
        self.bg_choice = None
        self.custom_color = None
        self.cp_ctrl = None
        self.rev_check = None
        self.image_in_movie_info = None
        self.image_in_movie_edit_btn = None

        self.create_widgets()

    def create_widgets(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(vbox)

        chara_lbl = wx.StaticText(self, wx.ID_ANY, label="キャラ素材選択：")

        sozai_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.sozai_dir_tctrl = wx.TextCtrl(self, wx.ID_ANY, size=(200, 10), style=wx.TE_READONLY)
        sozai_sel_btn = wx.Button(self, wx.ID_ANY, label="素材選択")
        self.Bind(wx.EVT_BUTTON, self.select_sozai_dir, id=sozai_sel_btn.GetId())
        sozai_hbox.Add(self.sozai_dir_tctrl, proportion=1, flag=wx.EXPAND)
        sozai_hbox.Add(sozai_sel_btn, proportion=0, flag=wx.LEFT, border=5)

        vbox.Add(chara_lbl, flag=wx.ALL, border=5)
        vbox.Add(sozai_hbox, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=5)

        parts_lbl = wx.StaticText(self, wx.ID_ANY, label="パーツ画像選択：")

        parts_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.parts_li = wx.ListCtrl(self, wx.ID_ANY, size=(200, 120), style=wx.LC_REPORT)
        self.parts_li.InsertColumn(0, "パーツ", width=60)
        self.parts_li.InsertColumn(1, "選択画像", width=140)
        self.edit_btn = wx.Button(self, wx.ID_ANY, label="編集")
        self.Bind(wx.EVT_BUTTON, self.show_parts_edit_window, id=self.edit_btn.GetId())
        self.edit_btn.Enable(False)
        parts_hbox.Add(self.parts_li)
        parts_hbox.Add(self.edit_btn, flag=wx.LEFT | wx.ALIGN_BOTTOM, border=5)

        vbox.Add(parts_lbl, flag=wx.ALL, border=5)
        vbox.Add(parts_hbox, flag=wx.LEFT | wx.BOTTOM | wx.RIGHT, border=5)

        bg_lbl = wx.StaticText(self, wx.ID_ANY, label="背景色：")
        self.bg_choice = wx.Choice(self, wx.ID_ANY, choices=[bg_color.name for bg_color in self.context.bg_colors])
        self.Bind(wx.EVT_CHOICE, self.select_bg_color, id=self.bg_choice.GetId())
        cc_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.custom_color = wx.CheckBox(self, wx.ID_ANY, label="その他の背景色")
        self.Bind(wx.EVT_CHECKBOX, self.custom_flag_switcher, id=self.custom_color.GetId())
        self.cp_ctrl = wx.ColourPickerCtrl(self, wx.ID_ANY, colour=wx.WHITE, size=(40, 40))
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.select_custom_color, id=self.cp_ctrl.GetId())
        self.cp_ctrl.Enable(False)
        cc_hbox.Add(self.custom_color, flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=15)
        cc_hbox.Add(self.cp_ctrl, flag=wx.LEFT, border=5)

        vbox.Add(bg_lbl, flag=wx.ALL, border=5)
        vbox.Add(self.bg_choice, flag=wx.LEFT, border=20)
        vbox.Add(cc_hbox, flag=wx.LEFT | wx.TOP, border=5)

        other_set = wx.StaticText(self, wx.ID_ANY, label="その他の画像設定：")
        self.rev_check = wx.CheckBox(self, wx.ID_ANY, label="左右反転")
        self.Bind(wx.EVT_CHECKBOX, self.switch_rev, id=self.rev_check.GetId())

        vbox.Add(other_set, flag=wx.ALL, border=5)
        vbox.Add(self.rev_check, flag=wx.LEFT, border=20)

        save_image_btn = wx.Button(self, wx.ID_ANY, "静画保存")
        self.Bind(wx.EVT_BUTTON, self.save_still_image, id=save_image_btn.GetId())
        vbox.Add(save_image_btn, flag=wx.ALL | wx.ALIGN_CENTER, border=5)

        image_in_movie = wx.StaticText(self, wx.ID_ANY, label="動画の画像配置設定：")
        movie_info_box = wx.BoxSizer(wx.HORIZONTAL)
        self.image_in_movie_info = wx.ListCtrl(self, wx.ID_ANY, size=(200, 120), style=wx.LC_REPORT)
        self.image_in_movie_info.InsertColumn(0, "設定", width=70)
        self.image_in_movie_info.InsertColumn(1, "値", width=130)
        self.image_in_movie_info.Append(["解像度", self.context.movie_size.name])
        self.image_in_movie_info.Append(["素材位置", str(self.context.sozai_pos)])
        self.image_in_movie_info.Append(["素材倍率", str(self.context.sozai_scale)])
        self.image_in_movie_info.Append(["参考背景", "指定なし"])
        self.image_in_movie_edit_btn = wx.Button(self, wx.ID_ANY, label="編集")
        self.image_in_movie_edit_btn.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.movie_image_edit, id=self.image_in_movie_edit_btn.GetId())
        movie_info_box.Add(self.image_in_movie_info)
        movie_info_box.Add(self.image_in_movie_edit_btn, flag=wx.LEFT | wx.ALIGN_BOTTOM, border=5)

        vbox.Add(image_in_movie, flag=wx.LEFT, border=5)
        vbox.Add(movie_info_box, flag=wx.ALL, border=5)

        vbox.Layout()

    def select_sozai_dir(self, _event):
        with wx.DirDialog(self, "キャラ素材フォルダを選択", defaultPath=str(self.context.sozai_dir)) as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = dir_dialog.GetPath()
        self.context.set_sozai_dir(Path(pathname))

        self.setting_parts_list(Path(pathname).name)

        # 他のパネルのウィジェットに対する変更
        self.GetParent().GetParent().update_image_disp()
        self.GetParent().GetParent().disp_unsaved()

    def setting_parts_list(self, sozai_name):
        if self.parts_li.GetItemCount() > 0:
            self.parts_li.ClearAll()
            self.parts_li.InsertColumn(0, "パーツ", width=60)
            self.parts_li.InsertColumn(1, "選択画像", width=140)

        # このパネルのウィジェットに対する変更
        self.sozai_dir_tctrl.SetValue(sozai_name)
        for i, part in enumerate(self.context.sozai.part_dirs):
            if len(self.context.current_images_dic) > 0:
                if len(self.context.current_images_dic[part.name]) < 1:
                    self.parts_li.Append([part.name, "未選択"])
                else:
                    disp_str = ""
                    for path in self.context.current_images_dic[part.name]:
                        if disp_str == "":
                            disp_str += str(path.name)
                        else:
                            disp_str += ", " + str(path.name)
                    self.parts_li.Append([part.name, disp_str])
        if len(self.context.sozai.part_dirs) < 1:
            self.edit_btn.Enable(False)
            self.image_in_movie_edit_btn.Enable(False)
        else:
            self.edit_btn.Enable(True)
            self.image_in_movie_edit_btn.Enable(True)

    def setting_bg_color_choice(self):
        if self.context.bg_color in self.context.bg_colors:
            self.bg_choice.Enable(True)
            self.bg_choice.SetSelection(list(self.context.bg_colors).index(self.context.bg_color))
            self.custom_color.SetValue(False)
            self.cp_ctrl.Enable(False)
        else:
            self.bg_choice.Enable(False)
            self.custom_color.SetValue(True)
            self.cp_ctrl.Enable(True)
            self.cp_ctrl.SetColour(wx.Colour(*self.context.bg_color.color_tuple))

    def setting_rev_check(self):
        self.rev_check.SetValue(self.context.rev_flag)

    def setting_movie_info(self):
        self.image_in_movie_info.SetItem(0, 1, self.context.movie_size.name)
        self.image_in_movie_info.SetItem(1, 1, str(self.context.sozai_pos))
        self.image_in_movie_info.SetItem(2, 1, str(self.context.sozai_scale))
        if self.context.ref_background is None:
            self.image_in_movie_info.SetItem(3, 1, "指定なし")
        else:
            self.image_in_movie_info.SetItem(3, 1, self.context.ref_background.name)

    def select_bg_color(self, event):
        self.context.bg_color = self.context.bg_colors[event.GetSelection()]
        self.GetParent().GetParent().update_image_disp()
        self.GetParent().GetParent().disp_unsaved()

    def custom_flag_switcher(self, event):
        if event.GetInt():
            self.bg_choice.Enable(False)
            self.cp_ctrl.Enable(True)
            self.context.set_bg_color(self.cp_ctrl.GetColour().Get(includeAlpha=True))
        else:
            self.bg_choice.Enable(True)
            self.cp_ctrl.Enable(False)
            self.context.bg_color = self.context.bg_colors[self.bg_choice.GetSelection()]
        self.GetParent().GetParent().update_image_disp()
        self.GetParent().GetParent().disp_unsaved()

    def select_custom_color(self, event):
        self.context.set_bg_color(event.GetColour().Get(includeAlpha=True))
        self.GetParent().GetParent().update_image_disp()
        self.GetParent().GetParent().disp_unsaved()

    def switch_rev(self, event):
        if event.GetInt():
            self.context.rev_flag = True
        else:
            self.context.rev_flag = False
        self.GetParent().GetParent().update_image_disp()
        self.GetParent().GetParent().disp_unsaved()

    def save_still_image(self, _event):
        with wx.FileDialog(
                self, "画像を保存", "", self.context.proj_name,
                wildcard="PNG files (*.png)|*.png", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            self.context.save_still_image(pathname)

    def show_parts_edit_window(self, _event):
        PartsEditDialog(self, wx.ID_ANY, "パーツ選択ダイアログ", self.context)

    def update_image_context(self):
        self.GetParent().GetParent().update_image_disp()
        self.update_parts_li()
        self.GetParent().GetParent().disp_unsaved()

    def update_parts_li(self):
        for i, part in enumerate(self.context.sozai.part_dirs):
            path_list = self.context.current_images_dic[part.name]
            if len(path_list) < 1:
                name = "未選択"
            else:
                name = ""
                for path in path_list:
                    if name == "":
                        name += path.name
                    else:
                        name += ", " + path.name
            self.parts_li.SetItem(i, 1, name)

    def movie_image_edit(self, _event):
        MovieImageEditDialog(self, wx.ID_ANY, "動画の画像配置設定", self.context)

    def setting_panel(self, sozai_name):
        self.setting_parts_list(sozai_name)
        self.setting_bg_color_choice()
        self.setting_rev_check()
        self.setting_movie_info()
