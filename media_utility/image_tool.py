"""
yukkulips

copyright (c) 2018 - 2020 suitcase

this software is released under the mit license.
https://github.com/pickledchair/yukkulips/blob/master/license.txt
"""

from PIL import Image, ImageOps, ImageChops
from collections import namedtuple


ImageInfo = namedtuple("ImageInfo", ("path", "part", "is_mul", "is_front"))
BgColor = namedtuple("BgColor", ("name", "color_tuple"))


def combine_images(*image_infos, base_image=None, base_size=(400, 400), bg_color=(0, 0, 255, 255)):
    if base_image is None:
        if len(image_infos) > 0:
            base_size = Image.open(str(image_infos[0].path)).size
        base_image = Image.new("RGBA", base_size, bg_color)
    complete_image = base_image
    mul_image_infos = []
    front_image_infos = []

    # 部品画像がベース画像からはみ出ていた時のサイズ修正
    def get_modified_image(image, complete_image, bg_color):
        if image.size[0] >= complete_image.size[0] and image.size[1] >= complete_image.size[1]:
            new_image = Image.new("RGBA", image.size, bg_color)
            new_image.paste(complete_image,
                            (int((image.size[0] - complete_image.size[0]) / 2),
                             int((image.size[1] - complete_image.size[1]) / 2)))
            complete_image = new_image
        elif image.size[0] <= complete_image.size[0] and image.size[1] <= complete_image.size[1]:
            new_image = Image.new("RGBA", complete_image.size, (0, 0, 0, 0))
            new_image.paste(image,
                            (int((complete_image.size[0] - image.size[0]) / 2),
                             int((complete_image.size[1] - image.size[1]) / 2)))
            image = new_image
        elif image.size[0] >= complete_image.size[0] and image.size[1] <= complete_image.size[1]:
            new_image1 = Image.new("RGBA", (image.size[0], complete_image.size[1]), bg_color)
            new_image1.paste(complete_image,
                             (int((image.size[0] - complete_image.size[0]) / 2), 0))
            new_image2 = Image.new("RGBA", (image.size[0], complete_image.size[1]), (0, 0, 0, 0))
            new_image2.paste(image,
                             (0, int((complete_image.size[1] - image.size[1]) / 2)))
            complete_image = new_image1
            image = new_image2
        elif image.size[0] <= complete_image.size[0] and image.size[1] >= complete_image.size[1]:
            new_image1 = Image.new("RGBA", (complete_image.size[0], image.size[1]), bg_color)
            new_image1.paste(complete_image,
                             (0, int((image.size[1] - complete_image.size[1]) / 2)))
            new_image2 = Image.new("RGBA", (complete_image.size[0], image.size[1]), (0, 0, 0, 0))
            new_image2.paste(image,
                             (int((complete_image.size[1] - image.size[1]) / 2), 0))
            complete_image = new_image1
            image = new_image2
        return image, complete_image

    # 通常の描画順に基づく画像合成
    for image_info in image_infos:
        image = Image.open(str(image_info.path))
        if (not image_info.is_mul) and (not image_info.is_front):
            if image.size != complete_image.size:
                image, complete_image = get_modified_image(image, complete_image, bg_color)
            complete_image = Image.alpha_composite(complete_image, image)
        else:
            if image_info.is_mul:
                mul_image_infos.append(image_info)
            if image_info.is_front:
                front_image_infos.append(image_info)

    # 乗算で重ねるとしてはけられていた画像を合成する
    for image_info in mul_image_infos:
        image = Image.open(str(image_info.path))
        if image.size != complete_image.size:
            image, complete_image = get_modified_image(image, complete_image, bg_color)
        image = ImageChops.multiply(complete_image, image)
        complete_image = Image.alpha_composite(complete_image, image)

    # 基本の描画順ではなく最前面に合成される画像の合成
    for image_info in front_image_infos:
        image = Image.open(str(image_info.path))
        if image.size != complete_image.size:
            image, complete_image = get_modified_image(image, complete_image, bg_color)
        complete_image = Image.alpha_composite(complete_image, image)

    return complete_image

def get_mirror_image(image):
    return ImageOps.mirror(image)

def get_scene_image(images, pos_list, order_list, bg_size=(1920, 1080), bg_color=(0, 0, 225, 225)):
    scene_image = Image.new("RGBA", bg_size, bg_color)
    # for image, pos in zip(images, pos_list):
    for order in order_list:
        image = images[order]
        pos = pos_list[order]
        temp_image = Image.new("RGBA", bg_size, (0, 0, 0, 0))
        if pos[0] > bg_size[0] or pos[1] > bg_size[1]:
            continue
        if pos[0] < 0:
            image = image.crop((-pos[0], 0, image.size[0], image.size[1]))
            pos = (0, pos[1])
        if pos[1] < 0:
            image = image.crop((0, -pos[1], image.size[0], image.size[1]))
            pos = (pos[0], 0)
        if pos[0]+image.size[0] > bg_size[0]:
            image = image.crop((0, 0, bg_size[0]-pos[0], image.size[1]))
        if pos[1]+image.size[1] > bg_size[1]:
            image = image.crop((0, 0, image.size[0], bg_size[1]-pos[1]))
        temp_image.paste(image, pos)
        scene_image = Image.alpha_composite(scene_image, temp_image)

    return scene_image

def get_rescaled_image(image, scale):
    if scale == 1.0:
        return image
    image = image.resize((int(image.size[0] * scale), int(image.size[1] * scale)), Image.LANCZOS)
    return image

def get_thumbnail(image, size=100):
    w, h = image.size
    if w >= h:
        resize_ratio = size / w
    else:
        resize_ratio = size / h
    image = image.resize((int(w*resize_ratio), int(h*resize_ratio)), Image.LANCZOS)
    rw, rh = image.size
    bg = Image.new("RGBA", (size, size), (255,255,255,0))
    pos = (max(0, int((size-rw)/2)), max(0, int((size-rh)/2)))
    bg.paste(image, pos)

    return bg

def open_img(path):
    return Image.open(str(path))

def save_anime_frame(args):
    frame, images_dir, _count, digit_num, queue = args[0], args[1], args[2], args[3], args[4]
    file_name = "frame" + str(_count).zfill(digit_num) + ".png"
    frame.save(str(images_dir / file_name), quality=95)
    queue.put(file_name)
