"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://opensource.org/licenses/mit-license.php
"""

import soundfile as sf
import numpy as np
import wx


def get_sound_map(sound_file, imgs_num):
    data, fs = sf.read(sound_file, always_2d=True)
    data = [d[0] ** 2 for d in data]
    buf = []
    thresholds = [(1 / imgs_num * (i + 1)) ** 2 / 2 for i in range(imgs_num)]
    work_num = int(len(data)/1470)
    progress_dialog = wx.ProgressDialog(
        title="動画出力",
        message="動画出力中...",
        maximum=work_num,
        style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
    progress_dialog.Show()
    progress = 0
    while len(data) > 1470:
        break_flag = False
        mean = sum(data[:1470]) / 1470
        for i, g in enumerate(thresholds):
            if mean <= g:
                buf.append(i)
                break_flag = True
                break
        if not break_flag:
            buf.append(len(thresholds) - 1)
        data = data[1470:]
        progress += 1
        progress_dialog.Update(progress, "音声に対するリップシンク...({}/{} フレーム)".format(progress, work_num))

    return buf


def join_sound_files(*sound_files, interval=2.0, audio_cache=None):
    samplerate = 0
    total_audio_data = None
    progress_dialog = wx.ProgressDialog(
        title="動画出力",
        message="動画出力中...",
        maximum=len(sound_files),
        style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE)
    progress_dialog.Show()
    progress = 0
    for sound_file in sound_files:
        data, samplerate = sf.read(sound_file, always_2d=True)
        if total_audio_data is None:
            total_audio_data = data
            progress += 1
            progress_dialog.Update(progress, "音声ファイル連結中...({}/{})".format(progress, len(sound_files)))
        else:
            total_audio_data = np.vstack([total_audio_data, np.zeros([int(interval*samplerate), 1])])
            total_audio_data = np.vstack([total_audio_data, data])
            progress += 1
            progress_dialog.Update(progress, "音声ファイル連結中...({}/{})".format(progress, len(sound_files)))
    if (total_audio_data is not None) and (audio_cache is not None):
        file_name = str(audio_cache / "temp.wav")
        sf.write(file_name, total_audio_data, samplerate)
        return file_name
