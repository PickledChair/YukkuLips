"""
YukkuLips

Copyright (c) 2018 - 2020 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import wx
import wx.lib.newevent as NE
from media_utility.image_tool import get_rescaled_image, get_thumbnail, get_scene_image, open_img
from PIL import Image

# from copy import copy
from pathlib import Path

YKLLayoutEditUpdate, EVT_LAYOUT_EDIT_UPDATE = NE.NewCommandEvent()
YKLLayoutPreviewUpdate, EVT_LAYOUT_PREVIEW_UPDATE = NE.NewCommandEvent()


class YKLLauoutEditDialog(wx.Dialog):
    def __init__(self, parent, ctx, sceneblock):
        super().__init__(parent, title="レイアウト編集", style=wx.CAPTION | wx.CLOSE_BOX)
        self.ctx = ctx
        self.sceneblock = sceneblock

        scene_w, scene_h = self.ctx.resolution
        pp_bg_w, pp_bg_h = int(scene_w * (400 / scene_h)), 400
        pp_w, pp_h = pp_bg_w + 100, pp_bg_h + 100
        self_w, self_h = pp_w + 320, pp_h + 80 + 10
        self.SetSize(self_w, self_h)

        whole_vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        lvbox = wx.BoxSizer(wx.VERTICAL)
        pplabel = wx.StaticText(self, wx.ID_ANY, "プレビュー：（キャラ素材をドラッグで移動できます）")
        lvbox.Add(pplabel, flag=wx.ALL, border=5)

        self.ppanel = ImageMovePanel(
            self, wx.ID_ANY, self.ctx, self.sceneblock,
            (pp_w, pp_h), (pp_bg_w, pp_bg_h))
        lvbox.Add(self.ppanel)
        hbox.Add(lvbox)

        rvbox = wx.BoxSizer(wx.VERTICAL)
        splabel = wx.StaticText(self, wx.ID_ANY, "設定：")
        rvbox.Add(splabel, flag=wx.ALL, border=5)
        self.slistbook = ImageSettingListBook(
            self, wx.ID_ANY, self.ctx, self.sceneblock, size=(310, 350))
        rvbox.Add(self.slistbook, 1, flag=wx.ALL | wx.EXPAND, border=5)

        rvbox.Add(wx.StaticLine(self, wx.ID_ANY), flag=wx.EXPAND)

        bg_set_btn = wx.Button(self, wx.ID_ANY, "背景画像を設定")
        self.Bind(wx.EVT_BUTTON, self.bg_open, id=bg_set_btn.GetId())
        rvbox.Add(bg_set_btn, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, border=10)
        save_img_btn = wx.Button(self, wx.ID_ANY, "レイヤを結合して画像保存")
        self.Bind(wx.EVT_BUTTON, self.save_scene_image, id=save_img_btn.GetId())
        rvbox.Add(save_img_btn, flag=wx.ALIGN_CENTER_HORIZONTAL)
        img_caution = wx.StaticText(self, wx.ID_ANY, "（背景画像は結合されません）")
        rvbox.Add(img_caution, flag=wx.TOP | wx.ALIGN_CENTER_HORIZONTAL, border=5)
        hbox.Add(rvbox)

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

        whole_vbox.Add(btns, 0, flag=wx.RIGHT | wx.TOP | wx.ALIGN_RIGHT, border=5)

        self.SetSizer(whole_vbox)

        self.Bind(EVT_LAYOUT_PREVIEW_UPDATE, self.OnPreviewUpdate)
        self.Bind(EVT_LAYOUT_EDIT_UPDATE, self.OnEditUpdate)

    def OnBtnClick(self, event):
        self.sceneblock.sozai_order = self.sceneblock.sozai_order
        self.sceneblock.sozai_pos = self.sceneblock.sozai_pos
        self.sceneblock.sozai_scale = self.sceneblock.sozai_scale
        self.EndModal(event.GetId())

    def OnPreviewUpdate(self, event):
        for i in range(self.slistbook.GetPageCount()):
            self.slistbook.set_order(i)
            self.slistbook.set_position(i)
        self.slistbook.SetSelection(event.GetInt())

    def OnEditUpdate(self, event):
        self.ppanel.update_pos_and_scale(event.GetInt())

    def bg_open(self, _event):
        with wx.FileDialog(
                self, "背景を指定", str(self.ctx.get_project_path()), "",
                wildcard="PNG and JPG files (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
        bg_image = wx.Bitmap(pathname)
        bg_width, bg_height = bg_image.GetWidth(), bg_image.GetHeight()
        if bg_width/bg_height != self.ctx.resolution[0]/self.ctx.resolution[1]:
            wx.MessageBox("画像のアスペクト比はプロジェクトの解像度設定と一致している必要があります",
                          "エラー", wx.ICON_QUESTION | wx.OK, self)
            return
        self.ppanel.update_background(pathname)
        del bg_image

    def save_scene_image(self, _event):
        with wx.FileDialog(
                self, "画像を保存", "", self.ctx.get_project_name() + "_scene_image",
                wildcard="PNG files (*.png)|*.png", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            images = [sozai.get_image() for sozai in self.sceneblock.get_sozais()]
            images = [get_rescaled_image(image, scale)
                      for image, scale in zip(images, self.sceneblock.sozai_scale)]
            image = get_scene_image(
                images,
                self.sceneblock.sozai_pos,
                self.sceneblock.sozai_order,
                bg_size=self.ctx.resolution,
                bg_color=(0,0,0,0))
            image.save(pathname, quality=95)


class ImageSettingListBook(wx.Listbook):
    def __init__(self, parent, idx, ctx, block, size):
        super().__init__(parent, idx, size=size)
        self.ctx = ctx
        self.sceneblock = block
        im_size = 64
        il = wx.ImageList(im_size, im_size)
        for sozai in self.sceneblock.get_sozais():
            image = sozai.get_image()
            image = get_thumbnail(image, size=im_size)
            bmp = wx.Bitmap.FromBufferRGBA(im_size, im_size, image.tobytes())
            il.Add(bmp)
        self.AssignImageList(il)
        for i, sozai in enumerate(self.sceneblock.get_sozais()):
            page = ImageSettingPanel(self, wx.ID_ANY, self.ctx, self.sceneblock, i, size=(310, 250))
            self.AddPage(page, sozai.get_name(), imageId=i)
        for i in range(self.GetPageCount()):
            self.set_order(i)
            self.set_position(i)
            self.set_scale(i)

    def set_order(self, idx):
        order = self.sceneblock.sozai_order
        page = self.GetPage(idx)
        page.set_order(order[idx])

    def set_position(self, idx):
        pos = self.sceneblock.sozai_pos
        page = self.GetPage(idx)
        page.set_position(pos[idx])

    def set_scale(self, idx):
        scale = self.sceneblock.sozai_scale
        page = self.GetPage(idx)
        page.set_scale(scale[idx])


class ImageSettingPanel(wx.Panel):
    def __init__(self, parent, idx, ctx, block, page_count, size):
        super().__init__(parent, idx, size=size)
        self.ctx = ctx
        self.sceneblock = block
        self.page_count = page_count
        vbox = wx.BoxSizer(wx.VERTICAL)

        order_hbox = wx.BoxSizer(wx.HORIZONTAL)
        order_lbl = wx.StaticText(self, wx.ID_ANY, "描画順序：")
        order_hbox.Add(order_lbl, flag=wx.ALIGN_CENTER_VERTICAL)
        self.order_tc = wx.TextCtrl(self, wx.ID_ANY, size=(50, -1))
        self.order_tc.SetEditable(False)
        order_hbox.Add(self.order_tc, 1, flag=wx.ALIGN_CENTER_VERTICAL)
        vbox.Add(order_hbox, flag=wx.ALL, border=5)

        pos_hbox = wx.BoxSizer(wx.HORIZONTAL)
        pos_lbl_x = wx.StaticText(self, wx.ID_ANY, "位置　x：")
        pos_hbox.Add(pos_lbl_x, flag=wx.ALIGN_CENTER_VERTICAL)
        w, h = 1920, 1080 # 最大画質はフルHD
        x_min, x_max = -w, w * 2
        self.x_spin = wx.SpinCtrl(self, wx.ID_ANY, min=x_min, max=x_max, size=(60, -1))
        self.Bind(wx.EVT_SPINCTRL, self.on_spin_change, id=self.x_spin.GetId())
        # self.Bind(wx.EVT_TEXT, self.on_spin_change, id=self.x_spin.GetId())
        pos_hbox.Add(self.x_spin, flag=wx.ALIGN_CENTER_VERTICAL)
        pos_lbl_y = wx.StaticText(self, wx.ID_ANY, "　y：")
        pos_hbox.Add(pos_lbl_y, flag=wx.ALIGN_CENTER_VERTICAL)
        y_min, y_max = -h, h * 2
        self.y_spin = wx.SpinCtrl(self, wx.ID_ANY, min=y_min, max=y_max, size=(60, -1))
        self.Bind(wx.EVT_SPINCTRL, self.on_spin_change, id=self.y_spin.GetId())
        pos_hbox.Add(self.y_spin, flag=wx.ALIGN_CENTER_VERTICAL)
        vbox.Add(pos_hbox, flag=wx.ALL, border=5)

        scale_hbox = wx.BoxSizer(wx.HORIZONTAL)
        scale_lbl = wx.StaticText(self, wx.ID_ANY, "拡大率：")
        scale_hbox.Add(scale_lbl, flag=wx.ALIGN_CENTER_VERTICAL)
        self.scale_slider = wx.Slider(self, wx.ID_ANY, minValue=1, maxValue=1000, size=(160, -1))
        self.Bind(wx.EVT_SLIDER, self.on_slider_change, id=self.scale_slider.GetId())
        scale_hbox.Add(self.scale_slider, flag=wx.ALIGN_CENTER_VERTICAL)
        self.scale_spin = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0.01, max=10.0, inc=0.01, size=(60, -1))
        self.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_spin_change, id=self.scale_spin.GetId())
        scale_hbox.Add(self.scale_spin, flag=wx.ALIGN_CENTER_VERTICAL)
        vbox.Add(scale_hbox, flag=wx.ALL, border=5)

        img_save_btn = wx.Button(self, wx.ID_ANY, "このレイヤを画像保存")
        self.Bind(wx.EVT_BUTTON, self.save_scene_image, id=img_save_btn.GetId())
        vbox.Add(img_save_btn, flag=wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, border=5)

        self.SetSizer(vbox)

    def on_spin_change(self, event):
        if event.GetId() == self.x_spin.GetId():
            self.sceneblock.sozai_pos[self.page_count] = (self.x_spin.GetValue(), self.sceneblock.sozai_pos[self.page_count][1])
        elif event.GetId() == self.y_spin.GetId():
            self.sceneblock.sozai_pos[self.page_count] = (self.sceneblock.sozai_pos[self.page_count][0], self.y_spin.GetValue())
        elif event.GetId() == self.scale_spin.GetId():
            self.sceneblock.sozai_scale[self.page_count] = self.scale_spin.GetValue()
            self.scale_slider.SetValue(int(self.scale_spin.GetValue() * 100))
        new_event = YKLLayoutEditUpdate(self.GetId())
        new_event.SetInt(self.page_count)
        wx.PostEvent(self, new_event)

    def on_slider_change(self, event):
        self.scale_spin.SetValue(self.scale_slider.GetValue() / 100)
        self.sceneblock.sozai_scale[self.page_count] = self.scale_spin.GetValue()
        new_event = YKLLayoutEditUpdate(self.GetId())
        new_event.SetInt(self.page_count)
        wx.PostEvent(self, new_event)

    def set_order(self, order):
        self.order_tc.SetValue(str(order + 1))

    def set_position(self, pos):
        x, y = pos
        self.x_spin.SetValue(x)
        self.y_spin.SetValue(y)

    def set_scale(self, scale):
        self.scale_slider.SetValue(int(scale * 100))
        self.scale_spin.SetValue(scale)

    def save_scene_image(self, _event):
        sozai = self.sceneblock.get_sozais()[self.page_count]
        with wx.FileDialog(
                self, "画像を保存", "", self.ctx.get_project_name() + "_scene_image_" + sozai.get_name(),
                wildcard="PNG files (*.png)|*.png", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            image = sozai.get_image()
            image = get_rescaled_image(image, self.sceneblock.sozai_scale[self.page_count])
            image = get_scene_image(
                [image,],
                self.sceneblock.sozai_pos[self.page_count:self.page_count+1],
                [0,],
                bg_size=self.ctx.resolution,
                bg_color=(0,0,0,0))
            image.save(pathname, quality=95)


class ImageMovePanel(wx.Panel):
    def __init__(self, parent, idx, ctx, sceneblock, size, scene_size):
        super().__init__(parent, idx, size=size)
        self.ctx = ctx
        self.sceneblock = sceneblock
        self.objs = []
        self.drag_obj = None
        self.scene_size = scene_size
        self.bg_pos = (50, 50)
        self.resolution = self.ctx.resolution
        self.drag_start_pos = wx.Point(0, 0)
        self._buffer = wx.Bitmap(*self.GetClientSize())
        self.init_draw_buffer()
        self.init_images()

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_leftdown)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_leftup)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)

    def init_images(self):
        if self.sceneblock.bg_path is not None:
            if not Path(self.sceneblock.bg_path).exists():
                wx.MessageBox("参考背景画像を見つけられませんでした\n"
                              "（設定はまだ変更されていません）", "エラー",
                              wx.ICON_QUESTION | wx.OK, None)
                self.sceneblock.bg_path = None
        if self.sceneblock.bg_path is None:
            bg_bmp = wx.Bitmap.FromRGBA(*self.scene_size, *self.ctx.bg_color)
            bg_obj = ImageObj(bg_bmp, *self.bg_pos)
            self.objs.append(bg_obj)
        else:
            img = open_img(str(self.sceneblock.bg_path))
            img = img.resize(self.scene_size, Image.LANCZOS)
            # bg_bmp = wx.Bitmap(str(self.sceneblock.bg_path))
            if len(img.getpixel((0,0))) == 3:
                bg_bmp = wx.Bitmap.FromBuffer(*img.size, img.tobytes())
            elif len(img.getpixel((0,0))) == 4:
                bg_bmp = wx.Bitmap.FromBufferRGBA(*img.size, img.tobytes())
            else:
                return
            # SetSizeは内部でSetWidthなどを呼んでいるようだが、それらは非推奨である
            # bg_bmp.SetSize(size=self.scene_size)
            bg_obj = ImageObj(bg_bmp, *self.bg_pos)
            self.objs.append(bg_obj)

        self.update_sozai_scale()

        self.update_drawing()

    def update_background(self, pathname):
        self.sceneblock.bg_path = pathname
        img = open_img(str(self.sceneblock.bg_path))
        img = img.resize(self.scene_size, Image.LANCZOS)
        # bg_bmp = wx.Bitmap(str(self.sceneblock.bg_path))
        if len(img.getpixel((0,0))) == 3:
            bg_bmp = wx.Bitmap.FromBuffer(*img.size, img.tobytes())
        elif len(img.getpixel((0,0))) == 4:
            bg_bmp = wx.Bitmap.FromBufferRGBA(*img.size, img.tobytes())
        else:
            return
        # SetSizeは内部でSetWidthなどを呼んでいるようだが、それらは非推奨である
        # bg_bmp.SetSize(size=self.scene_size)
        bg_obj = ImageObj(bg_bmp, *self.bg_pos)
        self.objs[0] = bg_obj

        self.update_drawing()

    def update_pos_and_scale(self, idx):
        self.update_sozai_scale()
        obj = self.objs[self.sceneblock.sozai_order[idx] + 1]
        obj.pos.x, obj.pos.y = self.to_virtual_pos(self.sceneblock.sozai_pos[idx])
        self.update_drawing()

    def update_sozai_scale(self):
        scale = self.scene_size[0] / self.ctx.resolution[0]

        sozai_images = [get_rescaled_image(
            sozai.get_image(), scale * scl
            ) for sozai, scl in zip(self.sceneblock.get_sozais(), self.sceneblock.sozai_scale)]

        sozai_bmps = [wx.Bitmap.FromBufferRGBA(*img.size, img.tobytes()) for img in sozai_images]

        sozai_objs = [MoveImageObj(
            bmp,
            int(pos[0] * scale) + self.bg_pos[0],
            int(pos[1] * scale) + self.bg_pos[1]
            ) for bmp, pos in zip(sozai_bmps, self.sceneblock.sozai_pos)]
        self.objs = self.objs[:1]
        self.objs += [None for _ in range(len(sozai_objs))]
        for i, order in enumerate(self.sceneblock.sozai_order):
            self.objs[i+1] = sozai_objs[order]
        # self.update_drawing()

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
        if obj:
            self.drag_obj = obj
            self.drag_start_pos = pos
            self.drag_obj.save_pos_diff(pos)
            idx = self.sceneblock.sozai_order.index(self.objs.index(obj)-1)
            pos = tuple(self.to_physical_pos(self.drag_obj.pos))
            self.sceneblock.sozai_pos[idx] = pos # 割と危険な操作。sceneblock内でis_savedがFalseにならない
            # ダイアログを閉じる前に、自分自身をセットし直すことで強制的に発火させることは可能
            event = YKLLayoutPreviewUpdate(self.GetId())
            event.SetInt(idx)
            self.update_order(idx, obj)
            wx.PostEvent(self, event)

    def update_order(self, idx, obj):
        self.objs.remove(obj)
        self.objs.append(obj)
        self.update_drawing()
        sozai_num = len(self.sceneblock.get_sozais())
        cur_order = self.sceneblock.sozai_order[idx]
        for i in range(cur_order+1, sozai_num):
            j = self.sceneblock.sozai_order.index(i)
            self.sceneblock.sozai_order[j] -= 1
        self.sceneblock.sozai_order[idx] = sozai_num - 1

    def on_mouse_leftup(self, event):
        if self.drag_obj:
            pos = event.GetPosition()
            self.drag_obj.pos.x = pos.x + self.drag_obj.diff_pos.x
            self.drag_obj.pos.y = pos.y + self.drag_obj.diff_pos.y
            idx = self.sceneblock.sozai_order.index(self.objs.index(self.drag_obj)-1)
            pos = tuple(self.to_physical_pos(self.drag_obj.pos))
            self.sceneblock.sozai_pos[idx] = pos
            event = YKLLayoutPreviewUpdate(self.GetId())
            event.SetInt(idx)
            wx.PostEvent(self, event)
        self.drag_obj = None
        self.update_drawing()

    def on_mouse_motion(self, event):
        if self.drag_obj is None:
            return
        pos = event.GetPosition()
        self.drag_obj.pos.x = pos.x + self.drag_obj.diff_pos.x
        self.drag_obj.pos.y = pos.y + self.drag_obj.diff_pos.y
        idx = self.sceneblock.sozai_order.index(self.objs.index(self.drag_obj)-1)
        pos = tuple(self.to_physical_pos(self.drag_obj.pos))
        self.sceneblock.sozai_pos[idx] = pos
        event = YKLLayoutPreviewUpdate(self.GetId())
        event.SetInt(idx)
        wx.PostEvent(self, event)
        self.update_drawing()

    def to_physical_pos(self, pos):
        return [int((pos.x - self.bg_pos[0]) * self.resolution[0] / self.scene_size[0]),
                int((pos.y - self.bg_pos[1]) * self.resolution[1] / self.scene_size[1])]

    def to_virtual_pos(self, pos):
        return (int(pos[0] * self.scene_size[0] / self.resolution[0]) + self.bg_pos[0],
                int(pos[1] * self.scene_size[1] / self.resolution[1]) + self.bg_pos[1])


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
