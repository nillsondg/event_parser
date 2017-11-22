import requests
import event_desc_parser
import json
import parse_logger
import smtplib
import time
import config


def post_to_evendate(event_desc):
    print("posting " + event_desc['detail_info_url'])
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.post("https://evendate.io/api/v1/events/", data=json.dumps(event_desc), headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        return "https://evendate.io/event/" + str(json.loads(r.text)["data"]["event_id"])


def process_digital_october():
    file_name = "digit_october.txt"
    checked_urls = parse_logger.read_checked_urls(file_name)
    done_urls = parse_logger.read_completed_urls(file_name)

    process_set = checked_urls.difference(done_urls)

    server = smtplib.SMTP_SSL(config.SMTP_SERVER)
    server.login(config.EMAIL_LOGIN, config.EMAIL_PASS)

    for url in process_set:
        res_url = post_to_evendate(event_desc_parser.parse_desc_from_digit_october(url))
        send_email(server, res_url, url)
        parse_logger.write_url_to_file(parse_logger.events_desc_folders, file_name, url)
        time.sleep(30)

    server.quit()


def process_planetarium():
    file_name = "planetarium.txt"
    checked_urls = parse_logger.read_checked_urls(file_name)
    done_urls = parse_logger.read_completed_urls(file_name)
    process_set = checked_urls.difference(done_urls)
    server = smtplib.SMTP_SSL(config.SMTP_SERVER)
    server.login(config.EMAIL_LOGIN, config.EMAIL_PASS)

    for url in process_set:
        res_url = post_to_evendate(event_desc_parser.parse_desc_from_planetarium(url))
        send_email(server, res_url, url)
        parse_logger.write_url_to_file(parse_logger.events_desc_folders, file_name, url)
        time.sleep(30)

    server.quit()


def send_email(server, for_url, from_url):
    from_addr = 'Mr. Parser <%s>' % config.EMAIL_LOGIN
    to_addr = 'Mr. Poster <%s>' % config.TRELLO_EMAIL
    subj = 'New event'
    msg_txt = 'Change image for: ' + for_url + " from: " + from_url + ""

    msg = "From: %s\nTo: %s\nSubject: %s\n\n%s" % (from_addr, to_addr, subj, msg_txt)
    server.sendmail(from_addr, to_addr, msg)
