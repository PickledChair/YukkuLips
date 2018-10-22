"""
YukkuLips

Copyright (c) 2018 SuitCase

This software is released under the MIT License.
https://github.com/PickledChair/YukkuLips/blob/master/LICENSE.txt
"""

from PIL import Image, ImageOps, ImageChops


def combine_images(*image_infos, base_image=None, base_size=(400, 400), bg_color=(0, 0, 255, 255)):
    if base_image is None:
        if len(image_infos) > 0:
            base_size = Image.open(str(image_infos[0].path)).size
        base_image = Image.new("RGBA", base_size, bg_color)
    complete_image = base_image
    mul_image_infos = []
    front_image_infos = []

    for image_info in image_infos:
        image = Image.open(str(image_info.path))
        if (not image_info.is_mul) and (not image_info.is_front):
            if image.size != complete_image.size:
                # もうちょっとスマートな感じに一般化したいが、場当たり的に場合分けしたらダーティになってしまった
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
        image = ImageChops.multiply(complete_image, image)
        complete_image = Image.alpha_composite(complete_image, image)
    # 基本の描画順ではなく最前面に合成される画像の合成
    for image_info in front_image_infos:
        image = Image.open(str(image_info.path))
        if image.size != complete_image.size:
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
        complete_image = Image.alpha_composite(complete_image, image)
    return complete_image


def save_image(image, path, rev_flag=False, is_anim=False, bg_size=(1280, 720), bg_color=(0, 0, 255, 255),
               pos=(0, 0), scale=1.0):
    if rev_flag:
        image = ImageOps.mirror(image)
    if is_anim:
        image = image.resize((int(image.size[0] * scale), int(image.size[1] * scale)), Image.LANCZOS)
        if pos[0] < 0:
            image = image.crop((-pos[0], 0, image.size[0], image.size[1]))
            pos = (0, pos[1])
        if pos[1] < 0:
            image = image.crop((0, -pos[1], image.size[0], image.size[1]))
            pos = (pos[0], 0)
        if pos[0] > bg_size[0] or pos[1] > bg_size[1]:
            movie_image = Image.new("RGBA", bg_size, bg_color)
            movie_image.save(str(path), quality=95)
            return
        if pos[0]+image.size[0] > bg_size[0]:
            image = image.crop((0, 0, bg_size[0]-pos[0], image.size[1]))
        if pos[1]+image.size[1] > bg_size[1]:
            image = image.crop((0, 0, image.size[0], bg_size[1]-pos[1]))
        movie_image = Image.new("RGBA", bg_size, bg_color)
        movie_image.paste(image, pos)
        movie_image.save(str(path), quality=95)
    else:
        image.save(str(path), quality=95)
