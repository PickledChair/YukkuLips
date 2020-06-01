"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

from pathlib import Path
from uuid import uuid4
import shutil
import os
from copy import deepcopy

import wx

from .ykl_appsetting import YKLAppSetting
from .scene_block import SceneBlock
from .ykl_project import YKLProject
from media_utility.video_tool import make_mv_list_txt, concat_movies, FFMPEG_PATH


class YKLContext:
    def __init__(self, project_root):
        self.app_setting = YKLAppSetting()
        self.app_setting.load()
        self.__project = YKLProject(project_root)
        self.__scene_block_dic = {}
        self.__current_block = None
        self.ffmpeg_path = FFMPEG_PATH

        # scene_blockフォルダの作成
        scene_block_folder = self.__project.root_path() / "scene_block"
        if not scene_block_folder.exists():
            scene_block_folder.mkdir()

    def add_sozai(self, path):
        path = Path(path)
        new_uuid = str(uuid4())
        if self.__scene_block_dic:
            for scene_block in self.__scene_block_dic.values():
                scene_block.add_sozai(new_uuid, path)
        else:
            self.add_sceneblock(sozai_dic={new_uuid: path})
        self.__set_project_unsaved()

    def set_new_sozai(self, idx, sozai):
        current_block = self.__scene_block_dic[self.__current_block]
        current_block.set_new_sozai(idx, sozai)
        name = sozai.get_name()
        for block in self.__scene_block_dic.values():
            sozais = block.get_sozais()
            same_sozai = sozais[idx]
            if same_sozai.get_name() != name:
                same_sozai.set_name(name)
                # 結局同じキャラ素材オブジェクトを指定し直すだけなので、コピーを取らなくて良い
                block.set_new_sozai(idx, same_sozai)
        self.__set_project_unsaved()

    def remove_sozai(self, idx):
        for scene_block in self.__scene_block_dic.values():
            scene_block.remove_sozai(idx)
        self.__set_project_unsaved()

    def add_sceneblock(self, sozai_dic={}):
        new_uuid = str(uuid4())
        if self.__scene_block_dic:
            new_dic = {}
            block_uuids = list(self.__scene_block_dic.keys())
            current_idx = block_uuids.index(self.__current_block)
            new_sceneblock = self.__scene_block_dic[self.__current_block].get_copy(new_uuid)
            block_uuids.insert(current_idx+1, new_uuid)
            for b_uuid in block_uuids:
                if b_uuid == new_uuid:
                    new_dic[b_uuid] = new_sceneblock
                else:
                    new_dic[b_uuid] = self.__scene_block_dic[b_uuid]
            self.__scene_block_dic = new_dic
        else:
            self.__scene_block_dic[new_uuid] = SceneBlock(new_uuid, sozai_dic, self.__project)
        self.__current_block = new_uuid
        self.__set_project_unsaved()

    def set_new_sceneblock(self, block):
        self.__scene_block_dic[block.get_uuid()] = block
        self.__set_project_unsaved()

    def remove_sceneblock(self):
        idx = list(self.__scene_block_dic.keys()).index(self.__current_block)
        self.__scene_block_dic.pop(self.__current_block)
        if len(self.__scene_block_dic) == 0:
            self.__current_block = None
        else:
            self.__current_block = list(self.__scene_block_dic.keys())[min(idx, len(self.__scene_block_dic)-1)]
        self.__set_project_unsaved()

    def remove_sceneblocks_list(self, bool_list):
        self.__scene_block_dic = {
            item[0]: item[1] for checked, item in zip(bool_list, self.__scene_block_dic.items()) if not checked}
        if len(self.__scene_block_dic) == 0:
            self.__current_block = None
        elif self.__scene_block_dic.get(self.__current_block) is None:
            self.set_current_sceneblock(0)
        self.__set_project_unsaved()

    def get_sceneblocks(self):
        return list(self.__scene_block_dic.values())

    def unsaved_check(self):
        for block in self.get_sceneblocks():
            block.sozais_unsaved_check()
        if not all([block.is_saved() for block in self.get_sceneblocks()]):
            self.__set_project_unsaved()

    def get_current_sceneblock(self):
        return self.__scene_block_dic.get(self.__current_block)

    def get_project_path(self):
        return self.__project.root_path()

    def project_saved(self):
        return self.__project.is_saved()

    def __set_project_unsaved(self):
        self.__project.set_unsaved()

    def get_project_name(self):
        return self.__project.get_name()

    @property
    def resolution(self):
        return self.__project.resolution

    @resolution.setter
    def resolution(self, res):
        # projectのresolutionセッターで内部的にunsavedにしてある
        self.__project.resolution = res
        progress_dialog = wx.ProgressDialog(
            title="プロジェクト変更の反映",
            message="プロジェクト変更中...",
            maximum=len(self.__scene_block_dic),
            style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
        progress_dialog.Show()
        progress = 0
        for block in self.__scene_block_dic.values():
            block.update_scene_image()
            progress += 1
            progress_dialog.Update(
                progress,
                f"解像度の反映 {progress}/{len(self.__scene_block_dic)}")

    @property
    def bg_color(self):
        return self.__project.bg_color

    @bg_color.setter
    def bg_color(self, new_color):
        # projectのbg_colorセッターで内部的にunsavedにしてある
        self.__project.bg_color = new_color
        progress_dialog = wx.ProgressDialog(
            title="プロジェクト変更の反映",
            message="プロジェクト変更中...",
            maximum=len(self.__scene_block_dic),
            style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
        progress_dialog.Show()
        progress = 0
        for block in self.__scene_block_dic.values():
            block.update_scene_image()
            progress += 1
            progress_dialog.Update(
                progress,
                f"背景色の反映 {progress}/{len(self.__scene_block_dic)}")

    def open_project(self):
        sceneblock_list, sozai_resource_dic = self.__project.open()
        # parts_path_dicsを得るために、ダミーのシーンブロックを作成
        s1 = SceneBlock(sceneblock_list[0], sozai_resource_dic, self.__project)
        parts_path_dics = [cs.get_parts_path_dic() for cs in s1.get_sozais()]
        progress_dialog = wx.ProgressDialog(
            title="プロジェクト読込",
            message="プロジェクト読込中...",
            maximum=len(sceneblock_list),
            style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
        progress_dialog.Show()
        progress = 0
        self.__scene_block_dic = dict()
        for s in sceneblock_list:
            self.__scene_block_dic[s] = SceneBlock.open(
                s, deepcopy(sozai_resource_dic), self.__project, deepcopy(parts_path_dics))
            progress += 1
            progress_dialog.Update(
                progress,
                f"シーンブロック読込 {progress}/{len(sceneblock_list)}")
        self.set_current_sceneblock(0)

    def save_project(self):
        if self.__project.is_saved():
            return
        else:
            scene_block_folder = self.__project.root_path() / "scene_block"
            # シーンブロックの増減を反映してフォルダを削除
            items = [item.name for item in scene_block_folder.iterdir() if item.is_dir()]
            # print(items)
            delete_blocks = [item for item in items if item not in list(self.__scene_block_dic.keys())]
            # print(delete_blocks)
            for delete_block in delete_blocks:
                shutil.rmtree(scene_block_folder / delete_block)
        # プロジェクトに一つもシーンブロックがない場合、sozai_resource_dicの取得でリストの範囲外エラーが起きるので、
        # contextの保存を行わないようにする
        if len(self.__scene_block_dic) == 0:
            return
        for block in self.__scene_block_dic.values():
            block.save()
        self.__project.set_sceneblock_list(list(self.__scene_block_dic.keys()))
        self.__project.set_resource_path_dic(list(self.__scene_block_dic.values())[0].get_sozai_resource_dic())
        self.__project.save()

    def concat_movies(self, movie_path, check_list):
        # 動画未生成のシーンブロックがある場合、連結を行わない
        if not any(check_list):
            if not all([block.movie_generated for block in self.get_sceneblocks()]):
                return
        else:
            checked_blocks = [block for block, checked in zip(self.get_sceneblocks(), check_list) if checked]
            if not all([block.movie_generated for block in checked_blocks]):
                return
        pro_path = self.get_project_path()
        temp_path = pro_path / "temp"
        if not temp_path.exists():
            temp_path.mkdir()
        while not temp_path.exists():
            pass
        if Path(movie_path).exists():
            os.remove(movie_path)
        while Path(movie_path).exists():
            pass
        txt_path = temp_path / "mv_list.txt"
        if not any(check_list):
            mv_path_list = [block.movie_path for block in self.get_sceneblocks()]
        else:
            mv_path_list = [block.movie_path for block in checked_blocks]
        make_mv_list_txt(txt_path, mv_path_list)
        while not txt_path.exists():
            pass
        concat_movies(str(FFMPEG_PATH), txt_path, movie_path)
        while not Path(movie_path).exists():
            pass
        shutil.rmtree(temp_path)
        self.__set_project_unsaved()
        self.save_project()

    def set_current_sceneblock(self, idx):
        self.__current_block = list(self.__scene_block_dic.keys())[idx]
