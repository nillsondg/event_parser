# import requests
from grab import Grab
import datetime

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
}

urls_folder = "events/"


def read_events_from_file(file_name):
    exist_urls = set()
    try:
        with open(urls_folder + file_name) as f:
            for line in f:
                exist_urls.add(line.strip().split(' ')[1])
    except IOError:
        pass
    return exist_urls


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

    g = Grab()
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

    exist_urls = read_events_from_file(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + do_url)


def parse_from_strelka():
    file_name = "strelka.txt"
    strelka_url = "http://strelka.com/ru/events"
    base_url = "http://strelka.com"

    g = Grab()
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

    exist_urls = read_events_from_file(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + strelka_url)


def parse_from_planetarium():
    planetarium_url = "http://www.planetarium-moscow.ru/billboard/events/"
    file_name = "planetarium.txt"
    base_url = "http://www.planetarium-moscow.ru"

    g = Grab(log_file='out.html', headers=headers)
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

    exist_urls = read_events_from_file(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + planetarium_url)


def parse_from_skolkovo():
    skolkovo_url = "https://school.skolkovo.ru/static/201412_rss_reader/index_banners_fullview_2016.php?lang=ru"
    file_name = "skolkovo.txt"
    base_url = ""

    g = Grab(log_file='out.html', headers=headers)
    g.go(skolkovo_url)
    print("check " + skolkovo_url)

    events = g.xpath_list('.//a[@class="btn btn-large btn-info"]')

    urls = set()
    for event in events:
        url = event.get("href")
        if url.startswith("//"):
            url = "https:" + url
            urls.add(url)
        else:
            urls.add(url)

    exist_urls = read_events_from_file(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + skolkovo_url)


# парсить евенты по ссылкам
def parse_from_lumiere():
    lumiere_url = "http://www.lumiere.ru/events/"
    file_name = "lumiere.txt"
    base_url = "http://www.lumiere.ru"

    g = Grab(headers=headers)
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

    exist_urls = read_events_from_file(file_name=file_name)
    write_events_to_file(file_name, urls, exist_urls)
    print("end check " + lumiere_url)


def parse_all():
    parse_from_skolkovo()
    parse_from_planetarium()
    parse_from_strelka()
    parse_from_lumiere()
    parse_url_from_digit_october()
