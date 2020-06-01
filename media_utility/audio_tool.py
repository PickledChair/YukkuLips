"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

import subprocess
import shutil
from pathlib import Path

import soundfile as sf
import numpy as np
import wx


def gen_void_sound(path, fs=44100):
    # 基本的に動画に使う音源はサンプリングレートを44100Hzにアップコンバートしている
    sf.write(str(path), np.zeros([int(0.5*fs), 1]), fs)

def get_sound_length(sound_file, add_time=0.):
    if sound_file:
        data, fs = sf.read(str(sound_file), always_2d=True)
        return int(data.shape[0]/1470) + int(add_time*30)
    else:
        return 0

def get_sound_map(sound_file, imgs_num, threshold_ratio=1.0, line=lambda x: x**2 / 2, sizing=lambda x: x**2):
    data, fs = sf.read(str(sound_file), always_2d=True)
    data = [sizing(d[0]) for d in data]
    buf = []
    thresholds = [line(1 / imgs_num * (i + 1)) * threshold_ratio for i in range(imgs_num)]
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

def mix_movie_sounds(file_paths, ffmpeg_path, save_dir):
    file_paths = [file_path for file_path in file_paths if file_path]
    new_path = str(save_dir / "movie_sound") + ".wav"
    if Path(new_path).exists():
        shutil.rmtree(new_path)
    input_list = []
    for file_path in file_paths:
        input_list.extend(["-i", str(file_path)])
    p = subprocess.Popen([ffmpeg_path,]
                         + input_list
                         + ["-filter_complex", f"amix=inputs={len(file_paths)}:duration=longest", new_path])
    p.wait()
    return Path(new_path)

def gen_movie_sound(file_path, ffmpeg_path, save_dir, prefix_time=0.):
    new_path = str(save_dir / file_path.stem) + ".wav"
    if Path(new_path).exists():
        i = 1
        while Path(new_path).exists():
            new_path = str(save_dir / file_path.stem) + str(i) + ".wav"
            i += 1
    p = subprocess.Popen([ffmpeg_path, "-i", str(file_path),
                          "-ar", "44100", new_path])
    p.wait()
    if prefix_time > 0:
        data, fs = sf.read(new_path, always_2d=True)
        data = np.vstack(
            [np.zeros([int(prefix_time*fs), data.shape[1]]),
             data])
        sf.write(new_path, data, fs)
    return Path(new_path)


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
            try:
                total_audio_data = np.vstack([total_audio_data,
                                              np.zeros([int(interval*samplerate), total_audio_data.shape[1]])])
                total_audio_data = np.vstack([total_audio_data, data])
                progress += 1
                progress_dialog.Update(progress, "音声ファイル連結中...({}/{})".format(progress, len(sound_files)))
            except Exception as e:
                progress_dialog.Close()
                wx.LogError("YukkuLips error: 音声ファイルの結合に失敗しました\n"
                            "音声ファイル間でチャンネル数が一致していない可能性があります\n" + str(e))
                return
    if (total_audio_data is not None) and (audio_cache is not None):
        file_name = str(audio_cache / "temp.wav")
        sf.write(file_name, total_audio_data, samplerate)
        return file_name


def convert_mp3_to_wav(file_path, ffmpeg_path, save_dir):
    new_path = str(save_dir / file_path.stem) + ".wav"
    if Path(new_path).exists():
        i = 1
        while Path(new_path).exists():
            new_path = str(save_dir / file_path.stem) + str(i) + ".wav"
            i += 1
    p = subprocess.Popen([ffmpeg_path, "-i", str(file_path),
                          "-vn", "-ac", "1", "-ar", "44100", "-acodec", "pcm_s16le",
                          "-f", "wav", new_path])
    p.wait()
    return new_path

