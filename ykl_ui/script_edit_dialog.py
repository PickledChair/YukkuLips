"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

import shutil
import subprocess

import wx

from ykl_core.ykl_script import YKLScript


class YKLScriptEditDialog(wx.Dialog):
    def __init__(self, parent, ctx):
        super().__init__(parent, title="シナリオ編集", size=(800, 680), style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX)
        self.ctx = ctx
        self.temp_dir = self.ctx.get_project_path() / "temp"

        if not self.temp_dir.exists():
            self.temp_dir.mkdir()
        box = wx.BoxSizer(wx.VERTICAL)
        self.tctrl = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER, size=(780, 500))
        script = YKLScript.create_from_context(self.ctx)
        self.tctrl.SetValue(script.into_text())
        box.Add(self.tctrl, 1, flag=wx.ALL | wx.EXPAND, border=10)

        discript_panel = DiscriptionPanel(self, wx.ID_ANY)
        box.Add(discript_panel, 1, flag=wx.ALL | wx.EXPAND, border=5)

        btns = wx.BoxSizer(wx.HORIZONTAL)
        myv_btn = wx.Button(self, wx.ID_ANY, "MYukkuriVoiceに受け渡す")
        self.Bind(wx.EVT_BUTTON, self.OnMYukkuriBtnClick, id=myv_btn.GetId())
        btns.Add(myv_btn, flag=wx.ALL, border=5)
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "キャンセル")
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=cancel_btn.GetId())
        btns.Add(cancel_btn, flag=wx.ALL, border=5)
        ok_btn = wx.Button(self, wx.ID_OK, "適用して閉じる")
        self.Bind(wx.EVT_BUTTON, self.OnBtnClick, id=ok_btn.GetId())
        btns.Add(ok_btn, flag=wx.ALL, border=5)
        # btns.Layout()

        box.Add(btns, 0, flag=wx.RIGHT | wx.TOP | wx.ALIGN_RIGHT, border=5)
        box.Layout()
        self.SetSizer(box)

        self.Bind(wx.EVT_CLOSE, self.OnClose, id=self.GetId())

    def OnClose(self, event):
        if self.temp_dir.exists():
            shutil.rmtree(str(self.temp_dir))
        event.Skip()

    def OnMYukkuriBtnClick(self, event):
        self.send_to_myukkurivoice()

    def send_to_myukkurivoice(self):
        txt_path = self.temp_dir / "scenario.txt"
        text = ''.join(self.tctrl.GetValue().split("--\n"))
        with txt_path.open('w') as f:
            f.write(text)
        try:
            p = subprocess.Popen(["open", "-a", "MYukkuriVoice", str(txt_path)])
            p.wait()
        except OSError:
            wx.MessageBox("MYukkuriVoice.appはアプリケーションフォルダ内に"
                          "ある必要があります",
                          "MYukkuriVoiceを開けませんでした",
                          wx.ICON_EXCLAMATION | wx.OK)

    def OnBtnClick(self, event):
        if event.GetId() == wx.ID_OK:
            text = self.tctrl.GetValue()
            script = YKLScript.create_from_text(text)
            if script:
                script.dist_into_context(self.ctx)
            else:
                wx.MessageBox("スクリプトに正しくない記法が用いられています",
                              "エラー", wx.ICON_EXCLAMATION | wx.OK)
                return
        if self.temp_dir.exists():
            shutil.rmtree(str(self.temp_dir))
        self.EndModal(event.GetId())


class DiscriptionPanel(wx.ScrolledWindow):
    def __init__(self, parent, idx):
        super().__init__(parent, idx, size=(780, 100))
        box = wx.BoxSizer(wx.VERTICAL)
        discription = """
        シナリオの記法について：

        以下のように「(キャラ素材名)＞(セリフ)」と書くと、各キャラ素材にセリフを指定できます（"＞"は全角の三角括弧です）。
        （シーンブロックの境目では、"--"とハイフンを２つ続けて入力してください。）

        例：
        れいむ＞こんにちは、ゆっくり霊夢です。
        --
        まりさ＞ゆっくり魔理沙だぜ。
        --
        れいむ＞ゆっくりしていってね！
        まりさ＞ゆっくりしていってね！

        （１つのシーンブロックに複数のキャラ素材のセリフを設定する時は、キャラ素材リストにおける順番通りに記載してください。）
        """
        syntax = wx.StaticText(self, wx.ID_ANY, discription)
        box.Add(syntax)
        box.Layout()
        self.SetSizer(box)
        self.SetVirtualSize(syntax.GetClientSize())
        self.SetScrollRate(20, 20)
