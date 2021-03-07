"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

import subprocess
from collections import namedtuple
from pathlib import Path
import sys

from media_utility.audio_tool import get_sound_map, get_sound_length, gen_void_sound

MovieSize = namedtuple("MovieSize", ("name", "size_tuple"))

FFMPEG_PATH = Path.cwd() / "FFmpeg" / "ffmpeg"

if getattr(sys, 'frozen', False):
    # frozen は PyInstaller でこのスクリプトが固められた時に sys に追加される属性
    # frozen が見つからない時は素の Python で実行している時なので False を返す
    bundle_dir = sys._MEIPASS
    FFMPEG_PATH = Path(bundle_dir) / "FFmpeg" / "ffmpeg"


def save_video(cache_path, sound_file, save_file_path, ffmpeg_path):
    # 音声を動画の長さまで引き伸ばすオプションを-filter_complexで指定している
    # cf. https://superuser.com/questions/801547/ffmpeg-add-audio-but-keep-video-length-the-same-not-shortest
    p = subprocess.Popen([ffmpeg_path, "-f", "image2", "-pattern_type", "glob", "-framerate", "30",
                          "-i", str(cache_path / "*.png"),
                          "-i", str(sound_file),
                          "-pix_fmt", "yuv420p", "-qscale", "0",
                          "-filter_complex", "[1:0] apad", "-shortest",
                          str(save_file_path)])
    p.wait()


def save_silent_video(cache_path, save_file_path, ffmpeg_path):
    sound_file = cache_path / "void_sound.wav"
    gen_void_sound(sound_file)
    p = subprocess.Popen([ffmpeg_path, "-f", "image2", "-pattern_type", "glob", "-framerate", "30",
                          "-i", str(cache_path / "*.png"),
                          "-i", str(sound_file),
                          "-pix_fmt", "yuv420p", "-qscale", "0",
                          "-filter_complex", "[1:0] apad", "-shortest",
                          str(save_file_path)])
    p.wait()

def make_mv_list_txt(txt_path, mv_path_list):
    txt = ""
    for mv_path in mv_path_list:
        txt += "file " + str(mv_path) + "\n"
    with open(txt_path, "w") as f:
        f.write(txt)

def concat_movies(ffmpeg_path, mv_list_txt_path, save_path):
    p = subprocess.Popen([ffmpeg_path, "-f", "concat", "-safe", "0", "-i", str(mv_list_txt_path),
                          "-c:v", "copy", "-c:a", "copy", "-c:s", "copy",
                          "-map", "0:v", "-map", "0:a", "-map", "0:s?",
                          str(save_path)])


from enum import Enum, auto

class AnimeType(Enum):
    NOTHING = auto()              # なし
    VOLUME_FOLLOW = auto()        # 台詞音量型
    CYCLE_ROUND = auto()          # 定期往復型
    CYCLE_ONEWAY = auto()         # 定期片道型
    COME_LEAVE = auto()           # 登場退場型
    COME_ROUND = auto()           # 登場往復型
    COME_ONEWAY = auto()          # 登場片道型
    LEAVE_ROUND = auto()          # 退場往復型
    LEAVE_ONEWAY = auto()         # 退場片道型

    @staticmethod
    def get_labels():
        return ["なし",
                "台詞音量型",
                "定期往復型",
                "定期片道型",
                "登場退場型",
                "登場往復型",
                "登場片道型",
                "退場往復型",
                "退場片道型"]

    @staticmethod
    def from_str(string):
        if string == "VOLUME_FOLLOW" or string == "台詞音量型":
            return AnimeType.VOLUME_FOLLOW
        elif string == "CYCLE_ROUND" or string == "定期往復型":
            return AnimeType.CYCLE_ROUND
        elif string == "CYCLE_ONEWAY" or string == "定期片道型":
            return AnimeType.CYCLE_ONEWAY
        elif string == "COME_LEAVE" or string == "登場退場型":
            return AnimeType.COME_LEAVE
        elif string == "COME_ROUND" or string == "登場往復型":
            return AnimeType.COME_ROUND
        elif string == "COME_ONEWAY" or string == "登場片道型":
            return AnimeType.COME_ONEWAY
        elif string == "LEAVE_ROUND" or string == "退場往復型":
            return AnimeType.LEAVE_ROUND
        elif string == "LEAVE_ONEWAY" or string == "退場片道型":
            return AnimeType.LEAVE_ONEWAY
        else:
            return AnimeType.NOTHING

    def get_anime_generator(self):
        if self.name == "VOLUME_FOLLOW":
            def gen_volume_follow(sound_file, imgs_num, threshold, line, sizing):
                if sound_file:
                    sound_level_seq = get_sound_map(
                        sound_file, imgs_num,
                        threshold_ratio=threshold, line=line, sizing=sizing)
                    if sound_level_seq:
                        for i in sound_level_seq:
                            yield i
                while True:
                    yield 0
            return gen_volume_follow
        elif self.name == "CYCLE_ROUND":
            def gen_cycle_round(start, imgs_num, take_time, hold, interval, length):
                _count = 0
                for _ in range(int(start*30)):
                    _count += 1
                    yield 0
                anime_seq_up = [round((imgs_num-1)/(take_time/2*30)*i) for i in range(int(take_time/2*30))]
                anime_seq_down = list(reversed(anime_seq_up))
                status = "interval"
                anime_frame_num = len(anime_seq_up)*2 + hold
                while True:
                    if status == "up":
                        if length - _count < anime_frame_num:
                            status = "interval"
                            continue
                        for i in anime_seq_up:
                            _count += 1
                            yield i
                        status = "hold"
                    elif status == "hold":
                        for _ in range(hold):
                            _count += 1
                            yield imgs_num - 1
                        status = "down"
                    elif status == "down":
                        for i in anime_seq_down:
                            _count += 1
                            yield i
                        status = "interval"
                    elif status == "interval":
                        for _ in range(int(interval*30) - anime_frame_num):
                            _count += 1
                            yield 0
                        status = "up"
            return gen_cycle_round
        elif self.name == "CYCLE_ONEWAY":
            def gen_cycle_oneway(start, imgs_num, take_time, hold, interval, length):
                _count = 0
                for _ in range(int(start*30)):
                    _count += 1
                    yield 0
                anime_seq = [round((imgs_num-1)/(take_time*30)*i) for i in range(int(take_time*30))]
                status = "interval"
                anime_frame_num = len(anime_seq) + hold
                while True:
                    if status == "interval":
                        for _ in range(int(interval*30)-anime_frame_num):
                            _count += 1
                            yield 0
                        status = "up"
                    elif status == "up":
                        if length - _count < anime_frame_num:
                            status = "interval"
                            continue
                        for i in anime_seq:
                            _count += 1
                            yield i
                        status = "hold"
                    elif status == "hold":
                        for _ in range(hold):
                            _count += 1
                            yield imgs_num - 1
                        status = "interval"
            return gen_cycle_oneway
        elif self.name == "COME_LEAVE":
            def gen_come_leave(start, imgs_num, take_time, length):
                for _ in range(int(start)*30):
                    yield 0
                    length -= 1
                anime_seq_up = [round((imgs_num-1)/(take_time*30)*i) for i in range(int(take_time*30))]
                anime_seq_down = list(reversed(anime_seq_up))
                for i in anime_seq_up:
                    yield i
                    length -= 1
                for _ in range(length-len(anime_seq_down)):
                    yield imgs_num - 1
                for i in anime_seq_down:
                    yield i
                while True:
                    yield 0
            return gen_come_leave
        elif self.name == "COME_ROUND":
            def gen_come_round(start, imgs_num, take_time, hold):
                for _ in range(int(start*30)):
                    yield 0
                anime_seq_up = [round((imgs_num-1)/(take_time/2*30)*i) for i in range(int(take_time/2*30))]
                anime_seq_down = list(reversed(anime_seq_up))
                for i in anime_seq_up:
                    yield i
                for _ in range(hold):
                    yield imgs_num - 1
                for i in anime_seq_down:
                    yield i
                while True:
                    yield 0
            return gen_come_round
        elif self.name == "COME_ONEWAY":
            def gen_come_oneway(start, imgs_num, take_time):
                for _ in range(int(start*30)):
                    yield 0
                anime_seq_up = [round((imgs_num-1)/(take_time*30)*i) for i in range(int(take_time*30))]
                for i in anime_seq_up:
                    yield i
                while True:
                    yield imgs_num - 1
            return gen_come_oneway
        elif self.name == "LEAVE_ROUND":
            def gen_leave_round(start, imgs_num, take_time, hold, length):
                for _ in range(int(start*30)):
                    yield 0
                    length -= 1
                anime_seq_up = [round((imgs_num-1)/(take_time/2*30)*i) for i in range(int(take_time/2*30))]
                anime_seq_down = list(reversed(anime_seq_up))
                for _ in range(length-(len(anime_seq_up)*2+hold)):
                    yield 0
                for i in anime_seq_up:
                    yield i
                for _ in range(hold):
                    yield imgs_num - 1
                for i in anime_seq_down:
                    yield i
                while True:
                    yield 0
            return gen_leave_round
        elif self.name == "LEAVE_ONEWAY":
            def gen_leave_oneway(start, imgs_num, take_time, length):
                for _ in range(int(start*30)):
                    yield 0
                    length -= 1
                anime_seq_up = [round((imgs_num-1)/(take_time*30)*i) for i in range(int(take_time*30))]
                for _ in range(length-len(anime_seq_up)):
                    yield 0
                for i in anime_seq_up:
                    yield i
                while True:
                    yield imgs_num - 1
            return gen_leave_oneway
        else:
            def gen_nothing():
                while True:
                    yield 0
            return gen_nothing

class LineShape(Enum):
    LINEAR = auto()
    QUADRATIC = auto()

    @staticmethod
    def from_str(string):
        if string == "LINEAR" or string == "一次直線":
            return LineShape.LINEAR
        else:
            return LineShape.QUADRATIC

    def get_funcs(self):
        if self.name == "LINEAR":
            return lambda x: x / 2, lambda x: abs(x)
        elif self.name == "QUADRATIC":
            return lambda x: x ** 2 / 2, lambda x: x ** 2

class PartAnimeSetting:
    def __init__(self, partname, imgs_num):
        self.part = partname
        self.anime_type = AnimeType.NOTHING
        self.imgs_num = imgs_num
        self.start = 0.0
        self.interval = 5.0
        self.take_time = 0.5
        self.stop_frames = 2
        self.sound_threshold = 1.0
        self.line_shape = LineShape.LINEAR

    def get_gen_obj(self, length=30*60, sound=None):
        # print(self.anime_type)
        if self.anime_type == AnimeType.NOTHING:
            return self.anime_type.get_anime_generator()()
        elif self.anime_type == AnimeType.VOLUME_FOLLOW:
            line, sizing = self.line_shape.get_funcs()
            return self.anime_type.get_anime_generator()(sound, self.imgs_num, self.sound_threshold, line, sizing)
        elif self.anime_type == AnimeType.CYCLE_ROUND:
            return self.anime_type.get_anime_generator()(
                self.start, self.imgs_num, self.take_time, self.stop_frames, self.interval, length)
        elif self.anime_type == AnimeType.CYCLE_ONEWAY:
            return self.anime_type.get_anime_generator()(
                self.start, self.imgs_num, self.take_time, self.stop_frames, self.interval, length)
        elif self.anime_type == AnimeType.COME_LEAVE:
            return self.anime_type.get_anime_generator()(
                self.start, self.imgs_num, self.take_time, length)
        elif self.anime_type == AnimeType.COME_ROUND:
            return self.anime_type.get_anime_generator()(
                self.start, self.imgs_num, self.take_time, self.stop_frames)
        elif self.anime_type == AnimeType.COME_ONEWAY:
            return self.anime_type.get_anime_generator()(
                self.start, self.imgs_num, self.take_time)
        elif self.anime_type == AnimeType.LEAVE_ROUND:
            return self.anime_type.get_anime_generator()(
                self.start, self.imgs_num, self.take_time, self.stop_frames, length)
        elif self.anime_type == AnimeType.LEAVE_ONEWAY:
            return self.anime_type.get_anime_generator()(
                self.start, self.imgs_num, self.take_time, length)

class AnimeSetting:
    def __init__(self, anime_count_dict):
        self.part_settings = {part: PartAnimeSetting(part, _count) for part, _count in anime_count_dict.items()}

    def into_json(self):
        return {part.part: {
            "Anime Type": part.anime_type.name,
            "Start Time": part.start,
            "Interval": part.interval,
            "Take Time": part.take_time,
            "Hold Frame": part.stop_frames,
            "Threshold": part.sound_threshold,
            "Line Shape": part.line_shape.name,
            } for part in self.part_settings.values()}

    def get_anime_images_seq(self, part_order, images_dict, sound=None, take_time=1., suffix_time=0.):
        # print(part_order, list(self.part_settings.keys()))
        result = []
        if sound:
            sound_anime_parts = [part for part in self.part_settings if self.part_settings[part].anime_type == AnimeType.VOLUME_FOLLOW]
            # 音源は指定されているが台詞音量型アニメが指定されていない時がある
            # その時、便宜的にadd_timeはsuffix_timeと同じ値を指定する
            if len(sound_anime_parts) == 0:
                add_time = suffix_time
            else:
                add_time = max([self.part_settings[part].start for part in sound_anime_parts]) + suffix_time
            length = get_sound_length(sound, add_time=add_time)
            gen_list = [self.part_settings[part].get_gen_obj(sound=sound, length=length) for part in part_order]
            image = images_dict
            for _ in range(length):
                for gen in gen_list:
                    image = image[next(gen)]
                result.append(image)
                image = images_dict
            return result
        else:
            length = round((take_time+suffix_time)*30)
            gen_list = [self.part_settings[part].get_gen_obj(length=length) for part in part_order]
            image = images_dict
            for _ in range(length):
                for gen in gen_list:
                    image = image[next(gen)]
                result.append(image)
                image = images_dict
            return result
