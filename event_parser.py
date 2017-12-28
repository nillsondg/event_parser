from grab import Grab
import datetime
from parse_logger import read_checked_urls
from parse_logger import log_catalog_error as log_error

urls_folder = "events/"


def get_grab():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    g = Grab(log_file='out.html', headers=headers)
    g.setup(connect_timeout=60, timeout=60)
    return g


def write_events_to_file(file_name, url_set, exist_url_set):
    f = open(urls_folder + file_name, 'a+')
    for url in url_set:
        if url not in exist_url_set:
            f.write(datetime.datetime.now().strftime("%y.%m.%d|%H:%M:%S ") + url + "\n")
            print("added " + url)
    f.close()


def parse_from_skolkovo():
    skolkovo_url = "https://school.skolkovo.ru/static/201412_rss_reader/index_banners_fullview_2016.php?lang=ru"
    file_name = "skolkovo.txt"
    base_url = ""

    g = get_grab()
    g.go(skolkovo_url)
    print("check " + skolkovo_url)

    events = g.xpath_list('.//a[@class="btn btn-large btn-info"]')

    urls = set()
    for event in events:
        url = event.get("href")
        if url.startswith("//"):
            url = "https:" + url
        urls.add(url)

    exist_urls = read_checked_urls(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + skolkovo_url)


# парсить евенты по ссылкам
def parse_from_lumiere():
    lumiere_url = "http://www.lumiere.ru/events/"
    file_name = "lumiere.txt"
    base_url = "http://www.lumiere.ru"

    g = get_grab()
    g.go(lumiere_url)
    print("check " + lumiere_url)

    main = g.doc.select('//div[@id="expo_wide"]').node()
    events = main.xpath('.//a[@href]')

    urls = set()
    for event in events:
        url = event.get("href")
        if not url.startswith("http"):
            url = base_url + url
        urls.add(url)

    exist_urls = read_checked_urls(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + lumiere_url)


def parse_from_garage():
    garage_url = "https://garagemca.org/ru/calendar"
    file_name = "garage.txt"
    base_url = "https://garagemca.org"

    g = get_grab()
    g.go(garage_url)
    print("check " + garage_url)

    main = g.doc.select('//div[@class="calendar-events__container"]').node()
    events = main.xpath('.//div[@class="calendar-event"]')
    main_exb = g.doc.select('//div[@class="calendar-exhibitions"]').node()
    exhibitions = main_exb.xpath('.//div[@class="calendar-event is-white"]')

    urls = set()
    for event in events:
        url = event.xpath('.//a[@class="calendar-event__image"]')[0].get("href")
        if not url.startswith("https"):
            url = base_url + url
        urls.add(url)
    for exhibition in exhibitions:
        url = exhibition.xpath('.//a[contains(@class, "calendar-event__image")]')[0].get("href")
        if not url.startswith("https"):
            url = base_url + url
        urls.add(url)

    exist_urls = read_checked_urls(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + base_url)


def parse_from_strelka():
    file_name = "strelka.txt"
    strelka_url = "http://strelka.com/ru/events"
    base_url = "http://strelka.com"

    g = get_grab()
    g.go(strelka_url)
    print("check " + strelka_url)

    event_blocks = list()
    event_blocks.append(g.doc.select('//div[@class="new_container new_blocks_container"]').node())

    try:
        event_blocks.append(g.doc.select('//div[@class="new_container new_cinema_container"]').node())
    except IndexError:
        pass
    try:
        event_blocks.append(g.doc.select('//div[@class="new_container new_discussions_container"]').node())
    except IndexError:
        pass
    try:
        event_blocks.append(g.doc.select('//div[@class="new_container new_yellow_container"]').node())
    except IndexError:
        pass

    urls = set()
    for event_block in event_blocks:
        events = event_block.xpath('.//a[@href and @class!="new_summer_button_all"]')
        for event in events:
            url = event.get("href")
            if not url.startswith("http"):
                url = base_url + url
            urls.add(url)

    exist_urls = read_checked_urls(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + strelka_url)


def parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter):
    g = get_grab()
    g.go(do_url)
    print("check " + do_url)

    try:
        main = g.doc.select(main_pattern).node()
        events = main.xpath(events_pattern)

        urls = set()
        for event in events:
            url = url_getter(event)
            if url is None:
                continue
            if not url.startswith("http") and not url.startswith("https"):
                url = base_url + url
            urls.add(url)

        exist_urls = read_checked_urls(file_name=file_name)
        write_events_to_file(file_name, urls, exist_urls)

    except Exception as e:
        log_error(file_name, e)
    print("end check " + do_url)


def parse_from_digit_october():
    file_name = "digit_october.txt"
    do_url = "http://digitaloctober.ru/ru/events"
    base_url = "http://digitaloctober.ru"

    main_pattern = '//div[@class="schedule_page"]'
    events_pattern = './/a[@href]'

    def url_getter(event):
        url = event.get("href")
        if not url.startswith("/") or not url.startswith(base_url):
            return None
        return url

    parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


def parse_from_planetarium():
    do_url = "http://www.planetarium-moscow.ru/billboard/events/"
    file_name = "planetarium.txt"
    base_url = "http://www.planetarium-moscow.ru"

    main_pattern = '//div[@class="leftcolumn"]'
    events_pattern = './/a[@href and not(@onclick) and not(@onmouseover) and not(@class="orange")]'

    def url_getter(event):
        url = event.get("href")
        if "/billboard/today/" in url:
            url = url.replace("/today/", "/events/")
        return url

    parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


def parse_from_tretyako():
    do_url = "http://www.tretyakovgallery.ru/events/"
    file_name = "tretyako.txt"
    base_url = "http://www.tretyakovgallery.ru"

    main_pattern = '//div[@class="events__list events-list"]'
    events_pattern = './/div[@class="row"]'

    def url_getter(event):
        return event.xpath('.//a[@class="event-item__name"]')[0].get("href")

    parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


def parse_from_yandex():
    file_name = "yandex.txt"
    do_url = "https://events.yandex.ru"
    base_url = "https://events.yandex.ru"

    main_pattern = '//div[contains(@class, "events-calendar__cells")]'
    events_pattern = './/div[contains(@class, "events-calendar__cell")]'

    def url_getter(event):
        url_block = event.xpath('.//a[contains(@class, "action-announce") '
                                'and contains(@class, "action-announce_type_future")]')
        if len(url_block) == 0:
            return None
        return url_block[0].get("href")

    parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


def parse_from_flacon():
    file_name = "flacon.txt"
    do_url = "http://flacon.ru/afisha/"
    base_url = "http://flacon.ru"

    main_pattern = '//div[contains(@class, "album-block_wrap")]'
    events_pattern = './/div[contains(@class, "album-item")]'

    def url_getter(event):
        return event.xpath('.//a')[0].get("href")

    parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


def parse_from_vinzavod():
    file_name = "vinzavod.txt"
    do_url = "http://www.winzavod.ru/calendar/"
    base_url = "http://www.winzavod.ru"

    main_pattern = '//div[contains(@class, "main-inner")]'
    events_pattern = './/a[contains(@class, "item small")]'

    def url_getter(event):
        return event.get("href")

    parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


def parse_from_gorky_park():
    file_name = "gorky_park.txt"
    do_url = "http://park-gorkogo.com/events"
    base_url = "http://park-gorkogo.com"

    main_pattern = '//section[contains(@class, "Pdxih")]'
    events_pattern = './/section[contains(@class, "_1ExJg")]'

    def url_getter(event):
        return event.xpath('.//a[@class="_1fusP"]')[0].get("href")

    parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


def parse_from_artplay():
    file_name = "artplay.txt"
    do_url = "http://www.artplay.ru/events/all"
    base_url = "http://www.artplay.ru"

    main_pattern = '//ul[@class="cat-inside"]'
    events_pattern = './/li'

    def url_getter(event):
        return event.xpath('.//a')[0].get("href")

    parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


def parse_from_center_mars():
    file_name = "centermars.txt"
    do_url = "http://centermars.ru/projects/"
    base_url = "http://centermars.ru"
    main_pattern = '//div[@id="paginated_list"]'
    events_pattern = './/a[@class="show-itm"]'

    def url_getter(event):
        return event.get('href')

    parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


def parse_from_mail():
    file_name = "mail.txt"
    do_url = "https://corp.mail.ru/ru/press/events/"
    base_url = "https://corp.mail.ru"
    main_pattern = '//ul[@class="ev__row ev__tiles"]'
    events_pattern = './/li[@class="ev__col-4 ev__etype1"]'

    def url_getter(event):
        return event.xpath('.//a[@class="ev__tile_title"]')[0].get('href')

    parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


def parse_from_ditelegraph():
    file_name = "ditelegraph.txt"
    do_url = "http://ditelegraph.com"
    base_url = "http://ditelegraph.com"
    main_pattern = '//div[@class="posts current_posts"]'
    events_pattern = './/article'

    def url_getter(event):
        return event.xpath('.//a[@class="img"]')[0].get('href')

    parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


# def parse_from_vishka():
#     file_name = "vishka.txt"
#     do_url = "https://www.hse.ru/news/announcements"
#     base_url = "https://www.hse.ru"
#     main_pattern = '//div[@class="content__inner"]'
#     events_pattern = './/div[@class="b-events__item js-events-item" and not(contains(@data-filter, "private"))]'
#
#     def url_getter(event):
#         return event.xpath('.//a')[0].get('href')
#
#     parse_from_site(file_name, do_url, base_url, main_pattern, events_pattern, url_getter)


def parse_all():
    try:
        parse_from_strelka()
    except Exception as e:
        log_error("strelka", e)
    try:
        parse_from_garage()
    except Exception as e:
        log_error("garage", e)

    parse_from_planetarium()
    parse_from_digit_october()
    parse_from_tretyako()
    parse_from_yandex()
    parse_from_flacon()
    parse_from_vinzavod()
    parse_from_gorky_park()
    parse_from_artplay()
    parse_from_center_mars()
    parse_from_mail()
    parse_from_ditelegraph()
