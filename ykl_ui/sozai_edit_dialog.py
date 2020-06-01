"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

import wx
import wx.lib.newevent as NE

from media_utility.image_tool import get_thumbnail, open_img

YKLSozaiEditUpdate, EVT_SOZAI_EDIT_UPDATE = NE.NewCommandEvent()


class YKLSozaiEditDialog(wx.Dialog):
    def __init__(self, parent, ctx, sozai):
        super().__init__(parent, title='キャラ素材編集', size=(800, 680), style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX)
        self.ctx = ctx
        self.sozai = sozai

        whole_vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        lvbox = wx.BoxSizer(wx.VERTICAL)
        pplabel = wx.StaticText(self, wx.ID_ANY, "プレビュー：")
        lvbox.Add(pplabel, flag=wx.ALL, border=5)
        self.ppanel = PreviewPanel(self, wx.ID_ANY, sozai.get_image())
        lvbox.Add(self.ppanel, 1, flag=wx.EXPAND | wx.ALL, border=5)
        hbox.Add(lvbox, 1, flag=wx.EXPAND)

        # ダイアログ右側
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 名前の表示・編集
        name_box = wx.BoxSizer(wx.HORIZONTAL)
        name_label = wx.StaticText(self, wx.ID_ANY, "名前：")
        name_box.Add(name_label, flag=wx.ALIGN_CENTER_VERTICAL)
        self.name = wx.TextCtrl(self, wx.ID_ANY, sozai.get_name())
        name_box.Add(self.name, flag=wx.ALIGN_CENTER_VERTICAL)
        vbox.Add(name_box, 0, flag=wx.EXPAND | wx.ALL, border=5)

        # ２行目
        total_box = wx.BoxSizer(wx.HORIZONTAL)
        mirror_check = wx.CheckBox(self, wx.ID_ANY, "画像を左右反転")
        if self.sozai.is_mirror_img():
            mirror_check.SetValue(True)
        self.Bind(wx.EVT_CHECKBOX, self.OnMirrorChecked, id=mirror_check.GetId())
        total_box.Add(mirror_check, flag=wx.ALIGN_CENTER_VERTICAL)
        save_btn = wx.Button(self, wx.ID_ANY, "画像を保存")
        self.Bind(wx.EVT_BUTTON, self.OnSaveBtnClick, id=save_btn.GetId())
        total_box.Add(save_btn, flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=20)
        vbox.Add(total_box, 0, flag=wx.EXPAND | wx.ALL, border=5)

        anime_panel = AnimeSeriesPanel(self, wx.ID_ANY, self.sozai)
        vbox.Add(anime_panel, 1, flag=wx.EXPAND)

        vbox.Layout()
        hbox.Add(vbox)
        hbox.Layout()
        whole_vbox.Add(hbox)
        btns = wx.BoxSizer(wx.HORIZONTAL)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "キャンセル")
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=cancel_btn.GetId())
        btns.Add(cancel_btn, flag=wx.ALL, border=5)
        ok_btn = wx.Button(self, wx.ID_OK, "適用して閉じる")
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=ok_btn.GetId())
        btns.Add(ok_btn, flag=wx.ALL, border=5)
        btns.Layout()

        whole_vbox.Add(btns, 0, flag=wx.RIGHT | wx.ALIGN_RIGHT, border=5)
        self.SetSizer(whole_vbox)

        self.Bind(EVT_SOZAI_EDIT_UPDATE, self.OnSozaiEditUpdate)

    def OnMirrorChecked(self, event):
        if event.IsChecked():
            self.sozai.set_mirror_img(True)
        else:
            self.sozai.set_mirror_img(False)
        # self.ppanel.set_image(self.sozai.get_image())
        wx.PostEvent(self, YKLSozaiEditUpdate(self.GetId()))

    def OnSaveBtnClick(self, event):
        with wx.FileDialog(
                self, "キャラ素材画像を保存", str(self.ctx.get_project_path()), self.sozai.get_name() + ".png",
                wildcard="PNG files (*.png)|*.png", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            path = fileDialog.GetPath()
            image = self.sozai.get_image()
            image.save(path, quality=95)

    def OnSozaiEditUpdate(self, event):
        self.ppanel.set_image(self.sozai.get_image())

    def OnBtnClick(self, event):
        name = self.name.GetValue()
        self.sozai.set_name(name)
        self.EndModal(event.GetId())


class PreviewPanel(wx.ScrolledWindow):
    def __init__(self, parent, idx, image):
        super().__init__(parent, idx, size=(400, 500))
        self.max_width = image.size[0]
        self.max_height = image.size[1]
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        bmp = wx.Bitmap.FromBufferRGBA(*image.size, image.tobytes())
        self.sbmp = wx.StaticBitmap(self, wx.ID_ANY, bmp)
        hbox.Add(self.sbmp)
        hbox.Layout()
        self.SetSizer(hbox)
        self.SetVirtualSize(self.max_width, self.max_height)
        self.SetScrollRate(20, 20)

    def set_image(self, image):
        bmp = wx.Bitmap.FromBufferRGBA(*image.size, image.tobytes())
        self.sbmp.SetBitmap(bmp)
        size = bmp.GetSize()
        self.max_width = size.Width
        self.max_height = size.Height
        self.SetVirtualSize(self.max_width, self.max_height)
        self.Refresh()


class AnimeSeriesPanel(wx.Panel):
    def __init__(self, parent, idx, sozai, size=(400, 550)):
        super().__init__(parent, idx, size=size)
        self.sozai = sozai
        self.part_name = None
        self.series_name = None
        self.front_back = None
        self.front_indices = []
        self.front_series = None
        self.back_indices = []
        self.back_series = None

        vbox = wx.BoxSizer(wx.VERTICAL)
        _title = wx.StaticText(self, wx.ID_ANY, "パーツ選択：")
        vbox.Add(_title, flag=wx.ALL, border=5)
        self.tree = wx.TreeCtrl(self, wx.ID_ANY, size=(380, 200))
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeSelChanged, id=self.tree.GetId())
        vbox.Add(self.tree, 1, flag=wx.ALL, border=5)

        self.imgs_list = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_ICON, size=(380, 300))
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListItemSelected, id=self.imgs_list.GetId())
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnListItemDeselected, id=self.imgs_list.GetId())
        self.il = wx.ImageList(200, 200)
        self.imgs_list.SetImageList(self.il, wx.IMAGE_LIST_NORMAL)
        vbox.Add(self.imgs_list, 1, flag=wx.ALL | wx.EXPAND, border=5)

        vbox.Layout()
        self.SetSizer(vbox)

        self.__set_parts_dic()

        # 初期値の設定
        current_u = self.sozai.get_current_image_dic()["後"]
        if current_u:
            paths_dic = self.sozai.get_parts_path_dic()
            f_serieses = paths_dic["後"]["前側"]
            b_serieses = paths_dic["後"]["後側"]
            for f_paths in f_serieses.values():
                self.front_indices = [f_paths.index(path) for path in current_u if path in f_paths]
                if self.front_indices:
                    break
            for b_paths in b_serieses.values():
                self.back_indices = [b_paths.index(path) for path in current_u if path in b_paths]
                if self.back_indices:
                    break
            # f_paths, u_pathsはforループ外でも生きているようだ
            current_f = [path for path in current_u if path in f_paths]
            if current_f:
                self.front_series = current_f[0].name[:2]
            current_b = [path for path in current_u if path in b_paths]
            if current_b:
                self.back_series = current_b[0].name[:2]

    def OnTreeSelChanged(self, event):
        _item = event.GetItem()
        if _item.IsOk():
            i_name = self.tree.GetItemText(_item)
            parent = self.tree.GetItemParent(_item)
            if parent.IsOk():
                p_name = self.tree.GetItemText(parent)
            if p_name not in ["基底", "後"]:
                paths_dic = self.sozai.get_parts_path_dic()
                if p_name in ["前側", "後側"]:
                    self.part_name = "後"
                    self.series_name = i_name
                    self.front_back = p_name
                    self.__set_imgs("後", i_name, u_or_m=p_name)
                    current_p = self.sozai.get_current_image_dic()[self.part_name]
                    for path in current_p:
                        u_paths_list = paths_dic[self.part_name][self.front_back][self.series_name]
                        if path in u_paths_list:
                            idx = u_paths_list.index(path)
                            self.imgs_list.Select(idx)
                else:
                    self.part_name = p_name
                    self.series_name = i_name
                    self.__set_imgs(p_name, i_name)
                    current_p = self.sozai.get_current_image_dic()[self.part_name]
                    for path in current_p:
                        p_paths_list = paths_dic[self.part_name][self.series_name]
                        if path in p_paths_list:
                            idx = p_paths_list.index(path)
                            self.imgs_list.Select(idx)
        else:
            self.__set_imgs(None, None)
        self.Refresh()

    def OnListItemSelected(self, event):
        idx = event.Index
        if self.part_name == "後":
            if self.front_back == "前側":
                self.front_indices = [idx,]
                self.front_series = self.series_name
                if self.series_name != self.back_series:
                    self.back_indices = []
                    self.back_series = None
            else:
                self.back_indices = [idx,]
                self.back_series = self.series_name
                if self.series_name != self.front_series:
                    self.front_indices = []
                    self.front_series = None
            print(self.back_indices, self.front_indices)
            self.sozai.set_part_paths(self.part_name, self.series_name, self.back_indices, self.front_indices)
        else:
            self.sozai.set_part_paths(self.part_name, self.series_name, [idx,])
        self.__set_treeitems_bold()
        wx.PostEvent(self, YKLSozaiEditUpdate(self.GetId()))

    def OnListItemDeselected(self, event):
        if self.part_name == '後':
            if self.front_back == "前側":
                self.front_indices = []
                self.front_series = None
            else:
                self.back_indices = []
                self.back_series = None
            self.sozai.set_part_paths(self.part_name, self.series_name, self.back_indices, self.front_indices)
        else:
            self.sozai.set_part_paths(self.part_name, self.series_name, [])
        self.__set_treeitems_bold()
        wx.PostEvent(self, YKLSozaiEditUpdate(self.GetId()))

    def __set_parts_dic(self):
        self.root = self.tree.AddRoot("基底")

        for part, series in self.sozai.get_parts_path_dic().items():
            part_node = self.tree.AppendItem(self.root, part)

            for s, _item in series.items():
                s_node = self.tree.AppendItem(part_node, s)

                if part == "後":
                    for us, _uitem in _item.items():
                        self.tree.AppendItem(s_node, us)
        self.tree.Expand(self.root)
        p1, _ = self.tree.GetFirstChild(self.root)
        self.tree.Expand(p1)
        s1, _ = self.tree.GetFirstChild(p1)

        self.__set_treeitems_bold()
        self.tree.SelectItem(s1)

    def __set_treeitems_bold(self):
        current_image_dic = self.sozai.get_current_image_dic()

        part, _ = self.tree.GetFirstChild(self.root)
        while part.IsOk():
            part_name = self.tree.GetItemText(part)
            if part_name == "後":
                um, _ = self.tree.GetFirstChild(part)
                for _ in range(2):
                    series, _ = self.tree.GetFirstChild(um)
                    while series.IsOk():
                        s_name = self.tree.GetItemText(series)
                        paths = current_image_dic[part_name]
                        if s_name in [path.name[:len(s_name)] for path in paths]:
                            self.tree.SetItemBold(series)
                        else:
                            self.tree.SetItemBold(series, bold=False)
                        series = self.tree.GetNextSibling(series)
                    um = self.tree.GetNextSibling(um)
            else:
                series, _ = self.tree.GetFirstChild(part)
                while series.IsOk():
                    s_name = self.tree.GetItemText(series)
                    paths = current_image_dic[part_name]
                    if s_name in [path.name[:len(s_name)] for path in paths]:
                        self.tree.SetItemBold(series)
                    else:
                        self.tree.SetItemBold(series, bold=False)
                    series = self.tree.GetNextSibling(series)
            part = self.tree.GetNextSibling(part)

    def __set_imgs(self, part, series, u_or_m='後側'):
        self.imgs_list.DeleteAllItems()
        self.il.RemoveAll()
        if part is None:
            return
        if part == "後":
            paths = self.sozai.get_parts_path_dic()[part][u_or_m][series]
            for path in paths:
                image = open_img(path)
                image = get_thumbnail(image, size=200)
                bmp = wx.Bitmap.FromBufferRGBA(200, 200, image.tobytes())
                self.il.Add(bmp)
            for i, path in enumerate(paths):
                self.imgs_list.InsertItem(i, path.name, i)
        else:
            paths = self.sozai.get_parts_path_dic()[part][series]
            for path in paths:
                image = open_img(path)
                image = get_thumbnail(image, size=200)
                bmp = wx.Bitmap.FromBufferRGBA(200, 200, image.tobytes())
                self.il.Add(bmp)
            for i, path in enumerate(paths):
                self.imgs_list.InsertItem(i, path.name, i)
