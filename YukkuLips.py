"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx
import os
import sys
from pathlib import Path
from copy import copy
from ykl_core.ykl_context import YKLContext
from ykl_ui.still_image_set_panel import StillImageSetPanel
from ykl_ui.image_disp_panel import ImageDispPanel
from ykl_ui.av_set_panel import AVSetPanel
from ykl_core.ykl_project import YKLProjectBuilder
import wx.adv as ADV


class YKLAppWindow(wx.Frame):
    def __init__(self, parent, idx, title, size=(800, 670)):
        super().__init__(parent, idx, title, size=size)
        self.context = YKLContext()
        self.image_disp = None
        self.still_set = None
        self.av_set = None
        self.create_widgets()
        self.SetTitle("YukkuLips: " + self.context.proj_name + "*")
        self.create_menu()
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Centre()
        self.Show()

    def create_widgets(self):
        panel = wx.Panel(self, wx.ID_ANY)
        vbox = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(vbox)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.image_disp = ImageDispPanel(panel, wx.ID_ANY, self.context, size=(500, 520))
        self.still_set = StillImageSetPanel(panel, wx.ID_ANY, self.context, size=(300, 520))

        # proportionは、0がサイズ変更不可、1が変更可能（伸縮自在）を意味する
        hbox.Add(self.image_disp, proportion=1, flag=wx.EXPAND)
        hbox.Add(self.still_set, proportion=0, flag=wx.EXPAND)

        self.av_set = AVSetPanel(panel, wx.ID_ANY, self.context, size=(800, 150))

        vbox.Add(hbox, proportion=1, flag=wx.EXPAND)
        vbox.Add(self.av_set, proportion=0, flag=wx.EXPAND)

        hbox.Layout()
        vbox.Layout()

    def create_menu(self):
        menubar = wx.MenuBar()
        file = wx.Menu()

        open_item = wx.MenuItem(file, wx.ID_OPEN, "プロジェクトを開く\tCtrl+O")
        self.Bind(wx.EVT_MENU, self.on_open, id=open_item.GetId())
        file.Append(open_item)

        file.AppendSeparator()

        save = wx.MenuItem(file, wx.ID_SAVE, "プロジェクトを上書き保存\tCtrl+S")
        self.Bind(wx.EVT_MENU, self.on_save, id=save.GetId())
        file.Append(save)

        save_as = wx.MenuItem(file, wx.ID_SAVEAS, "プロジェクトに名前を付けて保存\tShift+Ctrl+S")
        self.Bind(wx.EVT_MENU, self.on_save_as, id=save_as.GetId())
        file.Append(save_as)

        about = wx.MenuItem(file, wx.ID_ABOUT, "&YukkuLipsについて")
        self.Bind(wx.EVT_MENU, self.show_about_dialog, id=about.GetId())
        file.Append(about)

        close = wx.MenuItem(file, wx.ID_EXIT, "&YukkuLipsを終了")
        self.Bind(wx.EVT_MENU, self.on_close, id=close.GetId())
        file.Append(close)

        menubar.Append(file, "&ファイル")
        self.SetMenuBar(menubar)

    def update_image_disp(self):
        if (self.context.ui_image_path / "ui_image.png").exists():
            os.remove(self.context.ui_image_path / "ui_image.png")
        image = self.context.integrate_images(self.context.base_size)
        self.context.save_ui_image(image)
        self.image_disp.update_panel()
        self.Refresh()

    def on_close(self, _event):
        if not self.context.save_flag:
            if wx.MessageBox("プロジェクトが保存されていません。終了しますか？",
                             "確認", wx.ICON_QUESTION | wx.YES_NO,
                             self) == wx.NO:
                return
        self.clear_cache()
        self.Destroy()

    def on_open(self, _event):
        self.open_project()

    def on_save(self, _event):
        self.save()

    def on_save_as(self, _event):
        self.save_as()

    def clear_cache(self):
        if (self.context.ui_image_path / "ui_image.png").exists():
            os.remove(self.context.ui_image_path / "ui_image.png")
        while (self.context.ui_image_path / "ui_image.png").exists():
            continue
        self.context.animation_image_path.rmdir()
        self.context.audio_path.rmdir()
        parent_dir = self.context.ui_image_path.parent
        self.context.ui_image_path.rmdir()
        # 子ディレクトリの削除が間に合わなかったのか、yukkulips_cacheディレクトリの削除に失敗することがあるので、
        # 一応待機のためのループを設置した
        while self.context.ui_image_path.exists() and self.context.animation_image_path.exists()\
                and self.context.audio_path.exists():
            continue
        parent_dir.rmdir()

    def save_as(self):
        with wx.FileDialog(
                self, "プロジェクトを保存", "", self.context.proj_name,
                wildcard="JSON files (*.json)|*.json", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
        self.build_project()
        self.context.project.save_as(pathname)
        self.context.save_flag = True
        self.SetTitle("YukkuLips: " + self.context.proj_name)

    def save(self):
        if self.context.project.contents["Project Name"] == ""\
                or self.context.project.contents["Project Name"] != self.context.proj_name:
            self.save_as()
        else:
            self.build_project()
            self.context.project.save()
            self.context.save_flag = True
            self.SetTitle("YukkuLips: " + self.context.proj_name)

    def build_project(self):
        builder = YKLProjectBuilder()
        builder.set_project_name(self.context.proj_name)
        builder.set_sozai_dir(str(self.context.sozai_dir))
        builder.set_current_images(self.context.current_images_dic)
        builder.set_bg_color(self.context.bg_color)
        builder.set_mirror_flag(self.context.rev_flag)
        builder.set_base_size(self.context.base_size)
        builder.set_audio_dir(str(self.context.proj_audio_dir))
        builder.set_is_silent(self.context.is_silent_movie)
        builder.set_silent_interval(self.context.silent_interval)
        builder.set_voice_interval(self.context.voice_interval)
        builder.set_blink_interval(self.context.blink_interval)
        builder.set_blink_type(list(self.context.blink_types).index(self.context.blink_type))
        builder.set_movie_size(self.context.movie_size)
        builder.set_sozai_pos(self.context.sozai_pos)
        builder.set_sozai_scale(self.context.sozai_scale)
        builder.set_bg_ref(self.context.ref_background)
        project = builder.build()

        location = self.context.project.location
        self.context.project = project
        self.context.project.location = location

    def open_project(self):
        with wx.FileDialog(self, "プロジェクトを開く", wildcard="JSON files (*.json)|*.json",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
        project_backup = copy(self.context.project)
        if not self.context.project.open(pathname):
            wx.MessageBox("サポートされていないプロジェクトバージョンです", "エラー", wx.ICON_QUESTION | wx.OK, None)
            return
        paths = [Path(self.context.project.contents["Sozai Directory"]),
                 Path(self.context.project.contents["Audio Directory"])]
        not_exists = []
        for path in paths:
            if not path.exists():
                not_exists.append(path)
        if len(not_exists) > 0:
            not_exists_text = ""
            for path in not_exists:
                not_exists_text += str(path) + "\n"
            wx.MessageBox(not_exists_text + "が見つかりませんでした",
                          "エラー", wx.ICON_QUESTION | wx.OK, self)
            self.context.project = project_backup
            return
        self.context.update_context_from_project()
        self.still_set.setting_panel(self.context.sozai.base_dir.name)
        self.av_set.setting_panel()

        self.update_image_disp()
        self.context.save_flag = True
        self.SetTitle("YukkuLips: " + self.context.proj_name)

    @staticmethod
    def show_about_dialog(_event):
        info = ADV.AboutDialogInfo()
        info.SetName("YukkuLips")
        info.SetVersion("0.0.1")
        info.SetDescription(
            "クロマキー合成用キャラ素材動画生成アプリケーション\n\n"       
            "スペシャルサンクス\n"
            "ズーズ氏 (http://www.nicotalk.com/charasozai.html)\n"
            "きつね氏 (http://seiga.nicovideo.jp/seiga/im4817713)\n\n"
            "YukkuLips Repository: --")
        info.SetCopyright("(c) 2018 SuitCase <ubatamamoon@gmail.com>")
        info.SetLicence(__doc__)

        ADV.AboutBox(info)

    def disp_unsaved(self):
        self.SetTitle("YukkuLips: " + self.context.proj_name + "*")
        self.context.save_flag = False


class YKLApp(wx.App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def OnInit(self):
        self.SetAppName("YukkuLips")
        YKLAppWindow(None, wx.ID_ANY, "YukkuLips")

        return True


if __name__ == "__main__":
    app = YKLApp()
    app.MainLoop()
