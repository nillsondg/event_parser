import requests
import event_desc_parser
import json
import parse_logger
import smtplib
import time
import config


def __post_to_evendate(event_desc):
    print("posting " + event_desc['detail_info_url'])
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.post("https://evendate.io/api/v1/events/", data=json.dumps(event_desc), headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        return "https://evendate.io/event/" + str(json.loads(r.text)["data"]["event_id"])


def __send_email(server, for_url, from_url):
    from_addr = 'Mr. Parser <%s>' % config.EMAIL_LOGIN
    to_addr = 'Mr. Poster <%s>' % config.TRELLO_EMAIL
    subj = 'New event'
    msg_txt = 'Change image for: ' + for_url + " from: " + from_url + ""

    msg = "From: %s\nTo: %s\nSubject: %s\n\n%s" % (from_addr, to_addr, subj, msg_txt)
    server.sendmail(from_addr, to_addr, msg)


def __process(file_name, processor):
    checked_urls = parse_logger.read_checked_urls(file_name)
    done_urls = parse_logger.read_completed_urls(file_name)
    process_set = checked_urls.difference(done_urls)
    server = smtplib.SMTP_SSL(config.SMTP_SERVER)
    server.login(config.EMAIL_LOGIN, config.EMAIL_PASS)

    for url in process_set:
        res_url = __post_to_evendate(processor(url))
        __send_email(server, res_url, url)
        parse_logger.write_url_to_file(parse_logger.events_desc_folders, file_name, url)
        time.sleep(30)

    server.quit()


def process_digital_october():
    __process("digit_october.txt", event_desc_parser.parse_desc_from_digit_october)


def process_planetarium():
    file_name = "planetarium.txt"
    __process(file_name, event_desc_parser.parse_desc_from_planetarium)


def process_strelka():
    __process("strelka.txt", event_desc_parser.parse_desc_from_strelka)


def process_all():
    process_strelka()
    process_digital_october()
    process_planetarium()
