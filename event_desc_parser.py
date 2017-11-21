from grab import Grab
from lxml.etree import tostring
from bs4 import BeautifulSoup
import datetime
import re
import base64


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
        month = one_day_pattern.match(date_str)[1]
        date_str = date_str.replace(month, str(month_to_num(month)))
        date = datetime.datetime.strptime(date_str, "%d %m %Y, %H:%M")
        end_date = date.replace(day=date.day, hour=22, minute=0, second=0, microsecond=0)
        return [(date, end_date)]
    elif many_days_pattern.match(date_str):
        match = many_days_pattern.match(date_str)
        first_day = match[1]
        last_day = match[2]
        month = match[3]
        month = month_to_num(month)
        year_and_time = match[4]
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
    if len(desc) > 1000:
        return desc[:1000]


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
    public_date = datetime.datetime.today() \
        .replace(day=datetime.datetime.today().day + 1, hour=14, minute=0, second=0, microsecond=0)

    img_url = base_url + title_block.xpath('.//img[@class="img"]')[0].get("src")
    format_list = title_block.xpath('.//span[@class="type"]')
    format_str = None
    if len(format_list) > 0:
        format_str = format_list[0].text

    text_block = g.doc.select('//div[@class="text_description pt15"]').node()
    text = BeautifulSoup(tostring(text_block)).text

    map_block = g.doc.select('//div[@class="contact"]').node()
    map_text = map_block.xpath('.//p')[0].text

    price = 1000

    tags = ["Digital October"]
    if format_str:
        tags.append(format_str)

    with open("evendate.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    image_horizontal = "data:image/png;base64," + encoded_string.decode("utf-8")

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates), "description": prepare_desc(text),
           "location": map_text, "price": price, "tags": tags, "detail_info_url": url,
           "public_at": public_date.strftime('%Y-%m-%dT%H:%M:%SZ'), "image_horizontal": image_horizontal,
           "filenames": {'horizontal': "image.png"}}
    return res
