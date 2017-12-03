from grab import Grab
from lxml.etree import tostring
from bs4 import BeautifulSoup
import datetime
import re
import base64
import requests
import mimetypes


def get_grab():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    g = Grab(log_file='out.html', headers=headers)
    g.setup(timeout=60)
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


def prepare_desc(desc):
    if len(desc) > 2000:
        return desc[:2000]
    return desc


def get_public_date():
    public_date = datetime.datetime.today() \
        .replace(day=datetime.datetime.today().day, hour=14, minute=0, second=0, microsecond=0)
    public_date += datetime.timedelta(days=1)
    return public_date.strftime('%Y-%m-%dT%H:%M:%SZ')


def get_default_img(img_name="evendate.png", ext="png"):
    with open(img_name, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    image_horizontal = "data:image/{};base64,".format(ext) + encoded_string.decode("utf-8")
    return image_horizontal


def get_img(url):
    img_raw = requests.get(url, allow_redirects=True)
    content_type = img_raw.headers['content-type']
    extension = mimetypes.guess_extension(content_type)
    if extension == ".jpe":
        extension = ".jpeg"
    img = "data:{};base64,".format(content_type) + base64.b64encode(img_raw.content).decode("utf-8")
    filename = "image" + extension
    return img, filename


def month_to_num(month):
    return {
        'января': 1,
        'янв': 1,
        'февраля': 2,
        'фев': 2,
        'марта': 3,
        'мар': 3,
        'апреля': 4,
        'апр': 4,
        'мая': 5,
        'май': 5,
        'июня': 6,
        'июн': 6,
        'июля': 7,
        'июл': 7,
        'августа': 8,
        'авг': 8,
        'сентября': 9,
        'сен': 9,
        'октября': 10,
        'окт': 10,
        'ноября': 11,
        'ноя': 11,
        'декабря': 12,
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
           "location": map_text, "price": price, "tags": tags, "detail_info_url": url,
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

    return {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
            "description": prepare_desc(description),
            "location": location, "price": price, "tags": tags, "detail_info_url": url,
            "public_at": get_public_date(), "image_horizontal": get_default_img(img_name="planetarium.png"),
            "filenames": {'horizontal': "image.png"}}


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
        # todo
        pass

    date = datetime.datetime.strptime(datetime_str, "%d %m %Y %H:%M")
    end_date = date + datetime.timedelta(hours=2)
    dates = [(date, end_date)]

    title = event_info_block.xpath('.//h1[@class="header-event__title h1"]')[0].text

    event_description_block = g.doc.select('//section[@class="event-desc"]').node()

    text_desc_block = event_description_block.xpath('.//div[@class="col-sm-7"]')[0]

    try:
        description = text_desc_block.xpath('.//div[@class="event-desc__lid"]')[0].text
    except IndexError:
        description = ""

    texts = text_desc_block.xpath('.//p')
    for text_elem in texts:
        if text_elem.text is not None:
            description += BeautifulSoup(tostring(text_elem), "lxml").text

    place = "Москва, " + g.doc.select('//div[@class="museum__address"]').node().text

    price = 0

    tags = ["Третьяковка", tag]

    try:
        img_url = base_url + g.doc.select('//img[@class="header-event__img"]').node().get('src')
        img, filename = get_img(img_url)
    except IndexError:
        img = get_default_img("tretyako.jpg", "jpg")
        filename = "image.png"

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": place, "price": price, "tags": tags,
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
    many_days_pattern = re.compile('(\d{1,2}) ([А-Яа-я]*) (\d{0,4})\s*–\s*(\d{1,2}) ([А-Яа-я]*) (\d{4})')
    time_pattern = re.compile('(\d\d):(\d\d)–(\d\d):(\d\d)')

    one_day_match = day_pattern.match(date_raw)
    many_days_match = many_days_pattern.match(date_raw)
    time_match = time_pattern.search(time_raw)

    if one_day_match and time_match:
        month = one_day_match.group(2)
        date_str = date_raw.replace(month, str(month_to_num(month)))
        date = datetime.datetime.strptime(date_str + " " + time_match.group(1) + ":" + time_match.group(2),
                                          "%d %m %Y %H:%M")
        end_date = date.replace(day=date.day, hour=int(time_match.group(3)), minute=int(time_match.group(4)))
        return [(date, end_date)]
    elif many_days_match and time_match:
        month1 = many_days_match.group(2)
        month2 = many_days_match.group(5)
        date_str = date_raw.replace(month1, str(month_to_num(month1)))
        date_str = date_str.replace(month2, str(month_to_num(month2)))

        first_day = many_days_match.group(1)
        last_day = many_days_match.group(4)
        year1 = many_days_match.group(3)
        year2 = many_days_match.group(6)
        if year1 == "":
            year1 = year2

        first_date = datetime.datetime.strptime(str(first_day) + " " + str(month_to_num(month1)) + " " + year1,
                                                "%d %m %Y")
        last_date = datetime.datetime.strptime(str(last_day) + " " + str(month_to_num(month2)) + " " + year2,
                                               "%d %m %Y")

        dates = []
        for date in date_range(first_date, last_date + datetime.timedelta(days=1)):
            start_date = date.replace(hour=int(time_match.group(1)), minute=int(time_match.group(2)))
            end_date = date.replace(hour=int(time_match.group(3)), minute=int(time_match.group(4)))
            dates.append((start_date, end_date))

        return dates


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
    time_raw = datetime_block.xpath('.//div')[0].text.lower()

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
        img = get_default_img()
        filename = "image.png"

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": place, "price": price, "tags": tags,
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
        img = get_default_img()
        filename = "image.png"

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": place, "price": price, "tags": tags,
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
    city = header_info_block.xpath('.//div[contains(@class, "event-header__place")]')[0].text.strip()

    # 5 ДЕКАБРЯ, 18:30
    one_day_pattern = re.compile('\d{1,2} ([А-Яа-я]*), \d\d:\d\d')
    match = one_day_pattern.match(datetime_raw)
    if match:
        month = match.group(1)
        date_str = datetime_raw.replace(month, str(month_to_num(month)))

        year = datetime.datetime.today().year
        if month_to_num(month) < datetime.datetime.today().month:
            year += 1

        datetime_str = date_str + " " + str(year)
    else:
        pass
        # todo

    date = datetime.datetime.strptime(datetime_str, "%d %m, %H:%M %Y")
    end_date = date + datetime.timedelta(hours=2)
    dates = [(date, end_date)]

    description_block = g.doc.select('//div[contains(@class, "event-description")]').node()
    texts = description_block.xpath('.//p')
    description = ""
    for text_elem in texts:
        if text_elem.text is not None:
            description += BeautifulSoup(tostring(text_elem), "lxml").text

    map_block = g.doc.select('//div[@class="event-place__place-title"]').node()
    map_text = city + ", " + map_block.text

    price = 0

    tags = []
    keywords = g.doc.select('//meta[@name="keywords"]').node().get("content").strip().split(',')
    for key in keywords:
        if len(tags) < 5:
            tags.append(key)

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": map_text, "price": price, "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(),
           "image_horizontal": get_default_img("yandex.jpg", "jpg"),
           "filenames": {'horizontal': "image.png"}}
    return res


def parse_desc_from_flacon(url):
    base_url = "http://flacon.ru"
    org_id = 31

    g = get_grab()
    g.go(url)
    print("parse " + url)

    title = g.doc.select('//meta[@property="og:title"]').node().get("content").strip()

    header_info_block = g.doc.select('//section[@class="preview-section_wrap"]').node()

    date_raw = header_info_block.xpath('.//div[@class="date"]')[0].text.strip().lower()
    time_raw = header_info_block.xpath('.//div[@class="date"]')[0].xpath('.//br')[0].tail.strip()

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
        end_hours, end_minutes = 0, 0

    one_day_pattern = re.compile('(\d{1,2}) ([А-Яа-я]*) (\d{4})')
    interval_pattern = re.compile('(\d{1,2})\s*([А-Яа-я]*)?\s*[—–]\s*(\d{1,2}) ([А-Яа-я]*) (\d{4})')
    match = one_day_pattern.match(date_raw)
    interval_match = interval_pattern.match(date_raw)
    if match:
        month = int(month_to_num(match.group(2)))
        day = int(match.group(1))
        year = int(match.group(3))
        date = datetime.datetime(year=year, month=month, day=day, hour=start_hours, minute=start_minutes)
        end_date = datetime.datetime(year=year, month=month, day=day, hour=end_hours, minute=end_minutes)
        dates = [(date, end_date)]
    elif interval_match:
        start_month = interval_match.group(2)
        end_month = month_to_num(interval_match.group(4))
        if start_month:
            start_month = month_to_num(start_month)
        else:
            start_month = end_month

        start_day = int(interval_match.group(1))
        end_day = int(interval_match.group(3))
        start_year = int(interval_match.group(5))
        end_year = int(interval_match.group(5))
        date = datetime.datetime(year=start_year, month=start_month, day=start_day, hour=start_hours,
                                 minute=start_minutes)
        last_date = datetime.datetime(year=end_year, month=end_month, day=end_day, hour=end_hours, minute=end_minutes)
        dates = []
        for day in range(start_day, end_day + 1):
            start_date = date + datetime.timedelta(day)
            end_date = last_date + datetime.timedelta(day)
            dates.append((start_date, end_date))
    else:
        # todo
        pass

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
        img = get_default_img()
        filename = "image.png"

    res = {"organization_id": org_id, "title": title, "dates": prepare_date(dates),
           "description": prepare_desc(description), "location": map_text, "price": price, "tags": tags,
           "detail_info_url": url, "public_at": get_public_date(),
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res
