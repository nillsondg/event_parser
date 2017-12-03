from grab import Grab
import datetime
from parse_logger import read_checked_urls

urls_folder = "events/"


def get_grab():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    g = Grab(log_file='out.html', headers=headers)
    g.setup(timeout=60)
    return g


def write_events_to_file(file_name, url_set, exist_url_set):
    f = open(urls_folder + file_name, 'a+')
    for url in url_set:
        if url not in exist_url_set:
            f.write(datetime.datetime.now().strftime("%y.%m.%d|%H:%M:%S ") + url + "\n")
            print("added " + url)
    f.close()


def parse_url_from_digit_october():
    file_name = "digit_october.txt"
    do_url = "http://digitaloctober.ru/ru/events"
    base_url = "http://digitaloctober.ru"

    g = get_grab()
    g.go(do_url)
    print("check " + do_url)
    main = g.doc.select('//div[@class="schedule_page"]').node()
    events = main.xpath('.//a[@href]')

    urls = set()
    for event in events:
        url = event.get("href")
        if not url.startswith("http"):
            url = base_url + url
        urls.add(url)

    exist_urls = read_checked_urls(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + do_url)


def parse_from_strelka():
    file_name = "strelka.txt"
    strelka_url = "http://strelka.com/ru/events"
    base_url = "http://strelka.com"

    g = get_grab()
    g.go(strelka_url)
    print("check " + strelka_url)

    event_blocks = list()
    event_blocks.append(g.doc.select('//div[@class="new_container new_blocks_container"]').node())
    event_blocks.append(g.doc.select('//div[@class="new_container new_cinema_container"]').node())
    event_blocks.append(g.doc.select('//div[@class="new_container new_discussions_container"]').node())
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


def parse_from_planetarium():
    planetarium_url = "http://www.planetarium-moscow.ru/billboard/events/"
    file_name = "planetarium.txt"
    base_url = "http://www.planetarium-moscow.ru"

    g = get_grab()
    g.go(planetarium_url)
    print("check " + planetarium_url)

    main = g.doc.select('//div[@class="leftcolumn"]').node()
    events = main.xpath('.//a[@href and not(@onclick) and not(@onmouseover) and not(@class="orange")]')

    urls = set()
    for event in events:
        url = event.get("href")
        if not url.startswith("http"):
            url = base_url + url
        urls.add(url)

    exist_urls = read_checked_urls(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + planetarium_url)


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


def parse_from_tretyako():
    tretyako_url = "http://www.tretyakovgallery.ru/events/"
    file_name = "tretyako.txt"
    base_url = "http://www.tretyakovgallery.ru"

    g = get_grab()
    g.go(tretyako_url)
    print("check " + tretyako_url)

    main = g.doc.select('//div[@class="events__list events-list"]').node()
    events = main.xpath('.//div[@class="row"]')

    urls = set()
    for event in events:
        url = event.xpath('.//a[@class="event-item__name"]')[0].get("href")
        if not url.startswith("http"):
            url = base_url + url
            urls.add(url)

    exist_urls = read_checked_urls(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + base_url)


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


def parse_url_from_yandex():
    file_name = "yandex.txt"
    do_url = "https://events.yandex.ru"
    base_url = "https://events.yandex.ru"

    g = get_grab()
    g.go(do_url)
    print("check " + do_url)
    main = g.doc.select('//div[contains(@class, "events-calendar__cells")]').node()
    events = main.xpath('.//div[contains(@class, "events-calendar__cell")]')

    urls = set()
    for event in events:
        url = event.xpath('.//a[contains(@class, "action-announce")]')[0].get("href")
        if not url.startswith("https"):
            url = base_url + url
        urls.add(url)

    exist_urls = read_checked_urls(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + do_url)


def parse_all():
    # parse_from_skolkovo()
    parse_from_planetarium()
    parse_from_strelka()
    # parse_from_lumiere()
    parse_url_from_digit_october()
    parse_from_tretyako()
    parse_from_garage()
    parse_url_from_yandex()
