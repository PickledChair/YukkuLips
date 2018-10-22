"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx


class CharaSozai:
    def __init__(self, sozai_dir):
        self.base_dir = sozai_dir
        self.part_dirs, self.images_dic = self.__get_image_paths(self.base_dir)
        self.thumbnails_dic = self.__get_thumbnails_dic()

    @staticmethod
    def __get_image_paths(base_dir):
        part_dirs = list(filter(lambda d: d.is_dir(), base_dir.iterdir()))
        images_dic = {}
        for part in part_dirs:
            part_images = sorted(part.glob("*.png"))
            images_dic[part.name] = part_images
        return part_dirs, images_dic

    def __get_thumbnails_dic(self):
        thumbnails_dic = {}
        image_count = 0
        progress = 0
        for v in self.images_dic.values():
            image_count += len(v)
        progress_dialog = wx.ProgressDialog(
            title="パーツ選択ダイアログ用のサムネイル作成",
            message="作成中...",
            maximum=image_count,
            style=wx.PD_APP_MODAL
                  | wx.PD_SMOOTH
                  | wx.PD_AUTO_HIDE)
        progress_dialog.Show()
        for part in self.part_dirs:
            for image_path in self.images_dic[part.name]:
                image = wx.Image(str(image_path))
                scale = (int(image.GetWidth() / max(image.GetWidth(), image.GetHeight()) * 200),
                         int(image.GetHeight() / max(image.GetWidth(), image.GetHeight()) * 200))
                image = image.Scale(scale[0], scale[1])
                bmp = image.ConvertToBitmap()
                thumbnails_dic[image_path] = bmp
                progress += 1
                progress_dialog.Update(progress, "読込: {:.01f}%".format(progress/image_count*100))
        return thumbnails_dic
