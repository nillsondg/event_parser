from grab import Grab
import datetime
import re
import requests, base64
import event_desc_parser as parser
import time
import parse_logger
import evendate_api
import event_creator
from bs4 import BeautifulSoup
from lxml.etree import tostring
import tmdbsimple as tmdb
import config
from utils import crop_img_to_16x9, get_img
from file_keeper import write_completed_url, read_completed_urls, read_ignored_urls
from parse_logger import log_catalog_error, log_event_parsing_error


def get_grab():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    g = Grab(log_file='out.html', headers=headers)
    g.setup(connect_timeout=60, timeout=60)
    return g


def find_img_in_tmdb(title):
    tmdb.API_KEY = config.TMDB_KEY
    search = tmdb.Search()
    response = search.movie(query=title)
    try:
        movie = search.results[0]
    except IndexError:
        return None, None
    if movie['poster_path'] is None:
        return None, None
    return prepare_cropped_img(crop_img_to_16x9(load_img(get_tmdb_img_url(movie['poster_path']))), "png")


def get_tmdb_img_url(path):
    return "http://image.tmdb.org/t/p/w1280" + path


def load_img(url):
    res = requests.get(url, allow_redirects=True)
    return res.content


def prepare_cropped_img(img, extension):
    img = "data:{};base64,".format(extension) + base64.b64encode(img).decode("utf-8")
    filename = "image." + extension
    return img, filename


def parse_from_cinemapark():
    try:
        __parse_from_cinemapark()
    except Exception as e:
        log_catalog_error("cinemapark.txt", e)


def __parse_from_cinemapark():
    file_name = "cinemapark.txt"
    do_url = "http://www.cinemapark.ru/"
    base_url = "http://www.cinemapark.ru"
    org_id = 13

    done_list = []
    error_list = []

    g = get_grab()
    g.go(do_url)
    print("check " + do_url)
    main = g.doc.select('//div[contains(@class, "films-box")]').node()

    # data-category 1 — now films
    # data-category 2 — future films
    # note when you select 2 a hover_block can change it's structure (there is not first text with film type)
    events = main.xpath('.//div[contains(@class, "afisha-item afisha-film") and @data-category="1"]')

    done_urls = read_completed_urls(file_name)
    ignored_urls = read_ignored_urls()
    skip_set = set(done_urls).union(set(ignored_urls))
    for event in events:
        url = event.xpath('.//a[@class="btn btn-block btn-default" or @class="btn btn-block btn-primary"]')[0].get(
            "href")
        if not url.startswith("http"):
            url = base_url + url

        if url in skip_set:
            continue
        print("preparing " + url)
        hover_block = event.xpath('.//div[@class="poster-holder"]')[0]
        title = event.xpath('.//div[@class="film-title"]')[0].text.strip()
        # 'Жанр: исторический/фантастика/экш'
        tags = ["синемапарк"]
        format_str = hover_block.xpath('.//br')[1].tail
        formats = format_str.split(":")[1].strip().split("/")
        tags.extend(formats)

        # 'В прокате  с 30 ноября по 13 декабря'
        date_raw = hover_block.xpath('.//br')[3].tail.strip().lower()
        date_pattern = re.compile("с (\d{1,2}) ([А-Яа-я]*) по (\d{1,2}) ([А-Яа-я]*)")
        match = date_pattern.search(date_raw)

        if match:
            start_day = int(match.group(1))
            start_month = parser.month_to_num(match.group(2))
            start_year = datetime.datetime.today().year
            end_day = int(match.group(3))
            end_month = parser.month_to_num(match.group(4))
            end_year = start_year
            if end_month < start_month:
                end_year = start_year + 1
            date = datetime.datetime(year=start_year, month=start_month, day=start_day, hour=0, minute=0)
            last_date = datetime.datetime(year=end_year, month=end_month, day=end_day)
            dates = []
            for day in range((last_date - date).days + 1):
                start_date = date + datetime.timedelta(day)
                end_date = date.replace(hour=23, minute=59) + datetime.timedelta(day)
                dates.append((start_date, end_date))
        else:
            # raise ValueError("Can't parse date " + date_raw)
            print("Can't parse date " + date_raw)
            parse_logger.log_event_parsing_error(url, "Can't parse date " + date_raw)
            continue

        def get_description(film_url):
            time.sleep(5)
            g = get_grab()
            g.go(film_url)
            desc_block = g.doc.select('//div[@class="film-block__text__description"]').node()

            desc = ""
            for text_elem in desc_block.xpath('.//p'):
                text = BeautifulSoup(tostring(text_elem), "lxml").text
                if text != "\n\n":
                    desc += text
            return desc

        description = get_description(url)
        if description == "":
            description = "Описание"
        map_text = "Москва"
        price = 0
        img_url = hover_block.xpath('.//img[@class="poster-image"]')[0].get("src")

        img, filename = find_img_in_tmdb(title)
        if img is None:
            img, filename = get_img(img_url)

        res = {"organization_id": org_id, "title": title, "dates": parser.prepare_date(dates),
               "description": parser.prepare_desc(description), "location": map_text, "price": price, "tags": tags,
               "detail_info_url": url, "public_at": parser.get_public_date(),
               "image_horizontal": img,
               "filenames": {'horizontal': filename}}

        res_url, event_id = evendate_api.post_event_to_evendate(res)
        if res_url is not None:
            write_completed_url(file_name, url)
            done_list.append((res_url, url))
        else:
            error_list.append(url)
        time.sleep(1)

    server = parse_logger.get_email_server()
    msg_header = event_creator.prepare_msg_header("Cinemapark", done_list, error_list)
    parse_logger.send_email(server, msg_header, event_creator.prepare_msg_text(done_list, error_list))
    server.close()
    print("end check " + do_url)


def parse_from_embjapan():
    file_name = "embjapan.txt"
    base_url = "http://www.ru.emb-japan.go.jp"
    xml_url = "http://www.ru.emb-japan.go.jp/japan2018/xml/event-ru.xml"
    import urllib.request
    import xmltodict
    from event_desc_parser import parse_desc_from_embjapan

    done_list = []
    error_list = []

    done_urls = read_completed_urls(file_name)
    ignored_urls = read_ignored_urls()
    skip_set = set(done_urls).union(set(ignored_urls))
    try:
        file = urllib.request.urlopen(xml_url)
        data = file.read()
        file.close()

        data = xmltodict.parse(data)

    except Exception as e:
        log_catalog_error(file_name, e)
        return
    for event in data["catalog"]["event"]:
        url = event["url"]
        if event["area"] != "Москва":
            continue
        if url == "#":
            continue
        if not url.startswith("http"):
            url = base_url + url
        if url.find("www.ru.emb-japan.go.jp") == -1:
            continue
        if url in skip_set:
            continue
        try:
            desc = parse_desc_from_embjapan(url, event)
        except Exception as e:
            log_event_parsing_error(url, e)
            continue

        res_url, event_id = evendate_api.post_event_to_evendate(desc)
        if res_url is not None:
            write_completed_url(file_name, url)
            done_list.append((res_url, url))
        else:
            error_list.append(url)
        time.sleep(1)

    server = parse_logger.get_email_server()
    msg_header = event_creator.prepare_msg_header("Japan Year in Russia", done_list, error_list)
    parse_logger.send_email(server, msg_header, event_creator.prepare_msg_text(done_list, error_list))
    server.close()
    print("end check " + xml_url)
