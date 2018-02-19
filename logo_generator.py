from PIL import Image, ImageDraw, ImageFont, ImageOps
import re
from random import randint
from io import BytesIO
import sys


def get_string(title):
    r = re.findall('([А-ЯA-Z])', title)
    try:
        return r[0] + r[1] + r[2]
    except IndexError:
        try:
            return r[0] + r[1]
        except IndexError:
            return title[:2].capitalize()


def generate_logo(title):
    size = (500, 500)
    img_w, img_h = size
    img = Image.new('RGB', (img_w, img_h), color=(get_color_int(), get_color_int(), get_color_int()))
    d = ImageDraw.Draw(img)
    text = get_string(title)
    fnt = ImageFont.truetype(get_font_path(), get_font_size(text))
    w, h = d.textsize(text, font=fnt)
    d.text(((img_w - w) / 2, (img_h - h) / 2), text, font=fnt, fill=(255, 255, 255))

    img_raw = BytesIO()
    img.save(img_raw, format='PNG')
    return img_raw.getvalue()


def circle_img(img, size):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    output = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    return


def get_color_int():
    return randint(100, 200)


def get_font_path():
    if sys.platform.startswith('win32'):
        return 'C:\Windows\Fonts\Roboto-Medium.ttf'
    elif sys.platform.startswith('darwin'):
        return '/Library/Fonts/Roboto-Medium.ttf'


def get_font_size(result_title):
    if len(result_title) == 2:
        return 208
    else:
        return 188
