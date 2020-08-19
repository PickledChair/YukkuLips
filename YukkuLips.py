"""
YukkuLips

Copyright (c) 2018 - 2020 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

from copy import deepcopy
from pathlib import Path
import sys
import webbrowser

import wx
import wx.adv as ADV

from ykl_core.ykl_context import YKLContext

from ykl_ui.layout_panel import YKLLayoutPanel, EVT_YKL_LAYOUT_UPDATE
from ykl_ui.sozai_panel import YKLSozaiPanel, EVT_YKL_SOZAI_UPDATE
from ykl_ui.scenario_panel import YKLScenarioPanel, EVT_YKL_SCENARIO_UPDATE
from ykl_ui.welcome_dialog import YKLWelcomeDialog
from ykl_ui.create_pro_dialog import YKLCreateProjectDialog
from ykl_ui.project_edit_dialog import YKLProjectEditDialog
from ykl_ui.script_edit_dialog import YKLScriptEditDialog
from ykl_ui.import_audio_dialog import YKLImportAudioDialog


VERSION = "0.2.2"

YKL_REPOSITORY_URL = "https://github.com/PickledChair/YukkuLips"


class YKLAppWindow(wx.Frame):
    def __init__(self, parent, idx, title,  size=(1000, 680)):
        super().__init__(parent, idx, title, size=size)
        self.ctx = None
        self.ctx_created = False

        self.create_widgets()
        self.create_menu()

        self.Centre()
        self.Show()

        self.img_dir = Path.cwd() / 'images'
        if getattr(sys, 'frozen', False):
            # frozen は PyInstaller でこのスクリプトが固められた時に sys に追加される属性
            # frozen が見つからない時は素の Python で実行している時なので False を返す
            bundle_dir = sys._MEIPASS
            self.img_dir = Path(bundle_dir) / "images"

        previous = wx.NewIdRef()
        # history = wx.NewIdRef()
        new_pro = wx.NewIdRef()

        with YKLWelcomeDialog(self, [previous, new_pro], self.img_dir) as w_dialog:
            ret_id = w_dialog.ShowModal()
            if ret_id == previous:
                with wx.DirDialog(self, 'プロジェクトフォルダを選択') as dir_dialog:
                    if dir_dialog.ShowModal() == wx.ID_CANCEL:
                        self.Close()
                        return
                    path = dir_dialog.GetPath()
                    if not (Path(path) / "project.json").exists():
                        wx.MessageBox("指定フォルダ内にproject.jsonがありません\n"
                                      "YukkuLipsを終了します", "確認",
                                      wx.ICON_EXCLAMATION | wx.OK)
                        self.Close()
            # elif ret_id == history:
            #     print('history')
            elif ret_id == new_pro:
                with YKLCreateProjectDialog(self) as create_dialog:
                    if create_dialog.ShowModal() == wx.ID_CANCEL:
                        self.Close()
                        return
                    path = create_dialog.get_path()
            else:
                self.Close()
                return

        self.ctx = YKLContext(path)
        self.ctx_created = True
        self.scenario_panel.set_context(self.ctx)
        self.sozai_panel.set_context(self.ctx)
        self.layout_panel.set_context(self.ctx)
        self.update_title()

        # self.create_widgets()
        # self.create_menu()
        if (Path(path) / "project.json").exists():
            self.ctx.open_project()
            self.update_ui()

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(EVT_YKL_LAYOUT_UPDATE, self.OnUpdate)
        self.Bind(EVT_YKL_SOZAI_UPDATE, self.OnUpdate)
        self.Bind(EVT_YKL_SCENARIO_UPDATE, self.OnUpdate)

        # self.Show()

    def create_widgets(self):
        self.total_rect = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3DSASH | wx.SP_LIVE_UPDATE)
        self.total_rect.SetMinimumPaneSize(100)

        self.upper_rect = wx.SplitterWindow(self.total_rect, wx.ID_ANY, style=wx.SP_3DSASH | wx.SP_LIVE_UPDATE)
        self.upper_rect.SetMinimumPaneSize(100)

        self.layout_panel = YKLLayoutPanel(self.upper_rect, wx.ID_ANY, self.ctx)
        self.sozai_panel = YKLSozaiPanel(self.upper_rect, wx.ID_ANY, self.ctx)

        self.upper_rect.SplitVertically(self.layout_panel, self.sozai_panel, sashPosition=700)

        self.scenario_panel = YKLScenarioPanel(self.total_rect, wx.ID_ANY, self.ctx)

        self.total_rect.SplitHorizontally(self.upper_rect, self.scenario_panel, sashPosition=380)

    def create_menu(self):
        menubar = wx.MenuBar()
        file_ = wx.Menu()

        new_item = wx.MenuItem(file_, wx.ID_NEW, "プロジェクトを新規作成\tCtrl+N")
        self.Bind(wx.EVT_MENU, self.OnNewProject, id=new_item.GetId())
        file_.Append(new_item)

        open_item = wx.MenuItem(file_, wx.ID_OPEN, "プロジェクトを開く\tCtrl+O")
        self.Bind(wx.EVT_MENU, self.OnOpen, id=open_item.GetId())
        file_.Append(open_item)

        file_.AppendSeparator()

        pro_set = wx.MenuItem(file_, wx.ID_ANY, "プロジェクト設定\tCtrl+P")
        self.Bind(wx.EVT_MENU, self.OnProjectSetting, id=pro_set.GetId())
        file_.Append(pro_set)

        file_.AppendSeparator()

        save = wx.MenuItem(file_, wx.ID_SAVE, "プロジェクトを保存\tCtrl+S")
        self.Bind(wx.EVT_MENU, self.OnSave, id=save.GetId())
        file_.Append(save)

        file_.AppendSeparator()

        self.audio_imp = wx.MenuItem(file_, wx.ID_ANY, "音声ファイルパスをインポート\tCtrl+I")
        self.audio_imp.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnImportAudio, id=self.audio_imp.GetId())
        file_.Append(self.audio_imp)

        about = wx.MenuItem(file_, wx.ID_ABOUT, "&YukkuLipsについて")
        self.Bind(wx.EVT_MENU, self.ShowAboutDialog, id=about.GetId())
        file_.Append(about)

        close = wx.MenuItem(file_, wx.ID_EXIT, "&YukkuLipsを終了")
        self.Bind(wx.EVT_MENU, self.OnMenuClose, id=close.GetId())
        file_.Append(close)

        edit = wx.Menu()

        self.scenario = wx.MenuItem(edit, wx.ID_ANY, "シナリオ編集\tCtrl+D")
        self.scenario.Enable(False)
        self.Bind(wx.EVT_MENU, self.OnScenarioEdit, id=self.scenario.GetId())
        edit.Append(self.scenario)

        help_ = wx.Menu()

        to_repo = wx.MenuItem(help_, wx.ID_ANY, "YukkuLips Repository を開く")
        self.Bind(wx.EVT_MENU, self.OnOpenRepoURL, id=to_repo.GetId())
        help_.Append(to_repo)

        menubar.Append(file_, "&ファイル")
        menubar.Append(edit, "&編集")
        menubar.Append(help_, "&Help")
        self.SetMenuBar(menubar)

    def OnOpenRepoURL(self, event):
        webbrowser.open(YKL_REPOSITORY_URL)

    def OnProjectSetting(self, event):
        with YKLProjectEditDialog(self, self.ctx) as e_dialog:
            ret = e_dialog.ShowModal()
            if not (ret == wx.ID_CANCEL or ret == wx.ID_CLOSE):
                # scene_imageの更新はcontextのsetterによって行われている
                self.update_ui()

    def OnScenarioEdit(self, event):
        with YKLScriptEditDialog(self, self.ctx) as e_dialog:
            # ret = e_dialog.ShowModal()
            # if not (ret == wx.ID_CANCEL or ret == wx.ID_CLOSE):
            e_dialog.ShowModal()
            # scene_imageの更新はcontextのsetterによって行われている
            self.update_ui()

    def OnImportAudio(self, event):
        with YKLImportAudioDialog(self, self.ctx) as e_dialog:
            e_dialog.ShowModal()
            self.update_ui()

    def OnClose(self, event):
        if self.close_cancel():
            return
        self.Destroy()
        event.Skip()

    def OnMenuClose(self, event):
        self.Close()

    def close_cancel(self):
        if self.ctx_created:
            if not self.ctx.project_saved():
                if wx.MessageBox("プロジェクトが保存されていません。終了しますか？",
                             "確認", wx.ICON_QUESTION | wx.YES_NO,
                             self) == wx.NO:
                    return True
        return False

    def OnOpen(self, event):
        if not self.ctx.project_saved():
            if wx.MessageBox("保存していない内容は失われます。続行しますか？",
                            "確認", wx.ICON_QUESTION | wx.YES_NO,
                            self) == wx.NO:
                return
        with wx.DirDialog(self, 'プロジェクトフォルダを選択') as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_CANCEL:
                self.Close()
            path = dir_dialog.GetPath()
            if not (Path(path) / "project.json").exists():
                wx.MessageBox("指定フォルダ内にproject.jsonがありません",
                              "確認", wx.ICON_EXCLAMATION | wx.OK)
                return
        self.ctx = YKLContext(path)
        self.ctx.open_project()
        # 各UIパネルに関連づけられているコンテキストオブジェクトを更新
        self.scenario_panel.set_context(self.ctx)
        self.sozai_panel.set_context(self.ctx)
        self.layout_panel.set_context(self.ctx)
        self.update_ui()

    def OnNewProject(self, event):
        if not self.ctx.project_saved():
            if wx.MessageBox("保存していない内容は失われます。続行しますか？",
                             "確認", wx.ICON_QUESTION | wx.YES_NO,
                             self) == wx.NO:
                return
        with YKLCreateProjectDialog(self) as create_dialog:
            if create_dialog.ShowModal() == wx.ID_CANCEL:
                return
            path = create_dialog.get_path()
        self.ctx = YKLContext(path)
        self.scenario_panel.set_context(self.ctx)
        self.sozai_panel.set_context(self.ctx)
        self.layout_panel.set_context(self.ctx)
        self.update_ui()

    def OnSave(self, event):
        self.ctx.save_project()
        self.update_title()

    def ShowAboutDialog(self, event):
        info = ADV.AboutDialogInfo()
        info.SetName("YukkuLips")
        info.SetVersion(VERSION)
        info.SetDescription(
            "クロマキー合成用キャラ素材動画生成アプリケーション\n\n"
            "スペシャルサンクス\n"
            "ズーズ氏 (http://www.nicotalk.com/charasozai.html)\n"
            "きつね氏 (http://www.nicotalk.com/ktykroom.html)\n\n"
            "YukkuLips Repository: https://github.com/PickledChair/YukkuLips")
        info.SetCopyright("(c) 2018 - 2020 SuitCase <ubatamamoon@gmail.com>")
        info.SetLicence(__doc__)

        ADV.AboutBox(info)

    def OnUpdate(self, event):
        self.update_ui()

    def update_title(self):
        if not self.ctx.project_saved():
            self.SetTitle("YukkuLips: " + self.ctx.get_project_name() + " (未保存)")
        else:
            self.SetTitle("YukkuLips: " + self.ctx.get_project_name())

    def update_ui(self):
        if len(self.ctx.get_sceneblocks()) == 0:
            self.scenario.Enable(False)
            self.audio_imp.Enable(False)
        else:
            self.scenario.Enable(True)
            self.audio_imp.Enable(True)
        self.sozai_panel.update_sozai_list()
        self.scenario_panel.update_sceneblock_list()
        self.layout_panel.update_layoutpreview()
        self.update_title()
        # self.Refresh()



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
