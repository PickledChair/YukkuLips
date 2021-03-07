"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

import json
from copy import deepcopy
import shutil
from multiprocessing import Manager, Pool, freeze_support
freeze_support()

import wx

from .chara_sozai import CharaSozai
from media_utility.image_tool import get_rescaled_image, get_scene_image, save_anime_frame
from media_utility.audio_tool import get_sound_length, mix_movie_sounds
from media_utility.video_tool import save_video, save_silent_video, FFMPEG_PATH


class SceneBlock:
    def __init__(self, sb_uuid, sozai_resource_dic, project):
        self.__project = project
        self.__uuid = sb_uuid
        self.__sozai_resource_dic = sozai_resource_dic
        self.__sozai_dic = {
            k: CharaSozai(
                k, self.__uuid, self.__project, resource)
            for k, resource in sozai_resource_dic.items()}
        self.__sozai_pos = [(0, 0) for _ in sozai_resource_dic]
        self.__sozai_order = [i for i in range(len(sozai_resource_dic))]
        self.__sozai_scale = [1.0 for _ in range(len(sozai_resource_dic))]
        self.__bg_path = None
        self.__content = SceneBlock.__initial_content()
        if sozai_resource_dic:
            self.__content['CharaSozai List'] = list(self.__sozai_dic.keys())
            self.__content['CharaSozai Pos'] = [list(pos) for pos in self.__sozai_pos]
            self.__content['CharaSozai Order'] = self.__sozai_order
            self.__content['CharaSozai Scale'] = self.__sozai_scale
        self.__scene_image = self.__integrate_scene_image()

        # 動画設定
        self.__movie_time = 1.
        self.__suffix_time = 0.5
        self.__movie_generated = False
        root = self.__project.root_path() / "scene_block" / self.__uuid
        movie_dir = root / "movie"
        self.__movie_path = movie_dir / "scene_movie.mp4"

        self.__is_saved = False

    @property
    def movie_path(self):
        if self.movie_generated:
            return self.__movie_path
        else:
            return None

    @movie_path.setter
    def movie_path(self, _):
        raise ValueError()

    @staticmethod
    def __initial_content():
        content = {
            'CharaSozai List': [],
            'CharaSozai Pos': [],
            'CharaSozai Order': [],
            'CharaSozai Scale': [],
            'Background Path': None,
            'Movie Time': 1.0,
            'Suffix Time': 0.5,
            'Movie Generated': False,
        }
        return content

    @staticmethod
    def open(sb_uuid, sozai_resource_dic, project, parts_path_dics=[]):
        block = SceneBlock(sb_uuid, {}, project)
        with (project.root_path() / "scene_block" / sb_uuid / "sceneblock.json").open('r') as f:
            content = json.load(f)
        block.__restore(content, sozai_resource_dic, parts_path_dics)
        return block

    def __restore(self, content, sozai_resource_dic, parts_path_dics):
        sozai_list = content['CharaSozai List']
        self.__sozai_resource_dic = sozai_resource_dic
        self.__sozai_dic = {
            s: CharaSozai.open(
                s, self.__uuid, self.__project, self.__sozai_resource_dic[s], parts_path_dic=p
                ) for s, p in zip(sozai_list, parts_path_dics)
            }
        self.__sozai_pos = [tuple(pos) for pos in content["CharaSozai Pos"]]
        self.__sozai_order = content["CharaSozai Order"]
        self.__sozai_scale = content["CharaSozai Scale"]
        self.__bg_path = content["Background Path"]
        self.__movie_time = content.get("Movie Time", 1.0)
        self.__suffix_time = content.get("Suffix Time", 0.5)
        self.__movie_generated = content.get("Movie Generated", False)
        self.__content = content
        self.__scene_image = self.__integrate_scene_image()
        self.__is_saved = True

    def add_sozai(self, k, resource_path):
        self.__sozai_dic[k] = CharaSozai(k, self.__uuid, self.__project, resource_path)
        self.__sozai_resource_dic[k] = resource_path
        self.__sozai_order.append(len(self.__sozai_dic)-1)
        self.__sozai_pos.append((0, 0))
        self.__sozai_scale.append(1.0)
        self.__content['CharaSozai List'] = list(self.__sozai_dic.keys())
        self.__content['CharaSozai Pos'] = [list(pos) for pos in self.__sozai_pos]
        self.__content['CharaSozai Order'] = self.__sozai_order
        self.__content['CharaSozai Scale'] = self.__sozai_scale
        self.__scene_image = self.__integrate_scene_image()
        self.movie_generated = False
        self.__is_saved = False

    def remove_sozai(self, idx):
        key = list(self.__sozai_dic.keys())[idx]
        self.__sozai_dic.pop(key)
        self.__sozai_resource_dic.pop(key)
        self.__sozai_order.pop(idx)
        self.__sozai_pos.pop(idx)
        self.__sozai_scale.pop(idx)
        self.__content['CharaSozai List'] = list(self.__sozai_dic.keys())
        self.__content['CharaSozai Pos'] = [list(pos) for pos in self.__sozai_pos]
        self.__content['CharaSozai Order'] = self.__sozai_order
        self.__content['CharaSozai Scale'] = self.__sozai_scale
        self.__scene_image = self.__integrate_scene_image()
        self.movie_generated = False
        self.__is_saved = False

    def set_new_sozai(self, idx, sozai):
        key = list(self.__sozai_dic.keys())[idx]
        self.__sozai_dic[key] = sozai
        self.__scene_image = self.__integrate_scene_image()
        self.movie_generated = False
        self.__is_saved = False

    def sozais_unsaved_check(self):
        self.__is_saved = all([sozai.is_saved() for sozai in self.get_sozais()])
        if not self.__is_saved:
            self.movie_generated = False

    def __integrate_scene_image(self):
        images = [sozai.get_image() for sozai in self.get_sozais()]
        # 整列はget_scene_image関数内で行うため、ここで並び替えてはいけない
        # images = [images[i] for i in self.__sozai_order]
        images = [get_rescaled_image(image, scale) for image, scale in zip(images, self.__sozai_scale)]
        bg_size = self.__project.resolution
        bg_color = self.__project.bg_color
        scene_image = get_scene_image(images, self.__sozai_pos, self.__sozai_order, bg_size=bg_size, bg_color=bg_color)
        return scene_image

    def update_scene_image(self):
        self.__scene_image = self.__integrate_scene_image()
        self.movie_generated = False
        self.__is_saved = False

    @property
    def sozai_pos(self):
        return self.__sozai_pos

    @sozai_pos.setter
    def sozai_pos(self, new_pos_list):
        self.__sozai_pos = new_pos_list
        self.__scene_image = self.__integrate_scene_image()
        self.__content["CharaSozai Pos"] = [list(pos) for pos in new_pos_list]
        self.movie_generated = False
        self.__is_saved = False

    @property
    def sozai_scale(self):
        return self.__sozai_scale

    @sozai_scale.setter
    def sozai_scale(self, new_scale_list):
        self.__sozai_scale = new_scale_list
        self.__scene_image = self.__integrate_scene_image()
        self.__content["CharaSozai Scale"] = new_scale_list
        self.movie_generated = False
        self.__is_saved = False

    @property
    def sozai_order(self):
        return self.__sozai_order

    @sozai_order.setter
    def sozai_order(self, new_order_list):
        self.__sozai_order = new_order_list
        self.__scene_image = self.__integrate_scene_image()
        self.__content["CharaSozai Order"] = new_order_list
        self.movie_generated = False
        self.__is_saved = False

    @property
    def bg_path(self):
        return self.__bg_path

    @bg_path.setter
    def bg_path(self, new_path):
        self.__bg_path = new_path
        self.__content["Background Path"] = str(new_path)
        self.__is_saved = False

    @property
    def scene_image(self):
        return self.__scene_image

    @scene_image.setter
    def scene_image(self, image):
        raise ValueError()

    @property
    def movie_generated(self):
        return self.__movie_generated

    @movie_generated.setter
    def movie_generated(self, b):
        self.__movie_generated = b
        self.__content["Movie Generated"] = self.__movie_generated
        self.__is_saved = False

    @property
    def movie_time(self):
        return self.__movie_time

    @movie_time.setter
    def movie_time(self, new_time):
        self.__movie_time = new_time
        self.__content["Movie Time"] = self.__movie_time
        self.movie_generated = False
        self.__is_saved = False

    @property
    def suffix_time(self):
        return self.__suffix_time

    @suffix_time.setter
    def suffix_time(self, new_time):
        self.__suffix_time = new_time
        self.__content["Suffix Time"] = self.__suffix_time
        self.movie_generated = False
        self.__is_saved = False

    def set_uuid(self, new_uuid):
        self.__uuid = new_uuid
        self.movie_generated = False
        self.__is_saved = False

    def get_uuid(self):
        return self.__uuid

    def get_copy(self, new_uuid):
        copy_self = deepcopy(self)
        copy_self.set_uuid(new_uuid)
        for sozai in copy_self.get_sozais():
            sozai.set_sb_uuid(new_uuid)
        copy_self.movie_generated = False
        return copy_self

    def get_sozais(self):
        return list(self.__sozai_dic.values())

    def get_sozai_resource_dic(self):
        return deepcopy(self.__sozai_resource_dic)

    def save(self):
        root = self.__project.root_path() / "scene_block" / self.__uuid
        sozai_folder = root / "chara_sozai"
        if not root.exists():
            root.mkdir()
            sozai_folder.mkdir()
        else:
            if self.__is_saved:
                return
            else:
                # キャラ素材の増減を反映してフォルダを削除
                items = [item.name for item in sozai_folder.iterdir() if item.is_dir()]
                # print(items)
                delete_sozais = [item for item in items if item not in list(self.__sozai_dic.keys())]
                # print(delete_sozais)
                for delete_sozai in delete_sozais:
                    shutil.rmtree(sozai_folder / delete_sozai)
        for sozai in self.get_sozais():
            sozai.save()
        block_file_path = root / 'sceneblock.json'
        with block_file_path.open('w') as f:
            json.dump(self.__content, f, indent=4, ensure_ascii=False)
        self.__is_saved = True

    def is_saved(self):
        return self.__is_saved

    def get_movie_time(self):
        anime_sounds = []
        for sozai in self.get_sozais():
            _, anime_audio = sozai.get_movie_anime_audio()
            anime_sounds.append(anime_audio)
        sound_time = max([get_sound_length(path) for path in anime_sounds]) / 30
        return sound_time

    def generate_movie(self):
        if not self.__is_saved:
            self.save()
            self.__is_saved = False
        movie_sounds = []
        anime_sounds = []
        ordered_parts = []
        anime_dicts = []
        anime_settings = []
        progress_dialog = wx.ProgressDialog(
            title="動画出力",
            message="動画出力中...",
            maximum=len(self.get_sozais())+1,
            style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
        progress_dialog.Show()
        progress = 1
        progress_dialog.Update(
            progress,
            "キャラ素材ごとのアニメ画像生成: 開始中...")
        for sozai in self.get_sozais():
            movie_audio, anime_audio = sozai.get_movie_anime_audio()
            movie_sounds.append(movie_audio)
            anime_sounds.append(anime_audio)
            anime_setting = sozai.create_anime_setting()
            anime_settings.append(anime_setting)
            soz = deepcopy(sozai)
            ordered_part, anime_dict = soz.get_anime_image_dict(image_elements=True)
            ordered_parts.append(ordered_part)
            anime_dicts.append(anime_dict)
            progress += 1
            progress_dialog.Update(
                progress,
                "キャラ素材ごとのアニメ画像生成: "
                "{}/{}".format(progress, len(self.get_sozais())))
        sound_time = max([get_sound_length(path) for path in anime_sounds]) / 30
        imgs_seqs = []
        progress_dialog = wx.ProgressDialog(
            title="動画出力",
            message="動画出力中...",
            maximum=len(anime_settings)+1,
            style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
        progress_dialog.Show()
        progress = 1
        progress_dialog.Update(
            progress,
            "キャラ素材ごとのフレーム整列: 開始中...")
        if sound_time > 0:
            for a, p, i, s in zip(anime_settings, ordered_parts, anime_dicts, anime_sounds):
                sound = s if s else None
                imgs_seq = a.get_anime_images_seq(p, i, sound=sound, take_time=sound_time, suffix_time=self.__suffix_time)
                imgs_seqs.append(imgs_seq)
                progress += 1
                progress_dialog.Update(
                    progress,
                    "キャラ素材ごとのフレーム整列: "
                    "{}/{}".format(progress, len(anime_settings)))
        else:
            for a, p, i in zip(anime_settings, ordered_parts, anime_dicts):
                imgs_seq = a.get_anime_images_seq(p, i, take_time=self.__movie_time, suffix_time=self.__suffix_time)
                imgs_seqs.append(imgs_seq)
                progress += 1
                progress_dialog.Update(
                    progress,
                    "キャラ素材ごとのフレーム整列: "
                    "{}/{}".format(progress, len(anime_settings)))
        root = self.__project.root_path() / "scene_block" / self.__uuid
        images_dir = root / "images"
        sound_dir = root / "sound"
        movie_dir = root / "movie"
        if not images_dir.exists():
            images_dir.mkdir()
        else:
            shutil.rmtree(images_dir)
            images_dir.mkdir()
        if not sound_dir.exists():
            sound_dir.mkdir()
        else:
            shutil.rmtree(sound_dir)
            sound_dir.mkdir()
        if not movie_dir.exists():
            movie_dir.mkdir()
        else:
            shutil.rmtree(movie_dir)
            movie_dir.mkdir()
        imgs_num = min([len(imgs) for imgs in imgs_seqs])
        digit_num = len(str(imgs_num))
        args = []
        queue = Manager().Queue()
        progress_dialog = wx.ProgressDialog(
            title="動画出力",
            message="動画出力中...",
            maximum=imgs_num,
            style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
        progress_dialog.Show()
        progress = 0
        for i in range(imgs_num):
            imgs = []
            for seq in imgs_seqs:
                imgs.append(seq[i])
            imgs = [get_rescaled_image(image, scale) for image, scale in zip(imgs, self.__sozai_scale)]
            bg_size = self.__project.resolution
            bg_color = self.__project.bg_color
            frame = get_scene_image(imgs, self.__sozai_pos, self.__sozai_order, bg_size=bg_size, bg_color=bg_color)
            args.append((frame, images_dir, i, digit_num, queue))
            progress += 1
            progress_dialog.Update(
                progress,
                "全てのキャラ素材アニメーションを統合: "
                "{}/{}".format(progress, imgs_num))

        p = Pool()
        r = p.map_async(save_anime_frame, args)

        progress_dialog = wx.ProgressDialog(
            title="動画出力",
            message="動画出力中...",
            maximum=len(args),
            style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
        progress_dialog.Show()
        progress = 0

        while not r.ready() or progress < len(args):
            for _ in range(queue.qsize()):
                progress += 1
                progress_dialog.Update(
                    progress,
                    "連番画像をキャッシュに保存中: {}\n\t{}/{}"
                    " フレーム".format(queue.get(), progress, len(args)))

        p.close()

        movie_path = movie_dir / "scene_movie.mp4"
        progress_dialog = wx.ProgressDialog(
            title="動画出力",
            message="動画出力中...",
            maximum=2,
            style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
        progress_dialog.Show()
        progress = 1
        progress_dialog.Update(progress, "動画出力中...")
        if sound_time > 0:
            sound_path = mix_movie_sounds(movie_sounds, str(FFMPEG_PATH), sound_dir)
            while not sound_path.exists():
                pass
            save_video(images_dir, sound_path, movie_path, str(FFMPEG_PATH))
        else:
            save_silent_video(images_dir, movie_path, str(FFMPEG_PATH))
        progress += 1
        progress_dialog.Update(progress, "完了")
        while not movie_path.exists():
            pass
        shutil.rmtree(images_dir)
        shutil.rmtree(sound_dir)
        self.movie_generated = True
        self.__movie_path = movie_path
        return movie_path
