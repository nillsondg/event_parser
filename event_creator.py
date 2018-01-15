import event_desc_parser
import parse_logger
import time
from evendate_api import post_to_evendate


def prepare_msg_header(org, done_list, all_list):
    return "New events for {} +{}/-{}".format(org, len(done_list), len(all_list))


def prepare_msg_text(done_list, error_list):
    text = ""
    for res_url, url in done_list:
        text += "ADDED " + res_url + "\r\n"
    for url in error_list:
        text += "ERROR " + url + "\r\n"
    return text


def __process_bunch(file_name, org, processor):
    checked_urls = parse_logger.read_checked_urls(file_name)
    done_urls = parse_logger.read_completed_urls(file_name)
    ignored_urls = parse_logger.read_ignored_urls()
    process_set = checked_urls.difference(done_urls)

    done_list = []
    error_list = []

    for url in set(process_set) - set(ignored_urls):
        try:
            res_url, event_id = post_to_evendate(processor(url))
        except Exception as e:
            error_list.append(url)
            parse_logger.log_event_parsing_error(url, e)
            continue
        if res_url is not None:
            parse_logger.write_url_to_file(parse_logger.events_desc_folder, file_name, url)
            done_list.append((res_url, url))
        else:
            error_list.append(url)
        time.sleep(10)

    server = parse_logger.get_email_server()
    msg_header = prepare_msg_header(org, done_list, process_set)
    parse_logger.send_email_for_org(server, msg_header, prepare_msg_text(done_list, error_list))
    server.quit()


def process_digital_october():
    __process_bunch("digit_october.txt", "Digital October", event_desc_parser.parse_desc_from_digit_october)


def process_planetarium():
    __process_bunch("planetarium.txt", "Planetarium (CHANGE DATES)", event_desc_parser.parse_desc_from_planetarium)


def process_strelka():
    __process_bunch("strelka.txt", "Strelka", event_desc_parser.parse_desc_from_strelka)


def process_tretyako():
    __process_bunch("tretyako.txt", "Tretyakovskay gallery", event_desc_parser.parse_desc_from_tretyako)


def process_garage():
    __process_bunch("garage.txt", "Garage", event_desc_parser.parse_desc_from_garage)


def process_yandex():
    __process_bunch("yandex.txt", "Yandex", event_desc_parser.parse_desc_from_yandex)


def process_flacon():
    __process_bunch("flacon.txt", "Flacon", event_desc_parser.parse_desc_from_flacon)


def process_vinzavod():
    __process_bunch("vinzavod.txt", "Winzavod", event_desc_parser.parse_desc_from_vinzavod)


def process_gorky_park():
    __process_bunch("gorky_park.txt", "Gorky park", event_desc_parser.parse_desc_from_gorky_park)


def process_artplay():
    __process_bunch("artplay.txt", "Artplay", event_desc_parser.parse_desc_from_artplay)


def process_centermars():
    __process_bunch("centermars.txt", "Center Mars", event_desc_parser.parse_desc_from_centermars)


def process_mail():
    __process_bunch("mail.txt", "Mail.ru", event_desc_parser.parse_desc_from_mail)


def process_ditelegraph():
    __process_bunch("ditelegraph.txt", "DI Telegraph", event_desc_parser.parse_desc_from_ditelegraph)


def process_all():
    process_strelka()
    process_digital_october()
    process_planetarium()
    process_tretyako()
    process_garage()
    process_yandex()
    process_flacon()
    process_vinzavod()
    process_gorky_park()
    process_artplay()
    process_centermars()
    process_mail()
    process_ditelegraph()


process_strelka()
