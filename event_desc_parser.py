from grab import Grab
from lxml.etree import tostring
from bs4 import BeautifulSoup
import datetime
import re
import base64
import requests


def month_to_num(month):
    return {
        'января': 1,
        'февраля': 2,
        'марта': 3,
        'апреля': 4,
        'мая': 5,
        'июня': 6,
        'июля': 7,
        'августа': 8,
        'сентября': 9,
        'октября': 10,
        'ноября': 11,
        'декабря': 12
    }[month]


def parse_digital_october_date(date_str):
    # 28 ноября 2017, 10:00
    # 11 – 12 НОЯБРЯ 2017, 10:45
    # 10 – 12 НОЯБРЯ 2017, 10:00

    one_day_pattern = re.compile('\d{1,2} ([А-Яа-я]*) \d{4}, \d\d:\d\d')
    many_days_pattern = re.compile('(\d{1,2})\s*–\s*(\d{1,2}) ([А-Яа-я]*) (\d{4}, \d\d:\d\d)')

    if one_day_pattern.match(date_str):
        month = one_day_pattern.match(date_str).group(1)
        date_str = date_str.replace(month, str(month_to_num(month)))
        date = datetime.datetime.strptime(date_str, "%d %m %Y, %H:%M")
        end_date = date.replace(day=date.day, hour=22, minute=0, second=0, microsecond=0)
        return [(date, end_date)]
    elif many_days_pattern.match(date_str):
        match = many_days_pattern.match(date_str)
        first_day = match.group(1)
        last_day = match.group(2)
        month = match.group(3)
        month = month_to_num(month)
        year_and_time = match.group(4)
        dates = []
        first_date = None
        for day in range(int(first_day), int(last_day) + 1):
            start_date = datetime.datetime.strptime(str(day) + " " + str(month) + " " + year_and_time,
                                                    "%d %m %Y, %H:%M")
            if first_date is None:
                first_date = start_date
            end_date = start_date.replace(day=start_date.day, hour=22, minute=0, second=0, microsecond=0)
            dates.append((start_date, end_date))

        return dates


def prepare_date(dates):
    new_dates = []
    for day in dates:
        event_date = day[0].strftime('%Y-%m-%d')
        start_time = day[0].strftime('%H:%M')
        end_time = day[1].strftime('%H:%M')
        date = {"event_date": event_date, "start_time": start_time, "end_time": end_time}
        new_dates.append(date)
    return new_dates


def prepare_desc(desc):
    if len(desc) > 2000:
        return desc[:2000]
    return desc


def get_public_date():
    public_date = datetime.datetime.today() \
        .replace(day=datetime.datetime.today().day, hour=14, minute=0, second=0, microsecond=0)
    public_date += datetime.timedelta(days=1)
    return public_date.strftime('%Y-%m-%dT%H:%M:%SZ')


def get_default_img():
    with open("evendate.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    image_horizontal = "data:image/png;base64," + encoded_string.decode("utf-8")
    return image_horizontal


def parse_desc_from_digit_october(url):
    base_url = "http://digitaloctober.ru"
    org_id = 27

    g = Grab(log_file='out.html')
    g.go(url)
    print("parse " + url)

    title_block = g.doc.select('//div[@class="event event_close"]').node()
    title = title_block.xpath('.//h1')[0].text.strip()
    date_raw = title_block.xpath('.//span[@class="date"]')[0].text.strip()
    dates = parse_digital_october_date(date_raw)
    img_url = title_block.xpath('//meta[@property="og:image"]')[0].get("content")
    format_list = title_block.xpath('.//span[@class="type"]')
    format_str = None
    if len(format_list) > 0:
        format_str = format_list[0].text

    text_block = g.doc.select('//div[@class="text_description pt15"]').node()
    text = BeautifulSoup(tostring(text_block), "lxml").text

    map_block = g.doc.select('//div[@class="contact"]').node()
    map_text = map_block.xpath('.//p')[0].text

    price = 1000

    tags = ["Digital October"]
    if format_str:
        tags.append(format_str)

    img_raw = requests.get(img_url, allow_redirects=True)
    img = "data:image/png;base64," + base64.b64encode(img_raw.content).decode("utf-8")

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates), "description": prepare_desc(text),
           "location": map_text, "price": price, "tags": tags, "detail_info_url": url,
           "public_at": get_public_date(), "image_horizontal": img,
           "filenames": {'horizontal': "image.png"}}
    return res


def parse_desc_from_planetarium(url):
    base_url = "http://www.planetarium-moscow.ru/"
    org_id = 130

    g = Grab(log_file='out.html')
    g.go(url)
    print("parse " + url)

    event_block = g.doc.select('//div[@class="item news_item"]').node()

    title = event_block.xpath('.//h3')[0].text.strip()

    day_pattern = re.compile('[А-Яа-я:]*\s*(\d{1,2}).(\d{1,2}).(\d{4})')

    date_raw = event_block.xpath('.//div[@class="date"]')[0].text.strip()
    match = day_pattern.match(date_raw)
    dates = []
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        date = datetime.datetime(year=year, month=month, day=day, hour=0)
        end_date = date.replace(hour=23)
        dates = [(date, end_date)]

    texts = event_block.xpath('.//p')
    description = ""
    for text_elem in texts:
        if text_elem.text is not None:
            description += BeautifulSoup(tostring(text_elem), "lxml").text

    price = 500
    location = "г. Москва, ул.Садовая-Кудринская 5, стр. 1, м. Баррикадная, Краснопресненская"

    tags = ["Московский планетариум"]

    return {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
            "description": prepare_desc(description),
            "location": location, "price": price, "tags": tags, "detail_info_url": url,
            "public_at": get_public_date(), "image_horizontal": get_default_img(),
            "filenames": {'horizontal': "image.png"}}


def parse_desc_from_strelka(url):
    base_url = "http://strelka.com"
    org_id = 6

    g = Grab(log_file='out.html')
    g.go(url)
    print("parse " + url)

    title_block = g.doc.select('//h1[@class="new_top_title new_regular"]').node()
    title = title_block.xpath('.//a')[0].text.strip()

    description_block = g.doc.select('//div[@class="new_event_body_text"]').node()

    texts = description_block.xpath('.//p')
    description = ""
    for text_elem in texts:
        if text_elem.text is not None:
            description += BeautifulSoup(tostring(text_elem), "lxml").text

    info_block = g.doc.select('//div[@class="new_right_colomn_inner"]').node()
    info_blocks = info_block.xpath('.//div[@class="new_event_detail new_mono"]')
    tag = info_blocks[0][0].tail
    date_raw = info_blocks[1][0].tail
    time_raw = info_blocks[2][0].tail

    date_str = date_raw + " " + time_raw
    date = datetime.datetime.strptime(date_str, "%d.%m %H:%M")
    date = date.replace(year=datetime.datetime.today().year)
    end_date = date.replace(day=date.day, hour=date.hour + 2, minute=0, second=0, microsecond=0)
    dates = [(date, end_date)]

    place = info_blocks[3][0].tail
    price = info_blocks[4][0].tail
    price = 0
    background_style = g.doc.select('//div[@class="inner"]').node().get("style")

    img_pattern = re.compile(r"url\(([\w\/\-.]*)\)")

    match = img_pattern.search(background_style)
    if match:
        img_url = base_url + match.group(1)
        img_raw = requests.get(img_url, allow_redirects=True)
        img = "data:image/png;base64," + base64.b64encode(img_raw.content).decode("utf-8")
    else:
        img = get_default_img()

    # map_block = g.doc.select('//div[@class="contact"]').node()
    # map_text = map_block.xpath('.//p')[0].text
    #
    # price = 1000
    #
    tags = ["Стрелка", tag]

    # img_raw = requests.get(img_url, allow_redirects=True)
    # img = "data:image/png;base64," + base64.b64encode(img_raw.content).decode("utf-8")
    #
    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description),
           "location": place, "price": price, "tags": tags, "detail_info_url": url,
           "public_at": get_public_date(), "image_horizontal": img,
           "filenames": {'horizontal': "image.png"}}
    return res
