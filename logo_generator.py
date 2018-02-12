from PIL import Image, ImageDraw, ImageFont
import re
from transliterate import translit
from random import randint
from io import BytesIO


def get_string(title):
    r = re.findall('([А-ЯA-Z])', title)
    try:
        return r[0] + r[1]
    except KeyError:
        return title[:1].capitalize() + title[1:2].capitalize()


def generate_logo(title):
    from PIL import Image
    img_w, img_h = (500, 500)
    img = Image.new('RGB', (img_w, img_h), color=(get_color_int(), get_color_int(), get_color_int()))
    d = ImageDraw.Draw(img)
    fnt = ImageFont.truetype('/Library/Fonts/Roboto-Medium.ttf', 208)
    w, h = d.textsize(translit(get_string(title).capitalize(), 'ru', reversed=True), font=fnt)
    d.text(((img_w - w) / 2, (img_h - h) / 2), get_string(title), font=fnt, fill=(255, 255, 255))
    img_raw = BytesIO()
    d.save(img_raw, format='PNG')
    return img_raw.getvalue()


def get_color_int():
    return randint(100, 200)
