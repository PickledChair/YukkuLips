"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx
from copy import copy
from PIL import ImageOps
from pathlib import Path


class MovieImageEditDialog(wx.Dialog):
    def __init__(self, parent, idx, title, context, size=(900, 460)):
        super().__init__(parent, idx, title, size=size)
        self.context = context
        self.image_move_panel = None
        self.mov_img_edit_panel = None
        self.create_widgets()
        self.Centre()
        self.Show()

    def create_widgets(self):
        panel = wx.Panel(self, wx.ID_ANY)
        box = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(box)

        self.image_move_panel = ImageMovePanel(panel, wx.ID_ANY, self.context, size=(740, 460))
        self.mov_img_edit_panel = MovieImageEditPanel(panel, wx.ID_ANY, self.context, size=(160, 460))

        box.Add(self.image_move_panel)
        box.Add(self.mov_img_edit_panel)

        box.Layout()

    def update_image_move_panel_bg(self, pathname):
        self.image_move_panel.update_background(pathname)

    def update_edit_panel_pos_ent(self, pos):
        self.mov_img_edit_panel.update_pos_ent(pos)

    def update_image_move_panel_scale(self, scale):
        self.image_move_panel.update_sozai_scale(scale)

    def update_image_move_panel_mvsize(self, select_idx):
        self.image_move_panel.update_movie_size(select_idx)

    def decision_close(self):
        self.decision()
        self.Close()

    def decision(self):
        self.context.movie_size = self.context.movie_sizes[self.image_move_panel.movie_size_idx]
        self.context.sozai_pos = self.image_move_panel.to_physical_pos(self.image_move_panel.objs[1].pos)
        self.context.sozai_scale = self.image_move_panel.sozai_scale
        if self.image_move_panel.bg_path is None:
            self.context.ref_background = self.image_move_panel.bg_path
        else:
            self.context.ref_background = Path(self.image_move_panel.bg_path)

        self.GetParent().setting_movie_info()
        self.GetParent().GetParent().GetParent().disp_unsaved()


class ImageMovePanel(wx.Panel):
    def __init__(self, parent, idx, context, size):
        super().__init__(parent, idx, size=size)
        self.context = context
        self.objs = []
        self.drag_obj = None
        self.bg_path = copy(self.context.ref_background)
        self.bg_size = (640, 360)
        self.bg_pos = (50, 40)
        self.sozai_scale = self.context.sozai_scale
        self.movie_size = self.context.movie_size
        self.movie_size_idx = list(self.context.movie_sizes).index(self.context.movie_size)
        self.sozai_size = (400, 400)
        self.drag_start_pos = wx.Point(0, 0)
        self._buffer = wx.Bitmap(*self.GetClientSize())
        self.init_draw_buffer()
        self.init_images()

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_leftdown)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_leftup)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)

    def init_images(self):
        if self.bg_path is not None:
            if not Path(self.bg_path).exists():
                wx.MessageBox("参考背景画像を見つけられませんでした\n"
                              "（設定はまだ変更されていません）", "エラー", wx.ICON_QUESTION | wx.OK, None)
                self.bg_path = None
        if self.bg_path is None:
            bg_bmp = wx.Bitmap.FromRGBA(*self.bg_size, *self.context.bg_color.color_tuple)
            bg_obj = ImageObj(bg_bmp, *self.bg_pos)
            self.objs.append(bg_obj)
        else:
            bg_bmp = wx.Bitmap(str(self.bg_path))
            bg_bmp.SetSize(size=self.bg_size)
            bg_obj = ImageObj(bg_bmp, *self.bg_pos)
            self.objs.append(bg_obj)

        bg_color_backup = copy(self.context.bg_color)
        # 一時的に素材の背景を透明色にする
        self.context.bg_color = self.context.bg_colors[3]
        sozai_image = self.context.integrate_images(self.context.base_size)
        x_scale = self.bg_size[0] / self.context.movie_size.size_tuple[0]
        y_scale = self.bg_size[1] / self.context.movie_size.size_tuple[1]
        self.sozai_size = (sozai_image.size[0] * x_scale * self.sozai_scale,
                           sozai_image.size[1] * y_scale * self.sozai_scale)
        sozai_image = sozai_image.resize((int(sozai_image.size[0] * x_scale * self.sozai_scale),
                                          int(sozai_image.size[1] * y_scale * self.sozai_scale)))
        if self.context.rev_flag:
            sozai_image = ImageOps.mirror(sozai_image)

        sozai_bmp = wx.Bitmap.FromBufferRGBA(*sozai_image.size, sozai_image.tobytes())
        self.context.bg_color = bg_color_backup

        sozai_obj = MoveImageObj(sozai_bmp,
                                 int(self.context.sozai_pos[0] * x_scale) + self.bg_pos[0],
                                 int(self.context.sozai_pos[1] * y_scale) + self.bg_pos[1])
        self.objs.append(sozai_obj)

        self.update_drawing()

    def update_background(self, pathname):
        self.bg_path = pathname
        bg_bmp = wx.Bitmap(str(self.bg_path))
        bg_bmp.SetSize(size=self.bg_size)
        bg_obj = ImageObj(bg_bmp, *self.bg_pos)
        self.objs[0] = bg_obj

        self.update_drawing()

    def update_sozai_scale(self, scale):
        self.sozai_size = (self.sozai_size[0] / self.sozai_scale * scale,
                           self.sozai_size[1] / self.sozai_scale * scale)
        self.objs[1].bmp.SetSize((int(self.sozai_size[0]), int(self.sozai_size[1])))
        self.sozai_scale = scale
        self.update_drawing()

    def update_movie_size(self, select_idx):
        movie_size = self.context.movie_sizes[select_idx]
        self.sozai_size = (self.sozai_size[0] * self.movie_size.size_tuple[0] / movie_size.size_tuple[0],
                           self.sozai_size[1] * self.movie_size.size_tuple[1] / movie_size.size_tuple[1])
        self.objs[1].bmp.SetSize((int(self.sozai_size[0]), int(self.sozai_size[1])))
        self.movie_size_idx = select_idx
        self.movie_size = self.context.movie_sizes[select_idx]
        self.objs[1].pos = wx.Point(self.bg_pos[0], self.bg_pos[1])
        self.GetParent().GetParent().update_edit_panel_pos_ent(self.to_physical_pos(self.objs[1].pos))
        self.update_drawing()

    def init_draw_buffer(self):
        size = self.GetClientSize()
        self._buffer = wx.Bitmap(*size)
        self.update_drawing()

    def update_drawing(self):
        dc = wx.MemoryDC()
        dc.SelectObject(self._buffer)

        self.draw(dc)
        del dc

        self.Refresh()
        self.Update()

    def draw(self, dc):
        dc.Clear()
        for obj in self.objs:
            if isinstance(obj, ImageObj):
                obj.draw(dc, False)
            elif isinstance(obj, MoveImageObj):
                obj.draw(dc, True)

    def on_paint(self, _event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self._buffer, 0, 0, True)

    def find_obj(self, point):
        result = None
        for obj in self.objs:
            if isinstance(obj, MoveImageObj):
                if obj.hit_test(point):
                    result = obj
        return result

    def on_mouse_leftdown(self, event):
        pos = event.GetPosition()
        obj = self.find_obj(pos)
        if obj is not None:
            self.drag_obj = obj
            self.drag_start_pos = pos
            self.drag_obj.save_pos_diff(pos)
            self.GetParent().GetParent().update_edit_panel_pos_ent(self.to_physical_pos(self.drag_obj.pos))

    def on_mouse_leftup(self, event):
        if self.drag_obj is not None:
            pos = event.GetPosition()
            self.drag_obj.pos.x = pos.x + self.drag_obj.diff_pos.x
            self.drag_obj.pos.y = pos.y + self.drag_obj.diff_pos.y
            self.GetParent().GetParent().update_edit_panel_pos_ent(self.to_physical_pos(self.drag_obj.pos))
        self.drag_obj = None
        self.update_drawing()

    def on_mouse_motion(self, event):
        if self.drag_obj is None:
            return
        pos = event.GetPosition()
        self.drag_obj.pos.x = pos.x + self.drag_obj.diff_pos.x
        self.drag_obj.pos.y = pos.y + self.drag_obj.diff_pos.y
        self.GetParent().GetParent().update_edit_panel_pos_ent(self.to_physical_pos(self.drag_obj.pos))
        self.update_drawing()

    def to_physical_pos(self, pos):
        return [int((pos.x - self.bg_pos[0]) * self.movie_size.size_tuple[0] / self.bg_size[0]),
                int((pos.y - self.bg_pos[1]) * self.movie_size.size_tuple[1] / self.bg_size[1])]


class ImageObj:
    def __init__(self, bmp, x=0, y=0):
        self.bmp = bmp
        self.pos = wx.Point(x, y)
        self.diff_pos = wx.Point(0, 0)

    def get_rect(self):
        return wx.Rect(self.pos.x, self.pos.y, self.bmp.GetWidth(), self.bmp.GetHeight())

    def draw(self, dc, select_enable):
        if self.bmp.IsOk():
            r = self.get_rect()

            dc.SetPen(wx.Pen(wx.BLACK, 4))
            dc.DrawBitmap(self.bmp, r.GetX(), r.GetY(), True)

            if select_enable:
                dc.SetBrush(wx.TRANSPARENT_BRUSH)
                dc.SetPen(wx.Pen(wx.RED, 2))
                dc.DrawRectangle(r.GetX(), r.GetY(), r.GetWidth(), r.GetHeight())
            return True
        else:
            return False

    def hit_test(self, _point):
        pass

    def save_pos_diff(self, _point):
        pass


class MoveImageObj(ImageObj):
    def __init__(self, bmp, x=0, y=0):
        super().__init__(bmp, x, y)

    def hit_test(self, point):
        rect = self.get_rect()
        return rect.Contains(point)

    def save_pos_diff(self, point):
        self.diff_pos.x = self.pos.x - point.x
        self.diff_pos.y = self.pos.y - point.y


class MovieImageEditPanel(wx.Panel):
    def __init__(self, parent, idx, context, size):
        super().__init__(parent, idx, size=size, style=wx.BORDER_SUNKEN)
        self.context = context
        self.pos_ent = None
        self.scale_ent = None
        self.create_widgets()

    def create_widgets(self):
        box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(box)

        bg_open_btn = wx.Button(self, wx.ID_ANY, "背景をセット")
        self.Bind(wx.EVT_BUTTON, self.bg_open, id=bg_open_btn.GetId())

        box.Add(bg_open_btn, flag=wx.ALL, border=5)

        pos_label = wx.StaticText(self, wx.ID_ANY, "素材位置：")
        self.pos_ent = wx.TextCtrl(self, wx.ID_ANY, str(self.context.sozai_pos), style=wx.TE_READONLY)

        box.Add(pos_label, flag=wx.LEFT, border=5)
        box.Add(self.pos_ent, flag=wx.ALL, border=5)

        scale_label = wx.StaticText(self, wx.ID_ANY, "素材倍率：")
        self.scale_ent = wx.TextCtrl(self, wx.ID_ANY, str(self.context.sozai_scale), style=wx.TE_READONLY)
        scale_slider = wx.Slider(self, wx.ID_ANY, int(self.context.sozai_scale * 100), 1, 300)
        self.Bind(wx.EVT_SLIDER, self.on_rescale, id=scale_slider.GetId())

        box.Add(scale_label, flag=wx.LEFT, border=5)
        box.Add(self.scale_ent, flag=wx.ALL, border=5)
        box.Add(scale_slider, flag=wx.LEFT, border=5)

        movie_size_label = wx.StaticText(self, wx.ID_ANY, "動画解像度：")
        movie_size_choice = wx.Choice(self, wx.ID_ANY,
                                      choices=[movie_size.name for movie_size in self.context.movie_sizes])
        movie_size_choice.SetSelection(list(self.context.movie_sizes).index(self.context.movie_size))
        self.Bind(wx.EVT_CHOICE, self.on_movie_resize, id=movie_size_choice.GetId())

        box.Add(movie_size_label, flag=wx.ALL, border=5)
        box.Add(movie_size_choice, flag=wx.LEFT, border=5)

        out_button = wx.Button(self, wx.ID_ANY, "画像保存して閉じる")
        self.Bind(wx.EVT_BUTTON, self.output_image, id=out_button.GetId())

        box.Add(out_button, flag=wx.ALL, border=5)

        decision_btn = wx.Button(self, wx.ID_ANY, "反映して閉じる")
        self.Bind(wx.EVT_BUTTON, self.on_decision_close, id=decision_btn.GetId())

        box.Add(0, 0, proportion=1)
        box.Add(decision_btn, flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_BOTTOM | wx.ALL, border=10)

        box.Layout()

    def bg_open(self, _event):
        with wx.FileDialog(
                self, "背景を指定", "", self.context.proj_name,
                wildcard="PNG and JPG files (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
        bg_image = wx.Bitmap(pathname)
        bg_width, bg_height = bg_image.GetWidth(), bg_image.GetHeight()
        if bg_width/bg_height != 16/9:
            wx.MessageBox("画像のアスペクト比が16:9ではありません",
                          "エラー", wx.ICON_QUESTION | wx.OK, self)
            return
        # self.context.ref_background = Path(pathname)
        self.GetParent().GetParent().update_image_move_panel_bg(pathname)
        del bg_image

    def update_pos_ent(self, pos):
        self.pos_ent.SetValue(str(pos))

    def on_rescale(self, event):
        self.GetParent().GetParent().update_image_move_panel_scale(float(event.GetInt() / 100))
        self.scale_ent.SetValue(str(float(event.GetInt() / 100)))

    def on_movie_resize(self, event):
        self.GetParent().GetParent().update_image_move_panel_mvsize(event.GetSelection())

    def output_image(self, _event):
        with wx.FileDialog(
                self, "画像を保存", "", self.context.proj_name + "_MOVIE_SIZE",
                wildcard="PNG files (*.png)|*.png", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            self.GetParent().GetParent().decision()
            self.context.save_movie_size_image(pathname)
            self.GetParent().GetParent().Close()

    def on_decision_close(self, _event):
        self.GetParent().GetParent().decision_close()
