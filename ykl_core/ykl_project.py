"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://opensource.org/licenses/mit-license.php
"""

import json
from typing import Dict, List
from pathlib import Path


class YKLProjectBuilder:
    def __init__(self):
        self.project = YKLProject()

    def set_project_name(self, name):
        self.project.contents["Project Name"] = name

    def set_sozai_dir(self, directory):
        self.project.contents["Sozai Directory"] = directory

    def set_current_images(self, current_images):
        for k, v in current_images.items():
            self.project.contents["Current Images"][k] = [str(path) for path in v]

    def set_bg_color(self, bg_color):
        for i, k in enumerate(self.project.contents["Background Color"]):
            self.project.contents["Background Color"][k] = bg_color.color_tuple[i]

    def set_mirror_flag(self, flag):
        self.project.contents["Mirror Image"] = flag

    def set_base_size(self, base_size):
        self.project.contents["Base Image Size"]["width"] = base_size[0]
        self.project.contents["Base Image Size"]["height"] = base_size[1]

    def set_audio_dir(self, audio_dir):
        self.project.contents["Audio Directory"] = audio_dir

    def set_is_silent(self, silent_flag):
        self.project.contents["Is Silent Movie"] = silent_flag

    def set_silent_interval(self, silent_interval):
        self.project.contents["Silent Interval"] = silent_interval

    def set_voice_interval(self, voice_interval):
        self.project.contents["Voice Interval"] = voice_interval

    def set_blink_interval(self, blink_interval):
        self.project.contents["Blink Interval"] = blink_interval

    def set_blink_type(self, blink_type):
        self.project.contents["Blink Type"] = blink_type

    def set_movie_size(self, movie_size):
        self.project.contents["Movie Size"] = movie_size.name

    def set_sozai_pos(self, sozai_pos):
        self.project.contents["Sozai Position"]["x"] = sozai_pos[0]
        self.project.contents["Sozai Position"]["y"] = sozai_pos[1]

    def set_sozai_scale(self, sozai_scale):
        self.project.contents["Sozai Scale"] = sozai_scale

    def set_bg_ref(self, bg_ref):
        if bg_ref is None:
            self.project.contents["BG Reference"] = bg_ref
        else:
            self.project.contents["BG Reference"] = str(bg_ref)

    def build(self):
        return self.project


class YKLProject:
    def __init__(self):
        image_dic: Dict[str, List[str]] = {}
        self.contents = {
            "Project Version": 0.1,
            "Project Name": "",
            "Sozai Directory": "",
            "Current Images": image_dic,
            "Background Color": {"R": 0, "G": 0, "B": 255, "A": 255},
            "Mirror Image": False,
            "Base Image Size": {"width": 400, "height": 400},
            "Audio Directory": "",
            "Is Silent Movie": False,
            "Silent Interval": 0.0,
            "Voice Interval": 0.8,
            "Blink Interval": 15.0,
            "Blink Type": 0,
            "Movie Size": "720p",
            "Sozai Position": {"x": 0, "y": 0},
            "Sozai Scale": 1.0,
            "BG Reference": None,
        }
        self.location = str(Path.home())

    def save_as(self, file_path):
        with open(file_path, 'w') as f:
            json.dump(self.contents, f, indent=4, ensure_ascii=False)
        self.location = file_path

    def save(self):
        with open(self.location, 'w') as f:
            json.dump(self.contents, f, indent=4, ensure_ascii=False)

    def open(self, file_path):
        with open(file_path, 'r') as f:
            self.contents = json.load(f)
        if self.contents["Project Version"] != 0.1:
            return False
        self.location = file_path
        return True
