"""
YukkuLips

Copyright (c) 2018 - 2020 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import shutil
from pathlib import Path
import subprocess

import wx
import wx.adv as ADV
import wx.lib.newevent as NE
from media_utility.image_tool import get_thumbnail
from media_utility.audio_tool import convert_mp3_to_wav
from media_utility.video_tool import AnimeType, LineShape, AnimeSetting
from ykl_core.chara_sozai import CharaSozai

YKLSceneEditUpdate, EVT_SCENE_EDIT_UPDATE = NE.NewCommandEvent()


class YKLSceneEditDialog(wx.Dialog):
    def __init__(self, parent, ctx, sceneblock):
        super().__init__(parent, title="シーンブロック編集", size=(700, 510))
        self.ctx = ctx
        self.temp_dir = self.ctx.get_project_path() / "temp"
        if not self.temp_dir.exists():
            self.temp_dir.mkdir()
        else:
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir()
        self.sceneblock = sceneblock
        # シーンブロックのフォルダがないと、一時的な音声ファイルを保存できない
        if not self.sceneblock.is_saved():
            self.sceneblock.save()
        self.sceneblock.movie_generated = False
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.selistbook = SceneEditListBook(self, wx.ID_ANY, self.ctx, self.sceneblock, size=(680, 380))
        vbox.Add(self.selistbook, flag=wx.ALL, border=10)

        movie_box = wx.BoxSizer(wx.HORIZONTAL)
        len_lbl = wx.StaticText(self, wx.ID_ANY, "動画の長さ：")
        movie_box.Add(len_lbl, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.len_spin = wx.SpinCtrlDouble(self, wx.ID_ANY, min=1.0, max=120.0, inc=0.01, size=(60, -1))
        sound_time = self.sceneblock.get_movie_time()
        if sound_time > 0:
            self.len_spin.SetValue(sound_time)
            self.len_spin.Enable(False)
        else:
            self.len_spin.SetValue(self.sceneblock.movie_time)
        movie_box.Add(self.len_spin, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=5)
        intvl_lbl = wx.StaticText(self, wx.ID_ANY, "秒　末尾の追加時間：")
        movie_box.Add(intvl_lbl, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        self.intvl_spin = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0.1, max=120.0, inc=0.01, size=(60, -1))
        self.intvl_spin.SetValue(self.sceneblock.suffix_time)
        movie_box.Add(self.intvl_spin, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=5)
        intvl_lbl2 = wx.StaticText(self, wx.ID_ANY, "秒")
        movie_box.Add(intvl_lbl2, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        vbox.Add(movie_box, flag=wx.ALL, border=5)

        # if self.selistbook.has_anime:
        #     self.len_spin.Enable(False)
        #     self.intvl_spin.Enable(False)

        btns = wx.BoxSizer(wx.HORIZONTAL)
        self.gen_movie_btn = wx.Button(self, wx.ID_ANY, "動画を出力")
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=self.gen_movie_btn.GetId())
        btns.Add(self.gen_movie_btn, flag=wx.ALL, border=5)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "キャンセル")
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=cancel_btn.GetId())
        btns.Add(cancel_btn, flag=wx.ALL, border=5)
        ok_btn = wx.Button(self, wx.ID_OK, "適用して閉じる")
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=ok_btn.GetId())
        btns.Add(ok_btn, flag=wx.ALL, border=5)
        btns.Layout()
        vbox.Add(btns, 0, flag=wx.RIGHT | wx.TOP | wx.ALIGN_RIGHT, border=5)
        self.SetSizer(vbox)

        self.Bind(EVT_SCENE_EDIT_UPDATE, self.OnUpdate)

    def OnUpdate(self, event):
        self.set_data()
        sound_time = self.sceneblock.get_movie_time()
        if sound_time > 0:
            self.len_spin.SetValue(sound_time)
            self.len_spin.Enable(False)
        else:
            self.len_spin.SetValue(self.sceneblock.movie_time)
            self.len_spin.Enable(True)

    def set_data(self):
        self.sceneblock.movie_time = self.len_spin.GetValue()
        self.sceneblock.suffix_time = self.intvl_spin.GetValue()
        self.selistbook.set_data()

    def generate_movie(self):
        self.set_data()
        movie_path = self.sceneblock.generate_movie()
        p = subprocess.Popen(["open", "-a", "QuickTime Player", str(movie_path)])
        p.wait()

    def OnBtnClick(self, event):
        if event.GetId() == self.gen_movie_btn.GetId():
            self.generate_movie()
        else:
            if not self.sceneblock.movie_generated:
                self.set_data()
            # self.sceneblock.sozais_unsaved_check()
            shutil.rmtree(self.temp_dir)
            self.EndModal(event.GetId())


class SceneEditListBook(wx.Listbook):
    def __init__(self, parent, idx, ctx, block, size):
        super().__init__(parent, idx, size=size)
        self.has_anime = False
        self.ctx = ctx
        self.sceneblock = block
        im_size = 64
        il = wx.ImageList(im_size, im_size)
        for sozai in self.sceneblock.get_sozais():
            image = sozai.get_image()
            image = get_thumbnail(image, size=im_size)
            bmp = wx.Bitmap.FromBufferRGBA(im_size, im_size, image.tobytes())
            il.Add(bmp)
        self.AssignImageList(il)
        for i, sozai in enumerate(self.sceneblock.get_sozais()):
            page = SceneEditPanel(self, wx.ID_ANY, self.ctx, self.sceneblock, i, size=(680, 370))
            self.AddPage(page, sozai.get_name(), imageId=i)

        self.has_anime = all([self.GetPage(i).has_anime for i in range(self.GetPageCount())])

    def set_data(self):
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.set_data()


class SceneEditPanel(wx.Panel):
    def __init__(self, parent, idx, ctx, block, page_count, size):
        super().__init__(parent, idx, size=size)
        self.has_anime = False
        self.ctx = ctx
        self.sceneblock = block
        self.page_count = page_count
        self.sozai = self.sceneblock.get_sozais()[self.page_count]

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(self, wx.ID_ANY)
        self.audio_set_panel = AudioSettingPanel(self.notebook, wx.ID_ANY, self.sozai, self.ctx)
        self.notebook.AddPage(self.audio_set_panel, "セリフ・音源設定")
        self.anime_set_panel = AnimeSettingPanel(self.notebook, wx.ID_ANY, self.sozai)
        self.notebook.AddPage(self.anime_set_panel, "アニメーション設定")

        vbox.Add(self.notebook, flag=wx.EXPAND)

        self.has_anime = self.anime_set_panel.has_anime

        self.SetSizer(vbox)

    def set_data(self):
        self.audio_set_panel.set_data()
        self.anime_set_panel.set_data()


class AudioSettingPanel(wx.Panel):
    def __init__(self, parent, idx, sozai, ctx):
        super().__init__(parent, idx)
        self.sozai = sozai
        self.sound = None
        self.sf_path_dict = dict()
        self.ctx = ctx
        self.sound_temp_dir = self.ctx.get_project_path() / "temp" / "sound"
        if not self.sound_temp_dir.exists():
            self.sound_temp_dir.mkdir()
        sizer = wx.GridBagSizer(0, 0)
        scenario_lbl = wx.StaticText(self, wx.ID_ANY, "セリフ：")
        sizer.Add(scenario_lbl, (0, 0), flag=wx.ALL, border=10)
        self.sceneario_txt = wx.TextCtrl(self, wx.ID_ANY)
        self.sceneario_txt.SetValue(self.sozai.speech_content)
        sizer.Add(self.sceneario_txt, (0, 1), (3, 6), flag=wx.TOP | wx.BOTTOM | wx.EXPAND, border=10)

        audio_lbl = wx.StaticText(self, wx.ID_ANY, "音源設定：")
        sizer.Add(audio_lbl, (3, 0), flag=wx.ALL, border=10)

        change_flag = False

        anime_audio_lbl = wx.StaticText(self, wx.ID_ANY, "アニメ生成用音源：")
        sizer.Add(anime_audio_lbl, (4, 1), flag=wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)
        if not Path(self.sozai.anime_audio_path).exists():
            self.sozai.anime_audio_path = ""
            change_flag = True
        self.anime_audio_pick = wx.FilePickerCtrl(self, wx.ID_ANY, wildcard="WAV files (.wav)|.wav|MP3 files (.mp3)|.mp3", style=wx.FLP_OPEN | wx.FLP_USE_TEXTCTRL | wx.FLP_FILE_MUST_EXIST, path=self.sozai.anime_audio_path)
        anime_dt = PathDropTarget(self.anime_audio_pick)
        self.anime_audio_pick.SetDropTarget(anime_dt)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_audio_fill, id=self.anime_audio_pick.GetId())
        sizer.Add(self.anime_audio_pick, (4, 2), (1, 3), flag=wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.anime_audio_unsel = wx.Button(self, wx.ID_ANY, "ファイル指定を解除")
        sizer.Add(self.anime_audio_unsel, (4, 5), flag=wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.Bind(wx.EVT_BUTTON, self.on_unsel_btn, id=self.anime_audio_unsel.GetId())
        self.anime_audio_play = wx.Button(self, wx.ID_ANY, "再生")
        sizer.Add(self.anime_audio_play, (4, 6), flag=wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.Bind(wx.EVT_BUTTON, self.on_play_sound, id=self.anime_audio_play.GetId())

        movie_audio_lbl = wx.StaticText(self, wx.ID_ANY, "動画用音源：")
        sizer.Add(movie_audio_lbl, (5, 1), flag=wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)
        if not Path(self.sozai.movie_audio_path).exists():
            self.sozai.movie_audio_path = ""
            change_flag = True
        self.movie_audio_pick = wx.FilePickerCtrl(self, wx.ID_ANY, wildcard="WAV files (.wav)|.wav|MP3 files (.mp3)|.mp3", style=wx.FLP_OPEN | wx.FLP_USE_TEXTCTRL | wx.FLP_FILE_MUST_EXIST, path=self.sozai.movie_audio_path)
        movie_dt = PathDropTarget(self.movie_audio_pick)
        self.movie_audio_pick.SetDropTarget(movie_dt)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_audio_fill, id=self.movie_audio_pick.GetId())
        sizer.Add(self.movie_audio_pick, (5, 2), (1, 3), flag=wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.movie_audio_unsel = wx.Button(self, wx.ID_ANY, "ファイル指定を解除")
        self.Bind(wx.EVT_BUTTON, self.on_unsel_btn, id=self.movie_audio_unsel.GetId())
        sizer.Add(self.movie_audio_unsel, (5, 5), flag=wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.movie_audio_play = wx.Button(self, wx.ID_ANY, "再生")
        sizer.Add(self.movie_audio_play, (5, 6), flag=wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.Bind(wx.EVT_BUTTON, self.on_play_sound, id=self.movie_audio_play.GetId())
        prestart_lbl = wx.StaticText(self, wx.ID_ANY, "再生までの時間：")
        sizer.Add(prestart_lbl, (6, 1), flag=wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)
        self.prestart_spin = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0., max=120., inc=0.01, size=(60, -1))
        self.prestart_spin.SetValue(self.sozai.prestart_time)
        sizer.Add(self.prestart_spin, (6, 2), flag=wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)
        prestart_lbl2 = wx.StaticText(self, wx.ID_ANY, "秒")
        sizer.Add(prestart_lbl2, (6, 3), flag=wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=10)

        self.SetSizer(sizer)
        sizer.Fit(self)

        if change_flag:
            wx.MessageBox("一部の音声ファイルが見つかりませんでした。\n"
                          "ファイルパスを指定し直す必要があります。", "確認",
                          wx.ICON_EXCLAMATION | wx.OK)

    def set_data(self):
        self.sozai.speech_content = self.sceneario_txt.GetValue()
        anime_audio_path = self.anime_audio_pick.GetPath()
        if Path(anime_audio_path).exists():
            self.sozai.anime_audio_path = anime_audio_path
        movie_audio_path = self.movie_audio_pick.GetPath()
        if Path(movie_audio_path).exists():
            self.sozai.movie_audio_path = movie_audio_path
        self.sozai.prestart_time = self.prestart_spin.GetValue()

    def on_play_sound(self, event):
        if event.GetId() == self.anime_audio_play.GetId():
            pick = self.anime_audio_pick
        else:
            pick = self.movie_audio_pick

        path = pick.GetPath()
        if self.sf_path_dict.get(path) is None:
            if Path(path).suffix.lower() == ".mp3":
                convert_mp3_to_wav(Path(path), str(self.ctx.ffmpeg_path), self.sound_temp_dir)
                new_path = Path(str(self.sound_temp_dir / Path(path).stem) + ".wav")
                while not new_path.exists():
                    pass
                self.sf_path_dict[path] = str(new_path)
            elif Path(path).suffix.lower() == ".wav":
                self.sf_path_dict[path] = path
            else:
                wx.LogError(f"サポートされていない音声ファイル形式です：{path}")
                return
        self.sound = ADV.Sound(self.sf_path_dict[path])
        if self.sound.IsOk():
            self.sound.Play()

    def on_audio_fill(self, event):
        if event.GetId() == self.anime_audio_pick.GetId():
            if self.movie_audio_pick.GetPath() == "":
                self.movie_audio_pick.SetPath(self.anime_audio_pick.GetPath())
        wx.PostEvent(self, YKLSceneEditUpdate(self.GetId()))

    def on_unsel_btn(self, event):
        if event.GetId() == self.movie_audio_unsel.GetId():
            self.movie_audio_pick.SetPath("")
        else:
            self.anime_audio_pick.SetPath("")
        wx.PostEvent(self, YKLSceneEditUpdate(self.GetId()))


class PathDropTarget(wx.FileDropTarget):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        if filenames[0][-4:].lower() in [".mp3", ".wav"]:
            self.window.SetPath(filenames[0])
        return True


class AnimeSettingPanel(wx.ScrolledWindow):
    def __init__(self, parent, idx, sozai):
        super().__init__(parent, idx)
        self.sozai = sozai
        # if self.sozai.get_current_image_dic().get('全'):
        #     self.orderd_parts = ["全",]
        #     self.anime_images_dict = {0: None}
        #     self.count_dict = {"全": 1,}
        # else:
        self.orderd_parts, self.anime_images_dict = self.sozai.get_anime_image_dict()
        self.count_dict = CharaSozai.get_count_of_each_part_images_dict(self.orderd_parts, self.anime_images_dict)
        # print(self.orderd_parts, self.anime_images_dict, self.count_dict)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.widgets_dict = dict()
        if '全' in self.orderd_parts:
            nothing_lbl = wx.StaticText(self, wx.ID_ANY, "アニメーションなし（「全」パーツを選択中）")
            vbox.Add(nothing_lbl)
        else:
            self.anime_labels = AnimeType.get_labels()
            self.anime_type_dict = {k: v for k, v in zip(self.anime_labels, AnimeType)}
            settings = self.sozai.create_anime_setting().into_json()
            for part in self.count_dict:
                if self.count_dict[part] > 1:
                    setting = settings[part]
                    self.widgets_dict[part] = self.create_part_anime_widgets_dict(
                        part,
                        anime_type=[anime_type.name for anime_type in AnimeType].index(setting["Anime Type"]),
                        start=setting["Start Time"],
                        interval=setting["Interval"],
                        take_time=setting["Take Time"],
                        frame=setting["Hold Frame"],
                        threshold=setting["Threshold"],
                        line=[line_shape.name for line_shape in LineShape].index(setting["Line Shape"])
                    )
                    vbox.Add(self.widgets_dict[part]["bag"], flag=wx.LEFT, border=20)
        vbox.Layout()
        if self.widgets_dict:
            self.has_anime = True
        else:
            self.has_anime = False
        self.SetSizer(vbox)
        self.SetScrollRate(20, 20)

    def create_part_anime_widgets_dict(self, part, anime_type=2, start=0.0, interval=5.0, take_time=0.5, frame=2, threshold=1.0, line=1):
        ret_dict = dict()
        bag = wx.GridBagSizer(0, 0)
        if part in ["前側", "後側"]:
            part_name = "後・" + part
        else:
            part_name = part
        part_lbl = wx.StaticText(self, wx.ID_ANY, f"{part_name}：")
        bag.Add(part_lbl, (0, 0), flag=wx.TOP | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        type_lbl = wx.StaticText(self, wx.ID_ANY, "アニメタイプ")
        bag.Add(type_lbl, (0, 1), flag=wx.TOP | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        # type_choice
        ret_dict["type_choice"] = wx.Choice(self, wx.ID_ANY, choices=self.anime_labels)
        ret_dict["type_choice"].SetSelection(anime_type)
        bag.Add(ret_dict["type_choice"], (0, 2), flag=wx.TOP | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        start_lbl = wx.StaticText(self, wx.ID_ANY, "開始")
        bag.Add(start_lbl, (1, 1), flag=wx.TOP | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        # start_spin
        ret_dict["start_spin"] = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0., max=120., inc=0.01, size=(60, -1))
        ret_dict["start_spin"].SetValue(start)
        start_box = wx.BoxSizer(wx.HORIZONTAL)
        start_box.Add(ret_dict["start_spin"], flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        start_lbl2 = wx.StaticText(self, wx.ID_ANY, "秒")
        start_box.Add(start_lbl2, flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        bag.Add(start_box, (1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        intvl_lbl = wx.StaticText(self, wx.ID_ANY, "間隔")
        bag.Add(intvl_lbl, (2, 1), flag=wx.TOP | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        # interval_spin
        ret_dict["interval_spin"] = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0., max=120., inc=0.01, size=(60, -1))
        ret_dict["interval_spin"].SetValue(interval)
        intvl_box = wx.BoxSizer(wx.HORIZONTAL)
        intvl_box.Add(ret_dict["interval_spin"], flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        intvl_lbl2 = wx.StaticText(self, wx.ID_ANY, "秒")
        intvl_box.Add(intvl_lbl2, flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        bag.Add(intvl_box, (2, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        time_lbl = wx.StaticText(self, wx.ID_ANY, "時間")
        bag.Add(time_lbl, (3, 1), flag=wx.TOP | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        # time_spin
        ret_dict["time_spin"] = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0., max=120., inc=0.01, size=(60, -1))
        ret_dict["time_spin"].SetValue(take_time)
        time_box = wx.BoxSizer(wx.HORIZONTAL)
        time_box.Add(ret_dict["time_spin"], flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        time_lbl2 = wx.StaticText(self, wx.ID_ANY, "秒")
        time_box.Add(time_lbl2, flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        bag.Add(time_box, (3, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        hold_lbl = wx.StaticText(self, wx.ID_ANY, "中間割合")
        bag.Add(hold_lbl, (4, 1), flag=wx.TOP | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        # hold_spin
        ret_dict["hold_spin"] = wx.SpinCtrl(self, wx.ID_ANY, min=1, max=60, size=(60, -1))
        ret_dict["hold_spin"].SetValue(frame)
        hold_box = wx.BoxSizer(wx.HORIZONTAL)
        hold_box.Add(ret_dict["hold_spin"], flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        hold_lbl2 = wx.StaticText(self, wx.ID_ANY, "フレーム")
        hold_box.Add(hold_lbl2, flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        bag.Add(hold_box, (4, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        threshold_lbl = wx.StaticText(self, wx.ID_ANY, "音量ボーダーの係数")
        bag.Add(threshold_lbl, (5, 1), flag=wx.TOP | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        # threshold_spin
        ret_dict["threshold_spin"] = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0.1, max=2.0, inc=0.01, size=(60, -1))
        ret_dict["threshold_spin"].SetValue(threshold)
        bag.Add(ret_dict["threshold_spin"], (5, 2), flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        line_lbl = wx.StaticText(self, wx.ID_ANY, "音量ボーダーの形状")
        bag.Add(line_lbl, (6, 1), flag=wx.TOP | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=10)
        # line_choice
        ret_dict["line_choice"] = wx.Choice(self, wx.ID_ANY, choices=["一次直線", "二次曲線"])
        ret_dict["line_choice"].SetSelection(line)
        bag.Add(ret_dict["line_choice"], (6, 2), flag=wx.TOP | wx.ALIGN_CENTER_VERTICAL, border=10)
        ret_dict["bag"] = bag

        return ret_dict

    def set_data(self):
        anime_setting = AnimeSetting(self.count_dict)
        # 全パーツ選択時はself.widgets_dictが空なので、以下のforループは回らない
        for part, widgets in self.widgets_dict.items():
            part_set = anime_setting.part_settings[part]
            type_choice = widgets["type_choice"]
            type_idx = type_choice.GetSelection()
            anime_type = AnimeType.from_str(type_choice.GetString(type_idx))
            part_set.anime_type = anime_type
            part_set.start = widgets["start_spin"].GetValue()
            part_set.interval = widgets["interval_spin"].GetValue()
            part_set.take_time = widgets["time_spin"].GetValue()
            part_set.stop_frames = widgets["hold_spin"].GetValue()
            part_set.sound_threshold = widgets["threshold_spin"].GetValue()
            line_choice = widgets["line_choice"]
            line_idx = line_choice.GetSelection()
            line_shape = LineShape.from_str(line_choice.GetString(line_idx))
            part_set.line_shape = line_shape
        self.sozai.set_anime_setting(anime_setting)
