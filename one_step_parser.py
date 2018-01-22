from grab import Grab
import datetime
import re
import requests, mimetypes, base64
import event_desc_parser as parser
import time
import parse_logger
import evendate_api
import event_creator
from bs4 import BeautifulSoup
from lxml.etree import tostring
import tmdbsimple as tmdb
import config


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
    img = "data:{};base64,".format(content_type) + base64.b64encode(crop_img(img_raw.content)).decode("utf-8")
    filename = "image" + extension
    return img, filename


def find_img_in_tmdb(title):
    tmdb.API_KEY = config.TMDB_KEY
    search = tmdb.Search()
    response = search.movie(query=title)
    try:
        movie = search.results[0]
    except KeyError:
        return None
    return prepare_cropped_img(crop_img(load_img(get_tmdb_img_url(movie['poster_path']))), "png")


def get_tmdb_img_url(path):
    return "http://image.tmdb.org/t/p/w1280" + path


def load_img(url):
    img_raw = requests.get(url, allow_redirects=True)
    return img_raw.content


def crop_img(img_raw):
    from PIL import Image
    from io import BytesIO
    image = Image.open(BytesIO(img_raw))
    width = image.size[0]
    height = image.size[1]

    aspect = width / float(height)

    ideal_width = 1280
    ideal_height = 720

    ideal_aspect = ideal_width / float(ideal_height)

    if aspect > ideal_aspect:
        # Then crop the left and right edges:
        new_width = int(ideal_aspect * height)
        offset = (width - new_width) / 2
        resize = (offset, 0, width - offset, height)
    else:
        # ... crop the top and bottom:
        new_height = int(width / ideal_aspect)
        offset = (height - new_height) / 2
        resize = (0, offset, width, height - offset)

    thumb = image.crop(resize).resize((ideal_width, ideal_height), Image.ANTIALIAS)
    img_crop_raw = BytesIO()
    thumb.save(img_crop_raw, format='PNG')
    return img_crop_raw.getvalue()


def prepare_cropped_img(img, extension):
    img = "data:{};base64,".format(extension) + base64.b64encode(img).decode("utf-8")
    filename = "image." + extension
    return img, filename


def parse_from_cinemapark():
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

    done_urls = parse_logger.read_completed_urls(file_name)
    ignored_urls = parse_logger.read_ignored_urls()
    skip_set = set(done_urls).union(set(ignored_urls))
    for event in events:
        url = event.xpath('.//a[@class="btn btn-block btn-default" or @class="btn btn-block btn-primary"]')[0].get(
            "href")
        if not url.startswith("http"):
            url = base_url + url

        if url in skip_set:
            continue
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
            raise ValueError("Can't parse date " + date_raw)

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

        res_url, event_id = evendate_api.post_to_evendate(res)
        if res_url is not None:
            parse_logger.write_url_to_file(parse_logger.events_desc_folder, file_name, url)
            done_list.append((res_url, url))
        else:
            error_list.append(url)
        time.sleep(2)

    server = parse_logger.get_email_server()
    msg_header = event_creator.prepare_msg_header("Cinemapark", done_list, error_list)
    parse_logger.send_email(server, msg_header, event_creator.prepare_msg_text(done_list, error_list))
    server.close()
    print("end check " + do_url)
