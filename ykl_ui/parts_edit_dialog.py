"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx


class PartsEditDialog(wx.Dialog):
    def __init__(self, parent, idx, title, context, size=(800, 460)):
        super().__init__(parent, idx, title, size=size)
        self.context = context
        self.copy_dict = self.context.current_images_dic.copy()
        self.current_page_idx = 0
        self.select_name = None
        self.create_widgets()
        self.Centre()
        self.Show()

    def create_widgets(self):
        panel = wx.Panel(self, wx.ID_ANY)
        outer_vbox = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(outer_vbox)
        choice_book = wx.Choicebook(panel, wx.ID_ANY)
        for i, part in enumerate(self.context.sozai.part_dirs):
            bmps_panel = BmpButtonsPanel(panel, wx.ID_ANY, self.context, no=i, size=(800, 350))
            if part.name == '全':
                choice_book.InsertPage(i, bmps_panel, part.name + " (この項目で選択すると、他のパーツ画像は合成されません)")
            else:
                choice_book.InsertPage(i, bmps_panel, part.name)
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.on_choice_page, id=choice_book.GetId())

        btns_panel = wx.Panel(panel, wx.ID_ANY, size=(800, 60))
        btns_box = wx.BoxSizer(wx.HORIZONTAL)
        btns_panel.SetSizer(btns_box)
        select_image = wx.StaticText(btns_panel, wx.ID_ANY, "選択画像: ")
        self.select_name = wx.TextCtrl(btns_panel, wx.ID_ANY, size=(200, 25), style=wx.TE_READONLY)
        current_paths = self.context.current_images_dic[self.context.sozai.part_dirs[0].name]
        if len(current_paths) == 0:
            self.select_name.SetValue("未選択")
        else:
            paths_str = ""
            for current_path in current_paths:
                if paths_str == "":
                    paths_str += current_path.name
                else:
                    paths_str += ", " + current_path.name
            self.select_name.SetValue(paths_str)
        decide_btn = wx.Button(btns_panel, wx.ID_ANY, "決定して閉じる")
        self.Bind(wx.EVT_BUTTON, self.on_decision, id=decide_btn.GetId())
        btns_box.Add(select_image, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=5)
        btns_box.Add(self.select_name, 0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        btns_box.Add(width=0, height=0, proportion=1)
        btns_box.Add(decide_btn, 0, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=20)
        btns_box.Layout()

        outer_vbox.Add(choice_book)
        outer_vbox.Add(btns_panel, flag=wx.TOP, border=5)
        outer_vbox.Layout()

    def on_decision(self, _event):
        self.context.current_images_dic = self.copy_dict
        self.GetParent().update_image_context()
        self.Close()

    def on_choice_page(self, event):
        self.current_page_idx = event.GetSelection()
        current_paths = self.context.current_images_dic[self.context.sozai.part_dirs[self.current_page_idx].name]
        if len(current_paths) == 0:
            self.select_name.SetValue("未選択")
        else:
            paths_str = ""
            for current_path in current_paths:
                if paths_str == "":
                    paths_str += current_path.name
                else:
                    paths_str += ", " + current_path.name
            self.select_name.SetValue(paths_str)


class BmpButtonsPanel(wx.ScrolledWindow):
    def __init__(self, parent, idx, context, no, size=(100, 100)):
        super().__init__(parent, idx, size=size)
        self.context = context
        self.no = no
        self.btn_val_dict = {}
        self.create_widgets()

    def create_widgets(self):
        gsizer = wx.GridSizer(cols=4)
        self.SetSizer(gsizer)
        paths = self.context.sozai.images_dic[self.context.sozai.part_dirs[self.no].name]
        for path in paths:
            bmp = self.context.sozai.thumbnails_dic[path]
            bmp_btn = wx.BitmapToggleButton(self, wx.ID_ANY, bmp, size=(200, 200), style=wx.BU_TOP)
            if path in self.context.current_images_dic[self.context.sozai.part_dirs[self.no].name]:
                bmp_btn.SetValue(True)
            self.Bind(wx.EVT_TOGGLEBUTTON, self.on_click_bmp, id=bmp_btn.GetId())
            self.btn_val_dict[bmp_btn.GetId()] = path
            gsizer.Add(bmp_btn)
        gsizer.Layout()
        self.FitInside()
        self.SetScrollRate(10, 10)

    def on_click_bmp(self, event):
        path = self.btn_val_dict[event.GetId()]
        temp_paths = self.GetParent().GetParent().copy_dict[self.context.sozai.part_dirs[self.no].name].copy()
        if len(temp_paths) == 2:
            if path in temp_paths:
                temp_paths.remove(path)
            else:
                if len(path.name) > 7:
                    if path.name[0:4] in [temp_path.name[0:4] for temp_path in temp_paths]:
                        idx = [temp_path.name[0:4] for temp_path in temp_paths].index(path.name[0:4])
                        temp_paths.pop(idx)
                        temp_paths.append(path)
                    else:
                        temp_paths = [path, ]
                else:
                    temp_paths = [path, ]
        elif len(temp_paths) == 1:
            if path in temp_paths:
                temp_paths.remove(path)
            else:
                if len(path.name) > 7:
                    if path.name[0:2] == temp_paths[0].name[0:2]:
                        if (path.name[2:4] == "m1" and temp_paths[0].name[2:4] == "u1")\
                                or (path.name[2:4] == "u1" and temp_paths[0].name[2:4] == "m1"):
                            temp_paths.append(path)
                        else:
                            temp_paths = [path, ]
                    else:
                        temp_paths = [path, ]
                else:
                    temp_paths = [path, ]
        else:
            temp_paths.append(path)
        self.GetParent().GetParent().copy_dict[self.context.sozai.part_dirs[self.no].name] = temp_paths
        paths_str = ""
        for temp_path in temp_paths:
            if paths_str == "":
                paths_str += str(temp_path.name)
            else:
                paths_str += ", " + str(temp_path.name)
        if paths_str != "":
            self.GetParent().GetParent().select_name.SetValue(paths_str)
        else:
            self.GetParent().GetParent().select_name.SetValue("未選択")
        for child in self.GetChildren():
            if isinstance(child, wx.BitmapToggleButton):
                if self.btn_val_dict[child.GetId()] not in temp_paths:
                    child.SetValue(False)
