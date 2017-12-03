from grab import Grab
import datetime
import re
import requests, mimetypes, base64
import event_desc_parser as parser
import time
import parse_logger
import event_creator
from bs4 import BeautifulSoup
from lxml.etree import tostring


def get_grab():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    g = Grab(log_file='out.html', headers=headers)
    g.setup(connect_timeout=60, timeout=60)
    return g


def get_img(url):
    img_raw = requests.get(url, allow_redirects=True)
    content_type = img_raw.headers['content-type']
    extension = mimetypes.guess_extension(content_type)
    if extension == ".jpe":
        extension = ".jpeg"
    img = "data:{};base64,".format(content_type) + base64.b64encode(img_raw.content).decode("utf-8")
    filename = "image" + extension
    return img, filename


def parse_from_cinemapark():
    file_name = "cinemapark.txt"
    do_url = "http://www.cinemapark.ru/"
    base_url = "http://www.cinemapark.ru"
    org_id = 13

    server = event_creator.get_email_server()

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

    done_urls = parse_logger.read_completed_urls(file_name)
    for event in events:
        url = event.xpath('.//a[@class="btn btn-block btn-default" or @class="btn btn-block btn-primary"]')[0].get(
            "href")
        if not url.startswith("http"):
            url = base_url + url
        if url in done_urls:
            continue
        hover_block = event.xpath('.//div[@class="poster-holder"]')[0]
        title = event.xpath('.//div[@class="film-title"]')[0].text.strip()
        # 'Жанр: исторический/фантастика/экш'
        tags = ["синемапарк"]
        format_str = hover_block.xpath('.//br')[1].tail
        formats = format_str.split(":")[1].strip().split("/")
        tags.extend(formats)

        # 'В прокате  с 30 ноября по 13 декабря'
        data_raw = hover_block.xpath('.//br')[3].tail.strip().lower()
        date_pattern = re.compile("с (\d{1,2}) ([А-Яа-я]*) по (\d{1,2}) ([А-Яа-я]*)")
        match = date_pattern.search(data_raw)

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
            # todo
            pass

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

        img, filename = parser.get_img(img_url)
        res = {"organization_id": org_id, "title": title, "dates": parser.prepare_date(dates),
               "description": parser.prepare_desc(description), "location": map_text, "price": price, "tags": tags,
               "detail_info_url": url, "public_at": parser.get_public_date(),
               "image_horizontal": img,
               "filenames": {'horizontal': filename}}

        res_url = event_creator.post_to_evendate(res)
        if res_url is not None:
            parse_logger.write_url_to_file(parse_logger.events_desc_folders, file_name, url)
            done_list.append((res_url, url))
        else:
            error_list.append(url)
        time.sleep(2)

    event_creator.send_email_for_org(server, "Cinemapark (CHANGE IMAGES)",
                                     event_creator.prepare_msg_text(done_list, error_list))
    server.quit()
    print("end check " + do_url)
