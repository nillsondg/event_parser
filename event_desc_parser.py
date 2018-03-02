from grab import Grab
from lxml.etree import tostring
from bs4 import BeautifulSoup
import datetime
import re
import base64
import requests
from utils import get_default_img, get_img
import json


def get_grab():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    g = Grab(log_file='out.html', headers=headers)
    g.setup(connect_timeout=60, timeout=60)
    return g


def prepare_date(dates):
    new_dates = []
    for day in dates:
        event_date = day[0].strftime('%Y-%m-%d')
        start_time = day[0].strftime('%H:%M')
        end_time = day[1].strftime('%H:%M')
        date = {"event_date": event_date, "start_time": start_time, "end_time": end_time}
        new_dates.append(date)
    return new_dates


def prepare_title(title):
    if len(title) > 150:
        return title[:150]
    return title


def prepare_desc(desc):
    if len(desc) > 2000:
        return desc[:2000]
    return desc


def get_public_date():
    public_date = datetime.datetime.today() \
        .replace(day=datetime.datetime.today().day, hour=14, minute=0, second=0, microsecond=0)
    public_date += datetime.timedelta(days=1)
    return public_date.strftime('%Y-%m-%dT%H:%M:%SZ')


def month_to_num(month):
    return {
        'января': 1,
        'январь': 1,
        'янв': 1,
        'февраля': 2,
        'февраль': 2,
        'фев': 2,
        'марта': 3,
        'март': 3,
        'мар': 3,
        'апреля': 4,
        'апрель': 4,
        'апр': 4,
        'мая': 5,
        'май': 5,
        'июня': 6,
        'июнь': 6,
        'июн': 6,
        'июля': 7,
        'июль': 7,
        'июл': 7,
        'августа': 8,
        'август': 8,
        'авг': 8,
        'сентября': 9,
        'сентябрь': 9,
        'сен': 9,
        'октября': 10,
        'октябрь': 10,
        'окт': 10,
        'ноября': 11,
        'ноябрь': 11,
        'ноя': 11,
        'декабря': 12,
        'декабрь': 12,
        'дек': 12
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


def parse_desc_from_digit_october(url):
    base_url = "http://digitaloctober.ru"
    org_id = 27

    g = get_grab()
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
           "location": map_text, "tags": tags, "detail_info_url": url,
           "public_at": get_public_date(), "image_horizontal": img,
           "filenames": {'horizontal': "image.png"}}
    return res


def parse_desc_from_planetarium(url):
    base_url = "http://www.planetarium-moscow.ru/"
    org_id = 130

    g = get_grab()
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
    img, filename = get_default_img(img_name="planetarium.png")

    return {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
            "description": prepare_desc(description),
            "location": location, "tags": tags, "detail_info_url": url,
            "public_at": get_public_date(), "image_horizontal": img,
            "filenames": {'horizontal': filename}}


def process_strelka_date(date_raw, time_raw):
    many_days_pattern = re.compile('(\d{1,2}).(\d{1,2})-(\d{1,2}).(\d{1,2})')

    match_many = many_days_pattern.match(date_raw)
    if match_many:
        date_str_start = match_many.group(1) + " " + match_many.group(
            2) + " " + str(datetime.datetime.today().year) + " " + time_raw
        first_day = datetime.datetime.strptime(date_str_start, "%d %m %Y %H:%M")
        first_end_day = first_day.replace(day=first_day.day, hour=first_day.hour + 2, minute=0, second=0, microsecond=0)

        dates = [(first_day, first_end_day)]
        last_day = first_day
        for day in range(int(match_many.group(1)) + 1, int(match_many.group(3)) + 1):
            start_date = last_day + datetime.timedelta(days=1)
            end_date = start_date + datetime.timedelta(hours=2)
            last_day = start_date
            dates.append((start_date, end_date))
    else:
        date_str = date_raw + " " + time_raw
        date = datetime.datetime.strptime(date_str, "%d.%m %H:%M")
        date = date.replace(year=datetime.datetime.today().year)
        end_date = date.replace(day=date.day, hour=date.hour + 2, minute=0, second=0, microsecond=0)
        dates = [(date, end_date)]
    return dates


def parse_desc_from_strelka(url):
    base_url = "http://strelka.com"
    org_id = 6

    g = get_grab()
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

    dates = process_strelka_date(date_raw, time_raw)

    place = info_blocks[3][0].tail
    if place == "зал":
        place = "г. Москва, Берсеневская наб. 14, стр. 5а, м. Кропоткинская"

    price = info_blocks[4][0].tail
    price = 0
    background_style = g.doc.select('//div[@class="inner"]').node().get("style")

    img_pattern = re.compile(r"url\(([\w\/\-.]*)\)")

    match = img_pattern.search(background_style)
    if match:
        img_url = base_url + match.group(1)
        img, filename = get_img(img_url)
    else:
        img, filename = get_default_img()

    # map_block = g.doc.select('//div[@class="contact"]').node()
    # map_text = map_block.xpath('.//p')[0].text
    tags = ["Стрелка", tag]

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description),
           "location": place, "tags": tags, "detail_info_url": url,
           "public_at": get_public_date(), "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def parse_desc_from_tretyako(url):
    base_url = "https://www.tretyakovgallery.ru"
    org_id = 8

    g = get_grab()
    g.go(url)
    print("parse " + url)

    event_info_block = g.doc.select('//header[contains(@class, "header-event")]').node()

    tag = event_info_block.xpath('.//span[@class="event-info__type type"]')[0].text
    date_raw = event_info_block.xpath('.//span[@class="event-info__date"]')[0].text.lower()
    time_raw = event_info_block.xpath('.//span[@class="event-info__time"]')[0].text

    day_pattern = re.compile('\d{1,2} ([А-Яа-я]*)')
    match = day_pattern.match(date_raw)
    if match:
        month = match.group(1)
        date_str = date_raw.replace(month, str(month_to_num(month)))

        year = datetime.datetime.today().year
        if month_to_num(month) < datetime.datetime.today().month:
            year += 1

        datetime_str = date_str + " " + str(year) + " " + time_raw
    else:
        raise ValueError("Can't parse date")

    date = datetime.datetime.strptime(datetime_str, "%d %m %Y %H:%M")
    end_date = date + datetime.timedelta(hours=2)
    dates = [(date, end_date)]

    title = event_info_block.xpath('.//h1[@class="header-event__title h1"]')[0].text

    event_description_block = g.doc.select('//section[@class="event-desc"]').node()

    text_desc_block = event_description_block.xpath('.//div[@class="col-sm-7"]')[0]

    try:
        description = text_desc_block.xpath('.//div[@class="event-desc__lid"]')[0].text + "\r\n"
    except IndexError:
        description = ""

    texts = text_desc_block.xpath('.//p')
    if len(texts) == 1 and texts[0].text is None:
        texts = texts[0]
    for text_elem in texts:
        if text_elem.text is not None:
            description += BeautifulSoup(tostring(text_elem), "lxml").text

    try:
        place = "Москва, " + g.doc.select('//div[@class="museum__address"]').node().text
    except IndexError:
        place = "Москва"

    price = 0

    tags = ["Третьяковка", tag]

    try:
        img_url = base_url + g.doc.select('//img[@class="header-event__img"]').node().get('src')
        img, filename = get_img(img_url)
    except IndexError:
        img, filename = get_default_img("tretyako.jpg", "jpg")

    res = {"organization_id": org_id, "title": prepare_title(title), "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": place, "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(), "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def parse_garage_dates(date_raw, time_raw):
    # 1 декабря 2017
    # 19:30−21:00

    # 7 октября – 23 декабря 2017
    # По субботам, 13:00–15:00

    day_pattern = re.compile('(\d{1,2}) ([А-Яа-я]*) (\d{4})')
    many_days_pattern = re.compile('(\d{1,2})\s*([А-Яа-я]*)?\s*(\d{0,4})?\s*–\s*(\d{1,2}) ([А-Яа-я]*) (\d{4})')
    time_pattern = re.compile('(\d\d):(\d\d)–?(\d\d)?:?(\d\d)?')

    one_day_match = day_pattern.match(date_raw)
    many_days_match = many_days_pattern.match(date_raw)
    time_match = time_pattern.search(time_raw)

    if many_days_match and time_match:
        month1 = many_days_match.group(2)
        month2 = many_days_match.group(5)
        if month1 is "":
            month1 = month2

        first_day = many_days_match.group(1)
        last_day = many_days_match.group(4)
        year1 = many_days_match.group(3)
        year2 = many_days_match.group(6)
        if year1 is "":
            year1 = year2

        first_date = datetime.datetime.strptime(str(first_day) + " " + str(month_to_num(month1)) + " " + year1,
                                                "%d %m %Y")
        last_date = datetime.datetime.strptime(str(last_day) + " " + str(month_to_num(month2)) + " " + year2,
                                               "%d %m %Y")

        start_hours = int(time_match.group(1))
        start_minutes = int(time_match.group(2))
        end_hours = time_match.group(3)
        end_minutes = time_match.group(4)
        if end_hours is not None:
            end_hours = int(end_hours)
            end_minutes = int(end_minutes)
        else:
            end_hours, end_minutes = int(start_hours) + 2, start_minutes
            if end_hours > 23:
                end_hours = 23
                end_minutes = 59

        dates = []
        for date in date_range(first_date, last_date + datetime.timedelta(days=1)):
            start_date = date.replace(hour=start_hours, minute=start_minutes)
            end_date = date.replace(hour=end_hours, minute=end_minutes)
            dates.append((start_date, end_date))

        return dates
    elif one_day_match and time_match:
        month = one_day_match.group(2)
        date_str = date_raw.replace(month, str(month_to_num(month)))
        start_hours = time_match.group(1)
        start_minutes = time_match.group(2)
        date = datetime.datetime.strptime(date_str + " " + time_match.group(1) + ":" + time_match.group(2),
                                          "%d %m %Y %H:%M")
        end_hours = time_match.group(3)
        end_minutes = time_match.group(4)
        if end_hours is not None:
            end_hours = int(end_hours)
            end_minutes = int(end_minutes)
        else:
            end_hours, end_minutes = int(start_hours) + 2, int(start_minutes)
            if end_hours > 23:
                end_hours = 23
                end_minutes = 59
        end_date = date.replace(day=date.day, hour=end_hours, minute=end_minutes)
        return [(date, end_date)]
    else:
        raise ValueError("Can't parse date " + date_raw + " or time " + time_raw)


def __parse_event_desc_from_garage(url):
    base_url = "https://garagemca.org"
    org_id = 59

    g = get_grab()
    g.go(url)
    print("parse " + url)

    title = g.doc.select('//h1[@class="event__header__title"]').node()[0].text

    tag_container = g.doc.select('.//div[@class="event__header__tags"]').node()
    tags_blocks = tag_container.xpath('.//a')
    tags = ["Гараж"]

    for tag in tags_blocks:
        tags.append(tag.text)

    datetime_block = g.doc.select('//div[@class="event__meta__timestamp"]').node()
    date_raw = datetime_block.xpath('.//span')[0].text.lower()
    time_block = datetime_block.xpath('.//div')
    if len(time_block) < 1:
        time_raw = "00:00–23:59"
    else:
        time_raw = time_block[0].text.lower()

    dates = parse_garage_dates(date_raw, time_raw)

    event_description_block = g.doc.select('.//div[@class="event__text text"]').node()

    texts = event_description_block.xpath('.//p')
    description = ""
    for text_elem in texts:
        if text_elem.text is not None:
            description += BeautifulSoup(tostring(text_elem), "lxml").text

    place = "Ул. Крымский Вал, д. 9, стр. 32, Парк Горького, Москва, Россия, 119049"

    price = 0

    background_style = g.doc.select('//div[@class="intro-slide__gallery__image"]').node().get("style")

    img_pattern = re.compile(r"url\(([\w\/\-.]*)\)")

    match = img_pattern.search(background_style)
    if match:
        img_url = "http:" + match.group(1)
        img, filename = get_img(img_url)
    else:
        img, filename = get_default_img()

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": place, "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(), "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def __parse_exhibition_desc_from_garage(url):
    base_url = "https://garagemca.org"
    org_id = 59

    g = get_grab()
    g.go(url)
    print("parse " + url)

    title = g.doc.select('//h1[@class="exhibition__header__title"]').node()[0].text

    tags = ["Гараж", "выставка"]

    date_block = g.doc.select('//header[@class="info-bar__date"]').node()
    first_day = date_block.xpath('.//h1')[0].text
    last_day = date_block.xpath('.//h1')[1].text
    first_month = date_block.xpath('.//strong')[0].text
    last_month = date_block.xpath('.//strong')[1].text
    first_year = date_block.xpath('.//span')[1].text
    last_year = date_block.xpath('.//span')[3].text

    time_block = g.doc.select('//article[@class="info-bar__time"]').node()
    time_pattern = re.compile("(\d\d:\d\d)–(\d\d:\d\d)")

    time_match = time_pattern.match(time_block.xpath('.//strong')[0].text)
    start_time = time_match.group(1)
    end_time = time_match.group(2)
    first_date = datetime.datetime.strptime(
        first_day + " " + str(month_to_num(first_month)) + " " + first_year + " " + start_time, "%d %m %Y %H:%M")
    first_end_date = datetime.datetime.strptime(
        first_day + " " + str(month_to_num(first_month)) + " " + first_year + " " + end_time, "%d %m %Y %H:%M")
    last_date = datetime.datetime.strptime(
        str(last_day) + " " + str(month_to_num(last_month)) + " " + last_year + " " + start_time, "%d %m %Y %H:%M")

    dates = []
    for day_count in range((last_date - first_date).days + 1):
        start_date = first_date + datetime.timedelta(day_count)
        end_date = first_end_date + datetime.timedelta(day_count)
        dates.append((start_date, end_date))

    event_description_block = g.doc.select('.//article[contains(@class, "ex-text__section__content")]').node()

    texts = event_description_block.xpath('.//p')
    description = ""
    for text_elem in texts:
        if text_elem.text is not None:
            description += BeautifulSoup(tostring(text_elem), "lxml").text

    place = "Ул. Крымский Вал, д. 9, стр. 32, Парк Горького, Москва, Россия, 119049"

    price = 0

    background_style = g.doc.select('//div[@class="intro-slide__gallery__image"]').node().get("style")

    img_pattern = re.compile(r"url\(([\w\/\-.]*)\)")

    match = img_pattern.search(background_style)
    if match:
        img_url = "http:" + match.group(1)
        img, filename = get_img(img_url)
    else:
        img, filename = get_default_img()

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": place, "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(), "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def parse_desc_from_garage(url):
    if "/exhibition" in url:
        return __parse_exhibition_desc_from_garage(url)
    else:
        return __parse_event_desc_from_garage(url)


def parse_desc_from_yandex(url):
    base_url = "https://events.yandex.ru"
    org_id = 24

    g = get_grab()
    g.go(url)
    print("parse " + url)

    title_block = g.doc.select('//h2[@class="title title_size_xl"]').node()
    title = title_block.text

    header_info_block = g.doc.select('//div[@class="event-header__info"]').node()

    datetime_raw = header_info_block.xpath('.//div[contains(@class, "event-header__when")]')[0].text.strip().lower()
    try:
        city = header_info_block.xpath('.//div[contains(@class, "event-header__place")]')[0].text.strip()
    except IndexError:
        city = "Москва"

    # 5 ДЕКАБРЯ, 18:30
    # ДЕКАБРЬ
    # 2 – 28 АПРЕЛЯ
    one_day_pattern = re.compile('\d{1,2} ([А-Яа-я]*), \d\d:\d\d')
    day_pattern = re.compile(('\d{1,2} ([А-Яа-я]*) (\d{4})'))
    month_pattern = re.compile('([А-Яа-я]*)')
    match = one_day_pattern.match(datetime_raw)
    day_match = day_pattern.match(datetime_raw)
    month_match = month_pattern.match(datetime_raw)
    interval_pattern = re.compile('(\d{1,2})\s*[-–]\s*(\d{1,2})\s*([А-Яа-я]*)')
    interval_match = interval_pattern.match(datetime_raw)

    if match:
        month = match.group(1)
        date_str = datetime_raw.replace(month, str(month_to_num(month)))

        year = datetime.datetime.today().year
        if month_to_num(month) < datetime.datetime.today().month:
            year += 1

        datetime_str = date_str + " " + str(year)

        date = datetime.datetime.strptime(datetime_str, "%d %m, %H:%M %Y")
        end_date = date + datetime.timedelta(hours=2)
        dates = [(date, end_date)]
    elif day_match:
        month = day_match.group(1)
        date_str = datetime_raw.replace(month, str(month_to_num(month)))

        date = datetime.datetime.strptime(date_str, "%d %m %Y")
        date = date.replace(hour=10)
        end_date = date + datetime.timedelta(hours=2)
        dates = [(date, end_date)]
    elif interval_match:
        month = month_to_num(interval_match.group(3))

        start_day = int(interval_match.group(1))
        end_day = int(interval_match.group(2))
        year = datetime.datetime.today().year
        if month < datetime.datetime.today().month and month == 1:
            year += 1
        start_hours, start_minutes = 0, 0
        end_hours, end_minutes = 23, 59
        date = datetime.datetime(year=year, month=month, day=start_day, hour=start_hours,
                                 minute=start_minutes)
        last_date = datetime.datetime(year=year, month=month, day=end_day, hour=end_hours,
                                      minute=end_minutes)
        dates = []
        for day in range((last_date - date).days + 1):
            start_date = date + datetime.timedelta(day)
            end_date = date.replace(hour=end_hours, minute=end_minutes) + datetime.timedelta(day)
            dates.append((start_date, end_date))
    elif month_match:
        month = month_to_num(month_match.group(1))
        year = datetime.datetime.today().year

        date = datetime.datetime(year=year, month=month, day=1, hour=0, minute=0)
        last_date = date + datetime.timedelta(days=30)
        dates = []
        for day in range((last_date - date).days + 1):
            start_date = date + datetime.timedelta(day)
            end_date = date.replace(hour=23, minute=59) + datetime.timedelta(day)
            dates.append((start_date, end_date))
    else:
        raise ValueError("Can't parse date " + datetime_raw)

    description_block = g.doc.select('//div[contains(@class, "event-description")]').node()
    texts = description_block.xpath('.//p')
    description = ""
    for text_elem in texts:
        if text_elem.text is not None:
            description += BeautifulSoup(tostring(text_elem), "lxml").text

    try:
        map_block = g.doc.select('//div[@class="event-place__place-title"]').node()
        map_text = city + ", " + map_block.text
    except IndexError:
        map_text = city

    price = 0

    tags = []
    keywords = g.doc.select('//meta[@name="keywords"]').node().get("content").strip().split(',')
    for key in keywords:
        if len(tags) < 5:
            tags.append(key)

    img, filename = get_default_img("yandex.jpg", "jpg")

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": map_text, "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(),
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def parse_desc_from_flacon(url):
    base_url = "http://flacon.ru"
    org_id = 31

    g = get_grab()
    g.go(url)
    print("parse " + url)

    title = g.doc.select('//meta[@property="og:title"]').node().get("content").strip()

    header_info_block = g.doc.select('//section[@class="preview-section_wrap"]').node()

    try:
        date_block = header_info_block.xpath('.//div[@class="date"] | .//p[@class="date"]')[0]
        date_raw = date_block.text.strip().lower()
        time_raw = date_block.xpath('.//br')[0].tail.strip()
    except IndexError:
        try:
            date_block = header_info_block.xpath('.//div[@class="date"] | .//p[@class="date"]')[2]
            date_raw = date_block.text.strip().lower()
            time_raw = date_block.xpath('.//br')[0].tail.strip()
        except IndexError:
            date_block = header_info_block.xpath('.//h1')[0][0]
            date_raw = date_block.tail.strip().lower()
            time_raw = ""

    date_raw = date_raw.replace(u'\xa0', u' ')

    # 23 ДЕКАБРЯ 2017
    # 27 НОЯБРЯ—3 ДЕКАБРЯ 2017
    # 1 — 31 ДЕКАБРЯ 2017
    # 13:00 – 21:00
    # 23:30
    # no time

    time_pattern = re.compile('(\d\d:\d\d)( - )?(\d\d:\d\d)?')

    match = time_pattern.match(time_raw)

    if match:
        start_hours, start_minutes = match.group(1).split(":")
        start_hours = int(start_hours)
        start_minutes = int(start_minutes)
        end_time = match.group(3)
        if end_time is not None:
            end_hours, end_minutes = end_time.split(":")
            end_hours = int(end_hours)
            end_minutes = int(end_minutes)
        else:
            end_hours, end_minutes = start_hours + 2, start_minutes
            if end_hours > 23:
                end_hours = 23
                end_minutes = 59
    else:
        start_hours, start_minutes = 0, 0
        end_hours, end_minutes = 23, 59

    one_day_pattern = re.compile('(\d{1,2})\s*([А-Яа-я]*)\s*(\d{4})?')
    interval_pattern = re.compile('(\d{1,2})\s*([А-Яа-я]*)?\s*[-—–]\s*(\d{1,2}) ([А-Яа-я]*)\s*(\d{4})?')
    match = one_day_pattern.match(date_raw)
    interval_match = interval_pattern.match(date_raw)
    if interval_match:
        start_month = interval_match.group(2)
        end_month = month_to_num(interval_match.group(4))
        if start_month:
            start_month = month_to_num(start_month)
        else:
            start_month = end_month

        start_day = int(interval_match.group(1))
        end_day = int(interval_match.group(3))
        start_year = interval_match.group(5)
        if start_year:
            start_year = int(start_year)
        else:
            start_year = datetime.datetime.today().year
        end_year = start_year
        date = datetime.datetime(year=start_year, month=start_month, day=start_day, hour=start_hours,
                                 minute=start_minutes)
        last_date = datetime.datetime(year=end_year, month=end_month, day=end_day, hour=end_hours, minute=end_minutes)
        dates = []
        for day in range((last_date - date).days + 1):
            start_date = date + datetime.timedelta(day)
            end_date = date.replace(hour=end_hours, minute=end_minutes) + datetime.timedelta(day)
            dates.append((start_date, end_date))
    elif match:
        month = int(month_to_num(match.group(2)))
        day = int(match.group(1))
        year = match.group(3)
        if year:
            year = int(year)
        else:
            year = datetime.datetime.today().year
        date = datetime.datetime(year=year, month=month, day=day, hour=start_hours, minute=start_minutes)
        end_date = datetime.datetime(year=year, month=month, day=day, hour=end_hours, minute=end_minutes)
        dates = [(date, end_date)]
    else:
        raise ValueError("Can't parse date " + date_raw)

    description_block = \
        g.doc.select('//section[contains(@class, "about-section_wrap")]').node().xpath('.//div[@class="col-md-6"]')[0]

    texts = description_block.xpath('.//p | .//ul')
    description = ""
    for text_elem in texts:
        text = BeautifulSoup(tostring(text_elem), "lxml").text
        if text != "\n\n":
            description += text

    map_text = "Москва, ул. Б. Новодмитровская, 36"

    price = 0

    tags = ["flacon"]

    background_style = header_info_block.get("style")
    img_pattern = re.compile(r"url\(([\w\/\-.]*)\)")
    match = img_pattern.search(background_style)
    if match:
        img_url = base_url + match.group(1)
        img, filename = get_img(img_url)
    else:
        img, filename = get_default_img()

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": map_text, "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(),
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def parse_desc_from_vinzavod(url):
    base_url = "http://www.winzavod.ru"
    org_id = 9

    g = get_grab()
    g.go(url)
    print("parse " + url)

    try:
        title = g.doc.select('//meta[@property="og:title"]').node().get("content").strip()
    except IndexError:
        title_block = g.doc.select('//h2[@class="exhibition-type__name"]').node()
        title = BeautifulSoup(tostring(title_block), "lxml").text.strip()

    date_block = g.doc.select('//div[@class="exhibition-type__date"]').node()

    date_raw = date_block.text.strip().lower()
    time_block = date_block.xpath('.//br')
    time_raw = ""
    if len(time_block) > 0:
        time_raw = time_block[0].tail.strip()

    # 12 Декабря — 14 Января 2018
    # 21 Октября
    # 17 Октября — 22 Октября 2017
    # 15:00
    # 19:00 — 22:00

    time_pattern = re.compile('(\d\d:\d\d)(\s*—\s*)?(\d\d:\d\d)?')

    match = time_pattern.match(time_raw)

    if match:
        start_hours, start_minutes = match.group(1).split(":")
        start_hours = int(start_hours)
        start_minutes = int(start_minutes)
        end_time = match.group(3)
        if end_time is not None:
            end_hours, end_minutes = end_time.split(":")
            end_hours = int(end_hours)
            end_minutes = int(end_minutes)
        else:
            end_hours, end_minutes = start_hours + 2, start_minutes
            if end_hours > 23:
                end_hours = 23
                end_minutes = 59
    else:
        start_hours, start_minutes = 0, 0
        end_hours, end_minutes = 23, 59

    one_day_pattern = re.compile('(\d{1,2}) ([А-Яа-я]*)\s*(\d{4})?')
    interval_pattern = re.compile('(\d{1,2})\s*([А-Яа-я]*)?\s*[—–]\s*(\d{1,2}) ([А-Яа-я]*)\s*(\d{4})?')
    match = one_day_pattern.match(date_raw)
    interval_match = interval_pattern.match(date_raw)

    if interval_match:
        start_month = interval_match.group(2)
        end_month = month_to_num(interval_match.group(4))
        if start_month:
            start_month = month_to_num(start_month)
        else:
            start_month = end_month

        start_day = int(interval_match.group(1))
        end_day = int(interval_match.group(3))
        end_year = interval_match.group(5)
        if end_year:
            end_year = int(end_year)
        else:
            end_year = datetime.datetime.today().year
        if start_month > end_month:
            start_year = end_year - 1
        else:
            start_year = end_year
        date = datetime.datetime(year=start_year, month=start_month, day=start_day, hour=start_hours,
                                 minute=start_minutes)
        last_date = datetime.datetime(year=end_year, month=end_month, day=end_day, hour=end_hours, minute=end_minutes)
        dates = []
        for day in range((last_date - date).days + 1):
            start_date = date + datetime.timedelta(day)
            end_date = date.replace(hour=end_hours, minute=end_minutes) + datetime.timedelta(day)
            dates.append((start_date, end_date))
    elif match:
        month = int(month_to_num(match.group(2)))
        day = int(match.group(1))
        year = match.group(3)
        if year:
            year = int(year)
        else:
            year = datetime.datetime.today().year
        date = datetime.datetime(year=year, month=month, day=day, hour=start_hours, minute=start_minutes)
        end_date = datetime.datetime(year=year, month=month, day=day, hour=end_hours, minute=end_minutes)
        dates = [(date, end_date)]
    else:
        raise ValueError("Can't parse date " + date_raw)

    description_block = g.doc.select('//div[contains(@class, "exhibition-detail-info__right")]').node()

    def parse_description():
        texts = description_block.xpath('.//p | .//ul')
        desc = ""
        for text_elem in texts:
            desc += BeautifulSoup(tostring(text_elem), "lxml").text
        return desc

    description = parse_description()
    if description is "":
        description_block = g.doc.select(
            '//div[contains(@class, "place-description exhibition-detail__description--archive")]').node()
        description = parse_description()

    map_text = "Москва, 4-й Сыромятнический переулок, 1/8 "

    price = 0

    event_format = g.doc.select('//div[@class="exhibition-type__title"]').node().text
    tags = ["винзавод", event_format]

    background_style = g.doc.select('//div[@class="exhibition-slider-bg exhibition-slider-bg--1"]').node().get("style")
    img_pattern = re.compile(r"url\(([\w\/\-.]*)\)")
    match = img_pattern.search(background_style)
    if match:
        img_url = base_url + match.group(1)
        img, filename = get_img(img_url)
    else:
        img, filename = get_default_img()

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": map_text, "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(),
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def parse_desc_from_gorky_park(url):
    base_url = "http://park-gorkogo.com"
    org_id = 2

    g = get_grab()
    g.go(url)
    print("parse " + url)

    title = g.doc.select('//meta[@property="og:title"]').node().get("content").strip()

    date_block = g.doc.select('//span[@class="_39tx0"]').node()

    datetime_raw = date_block.xpath('.//span')[1].text.strip().lower()

    # 16 декабря – 17 декабря с 12.00 до 15.00
    # 14 декабря с 19.30 до 21.20
    # C 28 ноября
    # 4 августа – 16 февраля с 19.30 до 20.30

    time_pattern = re.compile('(\d\d.\d\d)(\s*до\s*)?(\d\d.\d\d)?')
    match = time_pattern.search(datetime_raw)
    if match:
        start_hours, start_minutes = match.group(1).split(".")
        start_hours = int(start_hours)
        start_minutes = int(start_minutes)
        end_time = match.group(3)
        if end_time is not None:
            end_hours, end_minutes = end_time.split(".")
            end_hours = int(end_hours)
            end_minutes = int(end_minutes)
        else:
            end_hours, end_minutes = start_hours + 2, start_minutes
        if end_hours > 23 or end_hours < start_hours:
            end_hours = 23
            end_minutes = 59

    else:
        start_hours, start_minutes = 0, 0
        end_hours, end_minutes = 23, 59

    one_day_pattern = re.compile('(с\s*)?(\d{1,2}) ([А-Яа-я]*)')
    interval_pattern = re.compile('(\d{1,2})\s*([А-Яа-я]*)\s*[—–]\s*(\d{1,2}) ([А-Яа-я]*)\s*(\d{4})?')
    match = one_day_pattern.match(datetime_raw)
    interval_match = interval_pattern.match(datetime_raw)

    if interval_match:
        start_month = month_to_num(interval_match.group(2))
        end_month = month_to_num(interval_match.group(4))

        start_day = int(interval_match.group(1))
        end_day = int(interval_match.group(3))
        start_year = datetime.datetime.today().year
        if start_month < datetime.datetime.today().month and start_month == 1:
            start_year += 1
            end_year = start_year
        elif start_month > end_month:
            end_year = start_year + 1
        else:
            end_year = start_year
        date = datetime.datetime(year=start_year, month=start_month, day=start_day, hour=start_hours,
                                 minute=start_minutes)
        last_date = datetime.datetime(year=end_year, month=end_month, day=end_day, hour=end_hours, minute=end_minutes)
        dates = []
        for day in range((last_date - date).days + 1):
            start_date = date + datetime.timedelta(day)
            end_date = date.replace(hour=end_hours, minute=end_minutes) + datetime.timedelta(day)
            dates.append((start_date, end_date))
    elif match:
        month = int(month_to_num(match.group(3)))
        day = int(match.group(2))
        year = datetime.datetime.today().year
        if month < datetime.datetime.today().month and month == 1:
            year += 1
        date = datetime.datetime(year=year, month=month, day=day, hour=start_hours, minute=start_minutes)
        end_date = datetime.datetime(year=year, month=month, day=day, hour=end_hours, minute=end_minutes)
        dates = [(date, end_date)]
    else:
        raise ValueError("Can't parse date " + datetime_raw)

    description = ""
    try:
        desc_header = g.doc.select('//p[@class="_1qgkv"]').node()
        description = desc_header.text
    except IndexError:
        pass
    description_block = g.doc.select('//div[@class="_3hm1Z"]').node()

    texts = description_block.xpath('.//p | .//ul')
    for text_elem in texts:
        description += BeautifulSoup(tostring(text_elem), "lxml").text

    map_text = "г. Москва, ул. Крымский Вал 9, м. Парк культуры"

    price = 0

    tags = ["парк горького"]
    keywords = g.doc.select('//meta[@name="keywords"]').node().get("content").strip().split('.')
    for key in keywords:
        if len(keywords) < 5:
            keywords.append(key)

    img_url = g.doc.select('//meta[@itemprop="image"]').node().get("content").strip()
    img, filename = get_img(img_url)

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": map_text, "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(),
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def parse_desc_from_artplay(url):
    base_url = "http://www.artplay.ru"
    org_id = 32

    g = get_grab()
    g.go(url)
    print("parse " + url)

    main = g.doc.select('//div[@id="content"]').node()

    title = main.xpath(".//h1")[0].text.strip()

    datetime_raw = g.doc.select('//strong[@class="date"]').node().text.strip().lower()

    # 16.01-16.01
    # 31.12-02.01

    start_hours, start_minutes = 0, 0
    end_hours, end_minutes = 23, 59

    interval_pattern = re.compile('(\d{1,2}).(\d{1,2})-(\d{1,2}).(\d{1,2})')
    interval_match = interval_pattern.match(datetime_raw)
    if interval_match:
        start_month = int(interval_match.group(2))
        end_month = int(interval_match.group(4))

        start_day = int(interval_match.group(1))
        end_day = int(interval_match.group(3))
        start_year = datetime.datetime.today().year
        if start_month < datetime.datetime.today().month and start_month == 1:
            start_year += 1
            end_year = start_year
        elif start_month > end_month:
            end_year = start_year + 1
        else:
            end_year = start_year
        date = datetime.datetime(year=start_year, month=start_month, day=start_day, hour=start_hours,
                                 minute=start_minutes)
        last_date = datetime.datetime(year=end_year, month=end_month, day=end_day, hour=end_hours, minute=end_minutes)
        dates = []
        for day in range((last_date - date).days + 1):
            start_date = date + datetime.timedelta(day)
            end_date = date.replace(hour=end_hours, minute=end_minutes) + datetime.timedelta(day)
            dates.append((start_date, end_date))
    else:
        raise ValueError("Can't parse date " + datetime_raw)

    description = ""
    try:
        desc_header = g.doc.select('//p[@class="_1qgkv"]').node()
        description = desc_header.text
    except IndexError:
        pass
    description_block = g.doc.select('//div[@class="shops-wrap node"]').node()

    texts = description_block.xpath('.//p | .//ul')
    for text_elem in texts:
        description += BeautifulSoup(tostring(text_elem), "lxml").text

    map_text = "г. Москва, Нижняя Сыромятническая улица, д.10"

    price = 0

    tags = ["artplay"]
    img, filename = get_default_img("artplay.png")

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": map_text, "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(),
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def parse_desc_from_centermars(url):
    base_url = "http://centermars.ru"
    org_id = 114

    g = get_grab()
    g.go(url)
    print("parse " + url)

    main = g.doc.select('//div[@class="b-prj-sgl"]').node()

    title = main.xpath('.//h1[@class="b-prj-sgl__title hyphen"]')[0].text.strip()

    datetime_raw = g.doc.select('//div[@class="b-prj-sgl__date"]').node().text.strip().lower()

    # '30.11.2017 — 01.02.2018'

    start_hours, start_minutes = 12, 00
    end_hours, end_minutes = 22, 00

    interval_pattern = re.compile('(\d{1,2}).(\d{1,2}).(\d{4})\s*[-—]\s*(\d{1,2}).(\d{1,2}).(\d{4})')
    interval_match = interval_pattern.match(datetime_raw)

    one_day_pattern = re.compile('(\d{1,2}).(\d{1,2}).(\d{4})\s*(\d\d):(\d\d)')
    match = one_day_pattern.match(datetime_raw)
    if match:
        month = int(match.group(2))
        day = int(match.group(1))
        year = int(match.group(3))
        hours = int(match.group(4))
        minutes = int(match.group(5))
        date = datetime.datetime(year=year, month=month, day=day, hour=hours,
                                 minute=minutes)
        end_date = date + datetime.timedelta(hours=2)
        dates = [(date, end_date)]
    elif interval_match:
        start_month = int(interval_match.group(2))
        end_month = int(interval_match.group(5))

        start_day = int(interval_match.group(1))
        end_day = int(interval_match.group(4))

        start_year = int(interval_match.group(3))
        end_year = int(interval_match.group(6))
        date = datetime.datetime(year=start_year, month=start_month, day=start_day, hour=start_hours,
                                 minute=start_minutes)
        last_date = datetime.datetime(year=end_year, month=end_month, day=end_day, hour=end_hours, minute=end_minutes)
        dates = []
        for day in range((last_date - date).days + 1):
            start_date = date + datetime.timedelta(day)
            end_date = date.replace(hour=end_hours, minute=end_minutes) + datetime.timedelta(day)
            dates.append((start_date, end_date))
    else:
        raise ValueError("Can't parse date " + datetime_raw)

    description = ""
    description_block = g.doc.select('//div[@class="b-prj-sgl__content content w-container "]').node()

    texts = description_block.xpath('.//p | .//ul')
    for text_elem in texts:
        description += BeautifulSoup(tostring(text_elem), "lxml").text

    map_text = "Москва, Пушкарев переулок, дом 5"

    price = 0

    tag = g.doc.select('//div[@class="b-prj-sgl__category"]').node().text.strip()
    tags = ["Центр МАРС", tag]

    background_style = g.doc.select('//div[@class="b-prj-sgl__img w-container"]').node().get("style")
    img_pattern = re.compile(r"url\(([\w\/\-.]*)\)")
    match = img_pattern.search(background_style)
    if match:
        img_url = base_url + match.group(1)
        img, filename = get_img(img_url)
    else:
        img, filename = get_default_img()

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": map_text, "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(),
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def parse_desc_from_mail(url):
    base_url = "https://corp.mail.ru/"
    org_id = 141

    g = get_grab()
    g.go(url)
    print("parse " + url)

    main = g.doc.select('//div[@class="ev__wrapper"]').node()

    title = main.xpath('.//h1[@class="ev__title1"]')[0].text.strip()

    date_raw = g.doc.select('//div[@class="ev__title3"]').node().text.strip().lower()
    time_raw = main.xpath('//div[@class="ev__title3"]')[1].text.strip().lower()

    # 08 декабря 2017 г., пятница
    # Начало события в 09.00

    time_pattern = re.compile('(\d\d.\d\d)')

    match = time_pattern.search(time_raw)

    if match:
        start_hours, start_minutes = match.group(1).split(".")
        start_hours = int(start_hours)
        start_minutes = int(start_minutes)
        end_hours, end_minutes = start_hours + 2, start_minutes
        if end_hours > 23:
            end_hours = 23
            end_minutes = 59
    else:
        start_hours, start_minutes = 0, 0
        end_hours, end_minutes = 23, 59

    one_day_pattern = re.compile('(\d{1,2})\s*([А-Яа-я]*)\s*(\d{4})')
    match = one_day_pattern.match(date_raw)
    if match:
        month = int(month_to_num(match.group(2)))
        day = int(match.group(1))
        year = int(match.group(3))
        date = datetime.datetime(year=year, month=month, day=day, hour=start_hours, minute=start_minutes)
        end_date = datetime.datetime(year=year, month=month, day=day, hour=end_hours, minute=end_minutes)
        dates = [(date, end_date)]

    description = ""
    description_block = g.doc.select('//div[@class="js-mediator-article"]').node()

    texts = description_block.xpath('.//p | .//ul')
    for text_elem in texts:
        description += BeautifulSoup(tostring(text_elem), "lxml").text

    try:
        map = g.doc.select(
            '//div[contains(@class, "leaflet-map leaflet-standard-map leaflet-container leaflet-retina leaflet-fade-anim") or contains(@class, "leaflet-marker")]').node()
        latitude = map.get('data-latitude')
        longtitude = map.get('data-longitude')

        req = requests.get(
            "https://geocode-maps.yandex.ru/1.x/?geocode={},{}&format=json&results=1".format(longtitude, latitude))
        response = json.loads(req.content.decode('utf-8'))

        map_text = response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"][
            'GeocoderMetaData']["text"]
    except IndexError:
        map_text = "Москва, Ленинградский проспект 39, стр. 79"

    price = 0
    tags = ["Mail.ru"]

    try:
        img_url = g.doc.select('//meta[@property="og:image"]').node().get("content").strip()
        if not img_url.startswith("http") or not img_url.startswith("https"):
            img_url = base_url + img_url
        img, filename = get_img(img_url)
    except IndexError:
        img, filename = get_default_img()

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates), "location": map_text,
           "description": prepare_desc(description), "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(),
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def parse_desc_from_ditelegraph(url):
    base_url = "http://ditelegraph.com"
    org_id = 26

    g = get_grab()
    g.go(url)
    print("parse " + url)

    main = g.doc.select('//div[@class="content"]').node()

    title_block = main.xpath('.//h1')[0]
    title = title_block.xpath('.//span')[0].tail.strip()
    try:
        format_str = title_block.xpath('.//span')[0].text.strip()
        format_str = format_str.replace(":", "")
    except AttributeError:
        format_str = ""

    date_block = main.xpath('.//div[@class="right fly"]')[0]
    date_raw = date_block[0].text.strip()
    time_raw = date_block.xpath('.//span')[0].text.strip()

    # 18 декабря 2017
    # 20:00

    time_pattern = re.compile('(\d\d:\d\d)')

    match = time_pattern.search(time_raw)

    if match:
        start_hours, start_minutes = match.group(1).split(":")
        start_hours = int(start_hours)
        start_minutes = int(start_minutes)
        end_hours, end_minutes = start_hours + 2, start_minutes
        if end_hours > 23:
            end_hours = 23
            end_minutes = 59
    else:
        start_hours, start_minutes = 0, 0
        end_hours, end_minutes = 23, 59

    one_day_pattern = re.compile('(\d{1,2})\s*([А-Яа-я]*)\s*(\d{4})')
    match = one_day_pattern.match(date_raw)
    if match:
        month = int(month_to_num(match.group(2)))
        day = int(match.group(1))
        year = int(match.group(3))
        date = datetime.datetime(year=year, month=month, day=day, hour=start_hours, minute=start_minutes)
        end_date = datetime.datetime(year=year, month=month, day=day, hour=end_hours, minute=end_minutes)
        dates = [(date, end_date)]

    description = ""
    description_block = g.doc.select('//div[@class="left"]').node()

    texts = description_block.xpath('.//p | .//ul')
    for text_elem in texts:
        description += BeautifulSoup(tostring(text_elem), "lxml").text

    map_text = "Москва, ул. Тверская, д.7, 9 подъезд, 5 этаж"

    price = 0
    tags = ["DI Telegraph", format_str]

    try:
        img_url = description_block.xpath(".//img")[0].get("src").strip()
        if not img_url.startswith("http") or not img_url.startswith("https"):
            img_url = base_url + img_url
        img, filename = get_img(img_url)
    except IndexError:
        img, filename = get_default_img()

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates), "location": map_text,
           "description": prepare_desc(description), "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(),
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def __parse_event_desc_from_mamm(url):
    base_url = "http://mamm-mdf.ru"
    org_id = 10

    g = get_grab()
    g.go(url)
    print("parse " + url)

    def get_title():
        main_block = g.doc.select('//div[@class="lBlock1"]').node()
        raw_title = main_block.xpath('.//h2[@class="smallcaps"]')[0]
        return BeautifulSoup(tostring(raw_title), "lxml").text

    def get_tags():
        tag_container = g.doc.select('//div[@class="txt1"]').node()
        tag = tag_container.xpath('.//span')[0].text
        return ["Mamm", tag]

    def get_dates():
        # 03/II 13:00. МАММ.ул. Остоженка, 16
        date_container = g.doc.select('//div[@class="txt1"]').node()
        date_raw = date_container.xpath('.//span')[0].tail.strip()
        if not date_raw:
            date_raw = date_container.xpath('.//span')[1].tail.strip()

        one_day_pattern = re.compile('(\d{1,2})/([IVX]{1,4})\s*(\d{2}):(\d{2})')
        match = one_day_pattern.match(date_raw)
        if match:
            month = int(convert_roman_month(match.group(2)))
            day = int(match.group(1))
            year = datetime.datetime.today().year
            if month < datetime.datetime.today().month and month == 1:
                year += 1
            hours = int(match.group(3))
            minutes = int(match.group(4))
            date = datetime.datetime(year=year, month=month, day=day, hour=hours, minute=minutes)
            end_date = date.replace(hour=date.hour + 2)
            if end_date.hour > date.hour:
                end_date.replace(hour=23, minute=59)

            return [(date, end_date)]
        raise ValueError("Can't parse date " + date_raw)

    def convert_roman_month(month):
        return {
            "I": 1,
            "II": 2,
            "III": 3,
            "IV": 4,
            "V": 5,
            "VI": 6,
            "VII": 7,
            "VIII": 8,
            "IX": 9,
            "X": 10,
            "XI": 11,
            "XII": 12,
        }[month]

    def get_description():
        event_description_block = g.doc.select('//div[@class="lBlock1"]').node()

        texts = event_description_block.xpath('.//big | .//b | .//p[not(ancestor::div/@class = "txt1")]')
        description = ""
        for text_elem in texts:
            if text_elem.text is not None:
                description += BeautifulSoup(tostring(text_elem), "lxml").text
        return description

    place = "ул. Остоженка, 16"

    def get_price():
        try:
            ticket_block = g.doc.select('//div[@id="tiketPayDiv"]').node()
        except IndexError:
            return 0
        price = ticket_block.xpath(".//td")[0].text
        return re.search("\\d+", price).group(0)

    try:
        img_url = g.doc.select('//meta[@property="og:image"]').node().get("content").strip()
        if not img_url.startswith("http") and not img_url.startswith("https"):
            img_url = base_url + img_url
        img, filename = get_img(img_url)
    except IndexError:
        img, filename = get_default_img()

    res = {"organization_id": org_id, "title": get_title(), "dates": prepare_date(get_dates()),
           "description": prepare_desc(get_description()), "location": place, "tags": get_tags(),
           "price": get_price(),
           "detail_info_url": url, "public_at": get_public_date(), "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def __parse_exhibition_desc_from_mamm(url):
    base_url = "http://mamm-mdf.ru"
    org_id = 10

    g = get_grab()
    g.go(url)
    print("parse " + url)

    def get_title():
        main_block = g.doc.select('//div[@class="block1"]').node()
        raw_title = main_block.xpath('.//div[@class="title smallcaps"]')[0]
        return BeautifulSoup(tostring(raw_title), "lxml").text

    def get_tags():
        return ["Mamm", "выставка"]

    def get_dates():
        # 9.02—1.05.2018
        date_container = g.doc.select('//span[@class="dates smallcaps"]').node()
        date_raw = BeautifulSoup(tostring(date_container), "lxml").text
        interval_pattern = re.compile('(\d{1,2}).(\d{1,2}).?(\d{4})?[—–](\d{1,2}).(\d{1,2}).(\d{4})')
        interval_match = interval_pattern.match(date_raw)
        if interval_match:
            start_month = int(interval_match.group(2))
            end_month = int(interval_match.group(5))

            start_day = int(interval_match.group(1))
            end_day = int(interval_match.group(4))
            start_year = interval_match.group(3)
            end_year = int(interval_match.group(6))
            if start_year:
                start_year = int(start_year)
            else:
                start_year = datetime.datetime.today().year

            start_hours, start_minutes = 0, 0
            end_hours, end_minutes = 23, 59
            date = datetime.datetime(year=start_year, month=start_month, day=start_day, hour=start_hours,
                                     minute=start_minutes)
            last_date = datetime.datetime(year=end_year, month=end_month, day=end_day, hour=end_hours,
                                          minute=end_minutes)
            dates = []
            for day in range((last_date - date).days + 1):
                start_date = date + datetime.timedelta(day)
                end_date = date.replace(hour=end_hours, minute=end_minutes) + datetime.timedelta(day)
                dates.append((start_date, end_date))
            return dates
        else:
            raise ValueError("Can't parse date " + date_raw)

    def get_description():
        try:
            event_description_block = g.doc.select('//div[@id="for_press_0"]').node()
        except IndexError:
            return get_title()
        texts = event_description_block.xpath('.//p')
        description = ""
        for text_elem in texts:
            if text_elem.text is not None:
                description += BeautifulSoup(tostring(text_elem), "lxml").text
        return description

    place = "ул. Остоженка, 16"

    price = 0

    try:
        img_url = g.doc.select('//meta[@property="og:image"]').node().get("content").strip()
        if not img_url.startswith("http") and not img_url.startswith("https"):
            img_url = base_url + img_url
        img, filename = get_img(img_url)
    except IndexError:
        img, filename = get_default_img()

    res = {"organization_id": org_id, "title": get_title(), "dates": prepare_date(get_dates()),
           "description": prepare_desc(get_description()), "location": place, "tags": get_tags(),
           "detail_info_url": url, "public_at": get_public_date(), "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def parse_desc_from_mamm(url):
    if "/exhibitions" in url:
        return __parse_exhibition_desc_from_mamm(url)
    else:
        return __parse_event_desc_from_mamm(url)
