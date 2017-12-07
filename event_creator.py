import requests
import event_desc_parser
import json
import parse_logger
import smtplib
import time
import config


def get_email_server():
    if config.SMTP_SERVER == 'smtp.yandex.ru':
        server = smtplib.SMTP_SSL(config.SMTP_SERVER)
    else:
        server = smtplib.SMTP(config.SMTP_SERVER, 25)
    server.login(config.EMAIL_LOGIN, config.EMAIL_PASS)
    return server


def post_to_evendate(event_desc):
    print("posting " + event_desc['detail_info_url'])
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.post("https://evendate.io/api/v1/events/", data=json.dumps(event_desc), headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        evendate_url = "https://evendate.io/event/" + str(json.loads(r.text)["data"]["event_id"])
        print("POSTED " + evendate_url)
        return evendate_url


def __send_email(server, for_url, from_url):
    from_addr = 'Mr. Parser <%s>' % config.EMAIL_LOGIN
    to_addr = 'Mr. Poster <%s>' % config.TRELLO_EMAIL
    subj = 'New event'
    msg_txt = 'Change image for: ' + for_url + " from: " + from_url + ""

    msg = "From: %s\nTo: %s\nSubject: %s\n\n%s" % (from_addr, to_addr, subj, msg_txt)
    server.sendmail(from_addr, to_addr, msg)


def send_email_for_org(server, org, msg_text):
    if msg_text == "":
        return
    from_addr = 'Mr. Parser <%s>' % config.EMAIL_LOGIN
    to_addr = 'Mr. Poster <%s>' % config.TRELLO_EMAIL
    subj = 'New events for ' + org

    msg = "From: %s\nTo: %s\nSubject: %s\n\n%s" % (from_addr, to_addr, subj, msg_text)
    server.sendmail(from_addr, to_addr, msg)


def __process(file_name, processor):
    checked_urls = parse_logger.read_checked_urls(file_name)
    done_urls = parse_logger.read_completed_urls(file_name)
    process_set = checked_urls.difference(done_urls)
    server = get_email_server()

    for url in process_set:
        res_url = post_to_evendate(processor(url))
        if res_url is not None:
            parse_logger.write_url_to_file(parse_logger.events_desc_folders, file_name, url)
            __send_email(server, res_url, url)
        else:
            __send_email(server, "ERROR", url)
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
    server = get_email_server()

    done_list = []
    error_list = []

    for url in process_set:
        res_url = post_to_evendate(processor(url))
        if res_url is not None:
            parse_logger.write_url_to_file(parse_logger.events_desc_folders, file_name, url)
            done_list.append((res_url, url))
        else:
            error_list.append(url)
        time.sleep(10)

    send_email_for_org(server, org, prepare_msg_text(done_list, error_list))
    server.quit()


def process_digital_october():
    __process_bunch("digit_october.txt", "Digital October", event_desc_parser.parse_desc_from_digit_october)


def process_planetarium():
    __process("planetarium.txt", event_desc_parser.parse_desc_from_planetarium)


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
