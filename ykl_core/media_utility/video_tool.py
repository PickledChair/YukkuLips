"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

import subprocess


def save_video(cache_path, sound_file, save_file_path, ffmpeg_path):
    p = subprocess.Popen([ffmpeg_path, "-f", "image2", "-pattern_type", "glob", "-framerate", "30",
                          "-i", str(cache_path / "*.png"),
                          "-i", sound_file,
                          "-pix_fmt", "yuv420p", str(save_file_path)])
    p.wait()


def save_silent_video(cache_path, save_file_path, ffmpeg_path):
    p = subprocess.Popen([ffmpeg_path, "-f", "image2", "-pattern_type", "glob", "-framerate", "30",
                          "-i", str(cache_path / "*.png"),
                          "-pix_fmt", "yuv420p", str(save_file_path)])
    p.wait()
