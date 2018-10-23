"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

from pathlib import Path
import wx
import os
import sys
from copy import copy
from .chara_sozai import CharaSozai
from .media_utility.image_tool import combine_images, save_image
from .media_utility.audio_tool import get_sound_map, join_sound_files, convert_mp3_to_wav
from .media_utility.video_tool import save_video, save_silent_video
from collections import namedtuple
from .ykl_project import YKLProject
from multiprocessing import Manager, Pool


BgColor = namedtuple("BgColor", ("name", "color_tuple"))
ImageInfo = namedtuple("ImageInfo", ("path", "part", "is_mul", "is_front"))
MovieSize = namedtuple("MovieSize", ("name", "size_tuple"))


class YKLContext:
    def __init__(self):
        self.proj_name = "Untitled_Project"

        # 静画設定
        self.sozai = None
        self.sozai_dir = Path.home()
        self.current_images_dic = {}
        self.bg_colors = (BgColor(name="ブルーバック", color_tuple=(0, 0, 255, 255)),
                          BgColor(name="グリーンバック", color_tuple=(0, 255, 0, 255)),
                          BgColor(name="レッドバック", color_tuple=(255, 0, 0, 255)),
                          BgColor(name="透過", color_tuple=(0, 0, 0, 0)))
        self.bg_color = self.bg_colors[0]
        self.rev_flag = False
        self.base_size = (400, 400)

        self.ui_image_path = Path.home() / "yukkulips_cache" / "ui_image_cache"
        if not self.ui_image_path.exists():
            self.ui_image_path.mkdir(parents=True)
        self.audio_path = Path.home() / "yukkulips_cache" / "audio_cache"
        if not self.audio_path.exists():
            self.audio_path.mkdir(parents=True)
        self.animation_image_path = Path.home() / "yukkulips_cache" / "animation_image_cache"
        if not self.animation_image_path.exists():
            self.animation_image_path.mkdir(parents=True)

        self.save_ui_image(self.integrate_images(self.base_size))

        # 動画設定
        self.proj_audio_dir = Path.home()
        self.is_silent_movie = False
        self.silent_interval = 0.0
        self.voice_interval = 0.8
        self.blink_interval = 5.0
        self.blink_types = ("定期往復型", "登場退場型")
        self.blink_type = self.blink_types[0]
        self.movie_sizes = (MovieSize(name="720p", size_tuple=(1280, 720)),
                            MovieSize(name="1080p", size_tuple=(1920, 1080)))
        self.movie_size = self.movie_sizes[0]
        self.sozai_pos = [0, 0]
        self.sozai_scale = 1.0
        self.ref_background = None

        self.project = YKLProject()
        self.save_flag = False

        self.ffmpeg_path = "./ffmpeg/ffmpeg"

        if getattr(sys, 'frozen', False):
            # frozen は PyInstaller でこのスクリプトが固められた時に sys に追加される属性
            # frozen が見つからない時は素の Python で実行している時なので False を返す
            bundle_dir = sys._MEIPASS
            self.ffmpeg_path = os.path.join(bundle_dir, self.ffmpeg_path)

    def set_sozai_dir(self, sozai_dir):
        self.sozai_dir = sozai_dir
        self.sozai = CharaSozai(self.sozai_dir)
        self.current_images_dic = self.__set_default_images()

    def __set_default_images(self):
        images_dic = {}
        for part in self.sozai.part_dirs:
            images = self.sozai.images_dic[part.name]
            default_images = []
            if len(images) > 0:
                default_images.append(self.sozai.images_dic[part.name][0])
                if "00" not in str(default_images[0]) or part.name == '全':
                    default_images = []
            images_dic[part.name] = default_images
        images_dic["髪(透明)"] = []
        if '髪' in [part.name for part in self.sozai.part_dirs]:
            # ここで tp と書いているのは transparent のこと
            tp_flag = False
            tp_num = -1
            for i, hair in enumerate(self.sozai.images_dic['髪']):
                if hair.name == "01.png":
                    images_dic["髪(透明)"].append(hair)
                    tp_flag = True
                    tp_num = i
            if not tp_flag:
                for hair in self.sozai.images_dic['髪']:
                    if hair.name == "00.png":
                        images_dic["髪(透明)"].append(hair)
            else:
                self.sozai.images_dic['髪'].pop(tp_num)
        return images_dic

    def integrate_images(self, base_size):
        if self.sozai is None:
            image = combine_images(base_size=base_size, bg_color=self.bg_color.color_tuple)
        else:
            image_infos = self.__sort_images()
            image = combine_images(*image_infos, bg_color=self.bg_color.color_tuple)
            self.base_size = image.size
        return image

    def __sort_images(self):
        image_infos = []
        images_order = ('後', '体', '顔', '髪', '眉', '目', '口', '髪(透明)', '他')
        if '全' in list(self.current_images_dic.keys()):
            if len(self.current_images_dic['全']) != 0:
                image_infos.append(ImageInfo(path=self.current_images_dic['全'][0],
                                             part='全', is_mul=False, is_front=False))
                return image_infos
        for part in images_order:
            if part in list(self.current_images_dic.keys()):
                if len(self.current_images_dic[part]) != 0:
                    if part == '顔':
                        for path in self.current_images_dic[part]:
                            if 'b' in path.name:
                                image_infos.append(ImageInfo(path=path,
                                                             part=part, is_mul=True, is_front=False))
                            else:
                                image_infos.append(ImageInfo(path=path,
                                                             part=part, is_mul=False, is_front=False))
                    elif part == '後':
                        for path in self.current_images_dic[part]:
                            if 'm1' in path.name:
                                image_infos.append(ImageInfo(path=path,
                                                             part=part, is_mul=False, is_front=True))
                            else:
                                image_infos.append(ImageInfo(path=path,
                                                             part=part, is_mul=False, is_front=False))
                    else:
                        for path in self.current_images_dic[part]:
                            image_infos.append(ImageInfo(path=path,
                                                         part=part, is_mul=False, is_front=False))
        return image_infos

    def save_ui_image(self, image):
        save_image(image, self.ui_image_path / "ui_image.png", rev_flag=self.rev_flag)

    def save_still_image(self, path):
        save_image(self.integrate_images(self.base_size), path, rev_flag=self.rev_flag)

    def save_movie_size_image(self, path):
        bg_color_backup = copy(self.bg_color)
        self.bg_color = self.bg_colors[3]
        save_image(self.integrate_images(self.base_size), path, rev_flag=self.rev_flag, is_anim=True,
                   bg_size=self.movie_size.size_tuple, bg_color=(0, 0, 0, 0), pos=self.sozai_pos,
                   scale=self.sozai_scale)
        self.bg_color = bg_color_backup

    def set_bg_color(self, color_tuple):
        self.bg_color = BgColor(name="その他", color_tuple=color_tuple)

    def gen_movie(self, file_path=Path.home() / "test.mp4", back_margin=60):
        eye_paths = []
        mouth_paths = []
        for eye_path in self.sozai.images_dic['目']:
            if eye_path.name[0:2] == self.current_images_dic['目'][0].name[0:2]:
                eye_paths.append(eye_path)
        for mouth_path in self.sozai.images_dic['口']:
            if mouth_path.name[0:2] == self.current_images_dic['口'][0].name[0:2]:
                mouth_paths.append(mouth_path)
        animation_images = []
        current_images_backup = self.current_images_dic.copy()
        if len(eye_paths) < 1 and len(mouth_paths) < 1:
            wx.MessageBox("目と口がないキャラ素材は現在サポートしておりません", "エラー", wx.ICON_QUESTION | wx.OK, None)
            return
        else:
            if len(eye_paths) > 0 and len(mouth_paths) > 0:
                progress_dialog = wx.ProgressDialog(
                    title="動画出力",
                    message="動画出力中...",
                    maximum=len(eye_paths)*len(mouth_paths),
                    style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
                progress_dialog.Show()
                progress = 0
                for i, eye_path in enumerate(eye_paths):
                    self.current_images_dic['目'] = [eye_path]
                    for j, mouth_path in enumerate(mouth_paths):
                        self.current_images_dic['口'] = [mouth_path]
                        image = self.integrate_images(self.base_size)
                        animation_images.append(image)
                        progress += 1
                        progress_dialog.Update(progress, "画像配列中...")
            else:
                if len(eye_paths) > 0:
                    for eye_path in eye_paths:
                        self.current_images_dic['目'] = [eye_path]
                        image = self.integrate_images(self.base_size)
                        animation_images.append(image)
                elif len(mouth_paths) > 0:
                    for mouth_path in mouth_paths:
                        self.current_images_dic['口'] = [mouth_path]
                        image = self.integrate_images(self.base_size)
                        animation_images.append(image)
        self.current_images_dic = current_images_backup

        total_sound = None

        if not self.is_silent_movie:
            sound_files = sorted(sorted(self.proj_audio_dir.glob("*.wav")) + sorted(self.proj_audio_dir.glob("*.WAV")))
            if len(sound_files) < 1:
                wx.MessageBox("指定フォルダ内にオーディオファイルがありません", "エラー", wx.ICON_QUESTION | wx.OK, None)
                return
            sound_files = [str(sound_file) for sound_file in sound_files]

            total_sound = join_sound_files(*sound_files, interval=self.voice_interval, audio_cache=self.audio_path)
            if total_sound is None:
                return
            sound_level_seq = get_sound_map(total_sound, len(mouth_paths))
        else:
            sound_level_seq = []
            if self.silent_interval > 2:
                sound_level_seq += [0 for _ in range(int((self.silent_interval - 2) * 30))]

        queue = Manager().Queue()
        arg = []

        if len(eye_paths) > 0 and len(mouth_paths) > 0:
            total_seqs_len_without_margin = len(sound_level_seq)
            sound_level_seq += [0 for _ in range(back_margin)]
            total_seqs_len = len(sound_level_seq)
            # blink interval frames number と、その半分(half)をあらかじめ定義
            progress_dialog = wx.ProgressDialog(
                title="動画出力",
                message="動画出力中...",
                maximum=total_seqs_len,
                style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
            progress_dialog.Show()
            progress = 0
            bif_num = int(self.blink_interval*30)
            vif_num = int(self.voice_interval*30)
            bifn_half = int(bif_num/2)
            for i, mouth_num in enumerate(sound_level_seq):
                eye_num = 0
                for j in range(len(eye_paths)):
                    if self.blink_type == "定期往復型":
                        if abs(i % bif_num - bifn_half) == j and total_seqs_len > i + vif_num + len(mouth_paths):
                            eye_num = len(eye_paths) - 1 - j
                            break
                    else:
                        if i < len(eye_paths):
                            eye_num = i
                        elif (total_seqs_len_without_margin - i) < len(eye_paths):
                            eye_num = max(total_seqs_len_without_margin - i, 0)
                        else:
                            eye_num = len(eye_paths) - 1
                out_image = animation_images[eye_num * len(mouth_paths) + mouth_num]
                arg.append((out_image, self.animation_image_path,
                            str(i).zfill((len(str(total_seqs_len)))),
                            self.rev_flag, self.bg_color.color_tuple, self.movie_size.size_tuple,
                            tuple(self.sozai_pos), self.sozai_scale, queue))
                progress += 1
                progress_dialog.Update(progress,
                                       "連番画像を生成中...({}/{} フレーム)".format(progress, total_seqs_len))

            p = Pool()
            r = p.map_async(save_anime_image, arg)

            progress_dialog = wx.ProgressDialog(
                title="動画出力",
                message="動画出力中...",
                maximum=total_seqs_len,
                style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
            progress_dialog.Show()
            progress = 0

            while not r.ready() or progress < total_seqs_len:
                for _ in range(queue.qsize()):
                    progress += 1
                    progress_dialog.Update(progress, "連番画像をキャッシュに保存中: {}\n\t{}/{}"
                                                     " フレーム".format(queue.get(), progress, total_seqs_len))

            p.close()

            try:
                progress_dialog = wx.ProgressDialog(
                    title="動画出力",
                    message="動画出力中...",
                    maximum=2,
                    style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
                progress_dialog.Show()
                progress = 1
                progress_dialog.Update(progress, "動画出力中...")
                if not self.is_silent_movie:
                    save_video(self.animation_image_path, total_sound, file_path, self.ffmpeg_path)
                else:
                    save_silent_video(self.animation_image_path, file_path, self.ffmpeg_path)
                progress += 1
                progress_dialog.Update(progress, "完了")
                for path in self.animation_image_path.glob("*.png"):
                    os.remove(str(path))
                if not self.is_silent_movie:
                    os.remove(str(self.audio_path / "temp.wav"))
            except Exception as e:
                progress += 1
                progress_dialog.Update(progress, "動画出力 失敗")
                wx.LogError("YukkuLips error: " + str(e))
                for path in self.animation_image_path.glob("*.png"):
                    os.remove(str(path))
                if not self.is_silent_movie:
                    os.remove(str(self.audio_path / "temp.wav"))

    def mp3_to_wav(self, file_path):
        convert_mp3_to_wav(file_path, self.ffmpeg_path)

    def update_context_from_project(self):
        self.proj_name = self.project.contents["Project Name"]
        self.sozai_dir = Path(self.project.contents["Sozai Directory"])
        self.sozai = CharaSozai(self.sozai_dir)
        self.current_images_dic = {}
        for part in self.project.contents["Current Images"]:
            if len(self.project.contents["Current Images"][part]) > 0:
                for path_str in self.project.contents["Current Images"][part]:
                    if part not in list(self.current_images_dic.keys()):
                        self.current_images_dic[part] = []
                    self.current_images_dic[part].append(Path(path_str))
            else:
                self.current_images_dic[part] = []
        proj_bg_color_tuple = tuple([self.project.contents["Background Color"][element]
                                    for element in self.project.contents["Background Color"]])
        has_basic = False
        for bg_color in self.bg_colors:
            if proj_bg_color_tuple == bg_color.color_tuple:
                self.bg_color = bg_color
                has_basic = True
                break
        if not has_basic:
            self.set_bg_color(proj_bg_color_tuple)
        self.rev_flag = self.project.contents["Mirror Image"]
        self.base_size = (self.project.contents["Base Image Size"]["width"],
                          self.project.contents["Base Image Size"]["height"])
        self.proj_audio_dir = Path(self.project.contents["Audio Directory"])
        self.is_silent_movie = self.project.contents["Is Silent Movie"]
        self.silent_interval = self.project.contents["Silent Interval"]
        self.voice_interval = self.project.contents["Voice Interval"]
        self.blink_interval = self.project.contents["Blink Interval"]
        self.blink_type = self.blink_types[self.project.contents["Blink Type"]]
        self.movie_size = self.movie_sizes[
            [movie_size.name for movie_size in self.movie_sizes].index(self.project.contents["Movie Size"])]
        self.sozai_pos = (self.project.contents["Sozai Position"]["x"], self.project.contents["Sozai Position"]["y"])
        self.sozai_scale = self.project.contents["Sozai Scale"]
        if self.project.contents["BG Reference"] is None:
            self.ref_background = self.project.contents["BG Reference"]
        else:
            self.ref_background = Path(self.project.contents["BG Reference"])


def save_anime_image(args):
    save_image(args[0], args[1] / (args[2] + ".png"),
               rev_flag=args[3], is_anim=True, bg_color=args[4], bg_size=args[5], pos=args[6], scale=args[7])
    args[8].put(args[2] + ".png")
