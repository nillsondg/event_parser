import requests
import event_desc_parser
import json
import parse_logger
import time
import config


def post_to_evendate(event_desc):
    print("posting " + event_desc['detail_info_url'])
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.post("https://evendate.io/api/v1/events/", data=json.dumps(event_desc), headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        event = json.loads(r.text)["data"]
        evendate_url = format_evendate_event_url(event["event_id"])
        print("POSTED " + evendate_url)
        return evendate_url, event["event_id"]
    else:
        parse_logger.log_posting_error(event_desc['detail_info_url'], r.text)
        return None, None


def format_evendate_event_url(event_id):
    return "https://evendate.io/event/" + str(event_id)


def __process(file_name, processor):
    checked_urls = parse_logger.read_checked_urls(file_name)
    done_urls = parse_logger.read_completed_urls(file_name)
    process_set = checked_urls.difference(done_urls)
    server = parse_logger.get_email_server()

    for url in process_set:
        res_url, event_id = post_to_evendate(processor(url))
        if res_url is not None:
            parse_logger.write_url_to_file(parse_logger.events_desc_folders, file_name, url)
            parse_logger.send_email(server, res_url, url)
        else:
            parse_logger.send_email(server, "ERROR", url)
        parse_logger.write_url_to_file(parse_logger.events_desc_folders, file_name, url)
        time.sleep(10)

    server.quit()


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
    process_set = checked_urls.difference(done_urls)
    server = parse_logger.get_email_server()

    done_list = []
    error_list = []

    for url in process_set:
        try:
            res_url, event_id = post_to_evendate(processor(url))
        except Exception as e:
            error_list.append(url)
            print("ERROR PARSING EVENT ", e)
            continue
        if res_url is not None:
            parse_logger.write_url_to_file(parse_logger.events_desc_folders, file_name, url)
            done_list.append((res_url, url))
        else:
            error_list.append(url)
        time.sleep(10)

    parse_logger.send_email_for_org(server, org, prepare_msg_text(done_list, error_list))
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
