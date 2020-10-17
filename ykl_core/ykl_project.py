"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

from pathlib import Path
import json

class YKLProject:
    def __init__(self, root_path):
        self.__root = Path(root_path)
        if not self.__root.exists():
            self.__root.mkdir()
        self.__resolution = (1920, 1080)
        self.__bg_color = (0, 0, 255, 255)
        self.__content = YKLProject.__initial_content(self.__resolution, self.__bg_color)
        self.__is_saved = True

    def root_path(self):
        return self.__root

    @staticmethod
    def __initial_content(resolution, bg_color):
        content = {
            "Project Version": 0.3,
            'SceneBlock List': [],
            'CharaSozai Resource Dict': {},
            'Resolution': list(resolution),
            'BG Color': list(bg_color),
        }
        return content

    def open(self):
        with (self.root_path() / "project.json").open('r') as f:
            content = json.load(f)
        self.__content = content
        sceneblock_list = content["SceneBlock List"]
        sozai_resource_dic = content["CharaSozai Resource Dict"]
        sozai_resource_dic = {k: Path(v) for k, v in sozai_resource_dic.items()}
        self.__resolution = tuple(content["Resolution"])
        self.__bg_color = tuple(content["BG Color"])
        self.__is_saved = True
        return sceneblock_list, sozai_resource_dic

    def is_saved(self):
        return self.__is_saved

    def set_unsaved(self):
        self.__is_saved = False

    def get_name(self):
        return self.__root.name

    def set_sceneblock_list(self, l):
        self.__content['SceneBlock List'] = l

    def set_resource_path_dic(self, d):
        d = {k: str(v) for k, v in d.items()}
        self.__content['CharaSozai Resource Dict'] = d

    @property
    def resolution(self):
        return self.__resolution

    @resolution.setter
    def resolution(self, res):
        self.__resolution = res
        self.__content['Resolution'] = list(res)
        self.__is_saved = False

    @property
    def bg_color(self):
        return self.__bg_color

    @bg_color.setter
    def bg_color(self, bg_color):
        self.__bg_color = bg_color
        self.__content['BG Color'] = list(bg_color)
        self.__is_saved

    def save(self):
        proj_file_path = self.__root / 'project.json'
        with proj_file_path.open('w') as f:
            json.dump(self.__content, f, indent=4, ensure_ascii=False)
        self.__is_saved = True
