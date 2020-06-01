"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

import json
from pathlib import Path
from copy import deepcopy
import shutil

from media_utility.image_tool import combine_images, get_mirror_image, ImageInfo
from media_utility.video_tool import AnimeType, LineShape, AnimeSetting, FFMPEG_PATH
from media_utility.audio_tool import gen_movie_sound, convert_mp3_to_wav


class CharaSozai:
    def __init__(self, cs_uuid, sb_uuid, project, resource_path, parts_path_dic={}):
        self.__uuid = cs_uuid
        self.__sb_uuid = sb_uuid
        self.__project = project

        # キャラ素材画像のデータ
        self.__resource_path = resource_path
        self.__name = self.__resource_path.name
        if parts_path_dic:
            self.__parts_dirs, self.__parts_path_dic = [resource_path / part for part in parts_path_dic.keys()], parts_path_dic
        else:
            self.__parts_dirs, self.__parts_path_dic = CharaSozai.__get_image_paths(self.__resource_path)
        self.__current_image_dic = self.__set_default_images()
        self.__is_mirror_img = False
        self.__image = self.__integrate_images()

        # セリフ
        self.__speech_content = ""
        self.__anime_audio_path = ""
        self.__movie_audio_path = ""
        self.__prestart_time = 0.0

        # アニメーション
        self.__anime_setting = self.__get_initial_anime_setteing(*self.get_anime_image_dict())

        self.__content = CharaSozai.__initial_content(self.__name, self.__current_image_dic, self.__anime_setting)
        self.__is_saved = False

    @staticmethod
    def __get_initial_anime_setteing(orderd_parts, anime_image_dict):
        count_dict = CharaSozai.get_count_of_each_part_images_dict(orderd_parts, anime_image_dict)
        parts = ['体', '顔', '髪', '眉', '目', '口', '髪(透明)', '他', '前側', '後側']
        anime_types = ["NOTHING",
                       "NOTHING",
                       "NOTHING",
                       "NOTHING",
                       "CYCLE_ROUND",
                       "VOLUME_FOLLOW",
                       "NOTHING",
                       "NOTHING",
                       "NOTHING",
                       "NOTHING",
                       ]
        start_times = [0.0 for _ in range(len(parts))]
        intervals = [5.0 for _ in range(len(parts))]
        take_times = [0.5 for _ in range(len(parts))]
        hold_frames = [2 for _ in range(len(parts))]
        thresholds = [1.0 for _ in range(len(parts))]
        line_shapes = ["LINEAR" for _ in range(len(parts))]
        initial_dict = {
            part: {
                "Anime Type": anime_type,
                "Start Time": start_time,
                "Interval": interval,
                "Take Time": take_time,
                "Hold Frame": hold_frame,
                "Threshold": threshold,
                "Line Shape": line_shape,
            } for part, anime_type, start_time, interval, take_time, hold_frame, threshold, line_shape
            in zip(parts, anime_types, start_times, intervals, take_times, hold_frames, thresholds, line_shapes)
        }
        initial_dict = {k: value for k, value in initial_dict.items() if count_dict.get(k)}
        return {k: value for k, value in initial_dict.items() if count_dict[k] > 1}

    def create_anime_setting(self):
        count_dict = self.get_count_of_each_part_images_dict(*self.get_anime_image_dict())
        anime_setting = AnimeSetting(count_dict)
        for part in anime_setting.part_settings.values():
            if self.__anime_setting.get(part.part):
                part.anime_type = AnimeType.from_str(self.__anime_setting[part.part]["Anime Type"])
                part.start = self.__anime_setting[part.part]["Start Time"]
                part.interval = self.__anime_setting[part.part]["Interval"]
                part.take_time = self.__anime_setting[part.part]["Take Time"]
                part.stop_frames = self.__anime_setting[part.part]["Hold Frame"]
                part.sound_threshold = self.__anime_setting[part.part]["Threshold"]
                part.line_shape = LineShape.from_str(self.__anime_setting[part.part]["Line Shape"])
        return anime_setting

    def set_anime_setting(self, anime_setting):
        self.__anime_setting = anime_setting.into_json()
        self.__content["Anime Setting"] = self.__anime_setting
        self.__is_saved = False

    def get_movie_anime_audio(self):
        if self.__movie_audio_path == "" or self.__anime_audio_path == "":
            return None, None
        root = (self.__project.root_path()
                / "scene_block" / self.__sb_uuid
                / "chara_sozai" / self.__uuid)
        sound_dir = root / "sound"
        if not sound_dir.exists():
            sound_dir.mkdir()
        else:
            shutil.rmtree(sound_dir)
            sound_dir.mkdir()
        if Path(self.__movie_audio_path).suffix.lower() == ".mp3":
            movie_audio_path = convert_mp3_to_wav(Path(self.__movie_audio_path), str(FFMPEG_PATH), sound_dir)
        else:
            movie_audio_path = Path(self.__movie_audio_path)
        movie_audio_path = gen_movie_sound(Path(movie_audio_path), str(FFMPEG_PATH), sound_dir, prefix_time=self.__prestart_time)
        if Path(self.__anime_audio_path).suffix.lower() == ".mp3":
            anime_audio_path = convert_mp3_to_wav(Path(self.__anime_audio_path), str(FFMPEG_PATH), sound_dir)
        else:
            anime_audio_path = Path(self.__anime_audio_path)
        anime_audio_path = gen_movie_sound(Path(anime_audio_path), str(FFMPEG_PATH), sound_dir, prefix_time=self.__prestart_time)
        while not (movie_audio_path.exists() and anime_audio_path.exists()):
            pass

        return movie_audio_path, anime_audio_path

    @staticmethod
    def __into_str_dic(image_dic):
        str_dic = {}
        for part, paths in image_dic.items():
            str_dic[part] = [str(path) for path in paths]
        return str_dic

    @staticmethod
    def __from_str_dic(str_dic):
        image_dic = {}
        for part, paths in str_dic.items():
            image_dic[part] = [Path(path) for path in paths]
        return image_dic

    @staticmethod
    def __initial_content(name, image_dic, anime_dict):
        str_dic = CharaSozai.__into_str_dic(image_dic)
        content = {
            "Name": name,
            "Speech Content": "",
            "Anime Audio Path": "",
            "Movie Audio Path": "",
            "Is Mirror Image": False,
            "Image Dict": str_dic,
            "Prestart Time": 0.0,
            "Anime Setting": anime_dict,
        }
        return content

    @staticmethod
    def open(cs_uuid, sb_uuid, project, resource_path, parts_path_dic={}):
        sozai = CharaSozai(cs_uuid, sb_uuid, project, resource_path, parts_path_dic=parts_path_dic)
        with (project.root_path() / "scene_block" / sb_uuid / "chara_sozai" / cs_uuid / "charasozai.json").open('r') as f:
            content = json.load(f)
        sozai.__restore(content)
        return sozai

    def __restore(self, content):
        self.__name = content.get("Name", "")
        self.__speech_content = content.get("Speech Content", "")
        self.__anime_audio_path = content.get("Anime Audio Path", "")
        self.__movie_audio_path = content.get("Movie Audio Path", "")
        self.__prestart_time = content.get("Prestart Time", 0.0)
        self.__is_mirror_img = content.get("Is Mirror Image", False)
        self.__current_image_dic = CharaSozai.__from_str_dic(content["Image Dict"])
        if self.__is_mirror_img:
            self.__image = self.__integrate_images(mirror_flag=self.__is_mirror_img)
        else:
            self.__image = self.__integrate_images()
        self.__anime_setting = content.get("Anime Setting", self.__get_initial_anime_setteing(*self.get_anime_image_dict()))
        self.__content = content
        self.__is_saved = True

    @staticmethod
    def __get_image_paths(base_dir):
        part_dirs = list(filter(lambda d: d.is_dir(), base_dir.iterdir()))
        images_dic = {}
        for part in part_dirs:
            part_images = sorted(part.glob("*.png"))
            images_dic[part.name] = {}
            if part.name == "後":
                images_dic[part.name]["前側"] = {}
                images_dic[part.name]["後側"] = {}
                counted = 0
                i = 0
                while counted < len(part_images):
                    m_images = [image for image in part_images if (image.name[:2] == f"{i:02}") and (image.name[2] == 'm')]
                    u_images = [image for image in part_images if (image.name[:2] == f"{i:02}") and (image.name[2] != 'm')]
                    if len(m_images) == 0 and len(u_images) == 0:
                        if len(part_images) == 0:
                            break
                        else:
                            i += 1
                            continue
                    else:
                        if len(m_images) != 0 or len(u_images) != 0:
                            images_dic[part.name]["前側"][f"{i:02}"] = m_images
                            images_dic[part.name]["後側"][f"{i:02}"] = u_images
                            counted += len(m_images) + len(u_images)
                    i += 1
            else:
                if part.name == "全":
                    if part_images:
                        series = part_images[0].name[:2]
                        images_dic[part.name] = {}
                        images_dic[part.name][series] = part_images
                    continue
                counted = 0
                i = 0
                while counted < len(part_images):
                    images = [image for image in part_images if image.name[:2] == f"{i:02}"]
                    if len(images) == 0:
                        if len(part_images) == 0:
                            break
                        else:
                            i += 1
                            continue
                    else:
                        images_dic[part.name][f"{i:02}"] = images
                        counted += len(images)
                    i += 1
        return part_dirs, images_dic

    def __set_default_images(self):
        images_dic = {}
        for part in self.__parts_dirs:
            default_images = []
            if len(self.__parts_path_dic[part.name]) > 0:
                if part.name == "後":
                    m_series = list(self.__parts_path_dic[part.name]["前側"].values())
                    u_series = list(self.__parts_path_dic[part.name]["後側"].values())
                    default_images.append((u_series[0] + m_series[0])[0])
                else:
                    default_images.append(list(self.__parts_path_dic[part.name].values())[0][0])
                if "00" not in str(default_images[0]) or part.name == '全':
                    default_images = []
            images_dic[part.name] = default_images
        images_dic["髪(透明)"] = []
        if '髪' in [part.name for part in self.__parts_dirs]:
            if self.__parts_path_dic['髪'].get("01"):
                images_dic["髪(透明)"].append(self.__parts_path_dic['髪']["01"][0])
                # ここでself.__parts_path_dicを編集しているので副作用がある
                self.__parts_path_dic['髪'].pop("01")
            elif self.__parts_path_dic['髪'].get("00"):
                images_dic["髪(透明)"].append(self.__parts_path_dic['髪']["00"][0])
        return images_dic

    def set_part_paths(self, part, series_num, indices, front_indices=[]):
        if part == "後":
            u_list = [self.__parts_path_dic[part]["後側"][series_num][idx] for idx in indices]
            m_list = [self.__parts_path_dic[part]["前側"][series_num][idx] for idx in front_indices]
            self.__current_image_dic[part] = u_list + m_list
        else:
            self.__current_image_dic[part] = [self.__parts_path_dic[part][series_num][idx] for idx in indices]
        self.__image = self.__integrate_images(mirror_flag=self.__is_mirror_img)
        self.__content["Image Dict"] = CharaSozai.__into_str_dic(self.__current_image_dic)
        new_anime_setting = self.__get_initial_anime_setteing(*self.get_anime_image_dict())
        previous_setting = {k: v for k, v in self.__anime_setting.items() if k in list(new_anime_setting.keys())}
        new_anime_setting.update(previous_setting)
        self.__anime_setting = new_anime_setting
        self.__content["Anime Setting"] = self.__anime_setting
        self.__is_saved = False

    def __integrate_images(self, base_size=(400, 400), mirror_flag=False):
        image_infos = CharaSozai.__sort_images(self.__current_image_dic)
        image = combine_images(*image_infos, bg_color=(0, 0, 0, 0))
        if mirror_flag:
            image = get_mirror_image(image)
        return image

    def is_mirror_img(self):
        return self.__is_mirror_img

    def set_mirror_img(self, b):
        self.__image = self.__integrate_images(mirror_flag=b)
        self.__is_mirror_img = b
        self.__content["Is Mirror Image"] = self.__is_mirror_img
        self.__is_saved = False

    def get_image(self):
        return self.__image

    def get_anime_image_dict(self, image_elements=False):
        if self.__current_image_dic['全']:
            ordered_parts = ['全',]
            if image_elements:
                anime_image_dict = {0: self.__image,}
            else:
                anime_image_dict = {0: None,}
            return ordered_parts, anime_image_dict
        images_order = ('体', '顔', '髪', '眉', '目', '口', '髪(透明)', '他', '前側', '後側')
        series_dict = {}
        for part in self.__current_image_dic:
            if part == "後":
                for image_path in self.__current_image_dic["後"]:
                    if 'm1' in image_path.name:
                        series_dict['前側'] = image_path.name[:2]
                    else:
                        series_dict['後側'] = image_path.name[:2]
            else:
                for image_path in self.__current_image_dic[part]:
                    series_dict[part] = image_path.name[:2]
        ordered_parts = [name for name in images_order if name in list(series_dict.keys())]
        # print(series_dict)
        # print(ordered_parts)
        front_temp = []
        def image_create(part, series, idx, _dict, create=True):
            # print(part, series, idx)
            if create and image_elements:
                if part == "前側":
                    self.set_part_paths("後", series, [], front_indices=[idx,])
                    front_temp = [idx,]
                elif part == "後側":
                    self.set_part_paths("後", series, [idx,], front_indices=front_temp)
                else:
                    self.set_part_paths(part, series, [idx,])
            current_idx = ordered_parts.index(part)
            if current_idx == len(ordered_parts)-1 and image_elements:
                _dict[idx] = deepcopy(self.get_image())
            elif current_idx == len(ordered_parts)-1 and (not image_elements):
                _dict[idx] = None
            else:
                next_part = ordered_parts[current_idx+1]
                _dict[idx] = dict()
                next_dict = _dict[idx]
                if next_part in ['前側', '後側']:
                    part_series = self.__parts_path_dic.get('後')
                    if part_series:
                        part_series = part_series.get(next_part)
                        if part_series:
                            _part_series = part_series.get(series_dict[next_part])
                            if _part_series:
                                for i in range(len(self.__parts_path_dic['後'][next_part][series_dict[next_part]])):
                                    image_create(next_part, series_dict[next_part], i, next_dict)
                        else:
                            image_create(next_part, "", 0, next_dict, create=False)
                else:
                    part_series = self.__parts_path_dic.get(next_part)
                    if part_series:
                        _part_series = part_series.get(series_dict[next_part])
                        if _part_series:
                            for i in range(len(self.__parts_path_dic[next_part][series_dict[next_part]])):
                                image_create(next_part, series_dict[next_part], i, next_dict)
                    else:
                        image_create(next_part, "", 0, next_dict, create=False)
        anime_image_dict = {}
        start_part = ordered_parts[0]
        start_series = series_dict[start_part]
        start_num = len(self.__parts_path_dic[start_part][start_series])
        for i in range(start_num):
            image_create(start_part, start_series, i, anime_image_dict)
        return ordered_parts, anime_image_dict

    @staticmethod
    def get_count_of_each_part_images_dict(parts, anime_dict):
        count_dict = dict()
        for part in parts:
            count_dict[part] = len(anime_dict)
            anime_dict = list(anime_dict.values())[0]
        return count_dict

    @staticmethod
    def __sort_images(current_image_dic):
        image_infos = []
        images_order = ('後', '体', '顔', '髪', '眉', '目', '口', '髪(透明)', '他')
        if '全' in list(current_image_dic.keys()):
            if len(current_image_dic['全']) != 0:
                image_infos.append(ImageInfo(path=current_image_dic['全'][0],
                                             part='全', is_mul=False, is_front=False))
                return image_infos
        for part in images_order:
            if part in list(current_image_dic.keys()):
                if len(current_image_dic[part]) != 0:
                    if part == '顔':
                        for path in current_image_dic[part]:
                            if 'b' in path.name:
                                image_infos.append(ImageInfo(path=path,
                                                             part=part, is_mul=True, is_front=False))
                            else:
                                image_infos.append(ImageInfo(path=path,
                                                             part=part, is_mul=False, is_front=False))
                    elif part == '後':
                        for path in current_image_dic[part]:
                            if 'm1' in path.name:
                                image_infos.append(ImageInfo(path=path,
                                                             part=part, is_mul=False, is_front=True))
                            else:
                                image_infos.append(ImageInfo(path=path,
                                                             part=part, is_mul=False, is_front=False))
                    else:
                        for path in current_image_dic[part]:
                            image_infos.append(ImageInfo(path=path,
                                                         part=part, is_mul=False, is_front=False))
        return image_infos

    def get_parts_path_dic(self):
        return self.__parts_path_dic

    def get_current_image_dic(self):
        return self.__current_image_dic

    def get_name(self):
        return self.__name

    def set_name(self, name):
        self.__name = name
        self.__content["Name"] = self.__name
        self.__is_saved = False

    def get_uuid(self):
        return self.__uuid

    def set_sb_uuid(self, new_uuid):
        self.__sb_uuid = new_uuid
        self.__is_saved = False

    @property
    def speech_content(self):
        return self.__speech_content

    @speech_content.setter
    def speech_content(self, speech):
        self.__speech_content = speech
        self.__content["Speech Content"] = self.__speech_content
        self.__is_saved = False

    @property
    def anime_audio_path(self):
        return self.__anime_audio_path

    @anime_audio_path.setter
    def anime_audio_path(self, new_path):
        self.__anime_audio_path = str(new_path)
        self.__content["Anime Audio Path"] = self.__anime_audio_path
        self.__is_saved = False

    @property
    def movie_audio_path(self):
        return self.__movie_audio_path

    @movie_audio_path.setter
    def movie_audio_path(self, new_path):
        self.__movie_audio_path = str(new_path)
        self.__content["Movie Audio Path"] = self.__movie_audio_path
        self.__is_saved = False

    @property
    def prestart_time(self):
        return self.__prestart_time

    @prestart_time.setter
    def prestart_time(self, new_time):
        self.__prestart_time = new_time
        self.__content["Prestart Time"] = self.__prestart_time
        self.__is_saved = False

    def save(self):
        root = (self.__project.root_path()
                / "scene_block" / self.__sb_uuid
                / "chara_sozai" / self.__uuid)
        # image_folder = root / "image"
        if not root.exists():
            root.mkdir()
            # image_folder.mkdir()
        else:
            if self.__is_saved:
                return
        sozai_file_path = root / "charasozai.json"
        # print(self.__content)
        with sozai_file_path.open('w') as f:
            json.dump(self.__content, f, indent=4, ensure_ascii=False)
        self.__is_saved = True

    def is_saved(self):
        return self.__is_saved
