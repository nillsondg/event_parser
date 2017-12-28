import datetime
import smtplib
import config

events_folder = "events/"
events_desc_folders = "events_desc/"


def __read_events_from_file(folder, file_name):
    exist_urls = set()
    try:
        with open(folder + file_name) as f:
            for line in f:
                exist_urls.add(line.strip().split(' ')[1])
    except IOError:
        pass
    return exist_urls


def write_url_to_file(folder, file_name, url):
    f = open(folder + file_name, 'a+')
    f.write(datetime.datetime.now().strftime("%y.%m.%d|%H:%M:%S ") + url + "\n")
    f.close()


def read_completed_urls(file_name):
    return __read_events_from_file(events_desc_folders, file_name)


def read_checked_urls(file_name):
    return __read_events_from_file(events_folder, file_name)


def log_catalog_error(org, e):
    print("ERROR PARSING CATALOG", e)
    fast_send_email(org, "ERROR PARSING CATALOG " + str(e))


def log_event_error(org, e):
    print("ERROR PARSING EVENT", e)
    fast_send_email(org, "ERROR PARSING EVENT " + str(e))


def log_posting_error(url, error_text):
    print("ERROR POSTING EVENT", error_text)
    fast_send_email(url, "ERROR POSTING EVENT " + error_text)


def log_loading_mincult_error(place_id, e):
    print("ERROR LOADING MINCULT EVENTS", e)
    fast_send_email(place_id, "ERROR LOADING MINCULT EVENTS " + str(e))


def get_email_server():
    if config.SMTP_SERVER == 'smtp.yandex.ru':
        server = smtplib.SMTP_SSL(config.SMTP_SERVER)
    else:
        server = smtplib.SMTP(config.SMTP_SERVER, 25)
    server.login(config.EMAIL_LOGIN, config.EMAIL_PASS)
    return server


def send_email(server, for_url, from_url):
    from_addr = 'Mr. Parser <%s>' % config.EMAIL_LOGIN
    to_addr = 'Mr. Poster <%s>' % config.TRELLO_EMAIL
    subj = 'New event'
    msg_txt = 'Change image for: ' + for_url + " from: " + from_url + ""

    msg = "From: %s\nTo: %s\nSubject: %s\n\n%s" % (from_addr, to_addr, subj, msg_txt)
    server.sendmail(from_addr, to_addr, msg)


def fast_send_email(org, msg_text):
    send_email_for_org(get_email_server(), org, msg_text)


def send_email_for_org(server, org, msg_text):
    if msg_text == "":
        return
    from_addr = 'Mr. Parser <%s>' % config.EMAIL_LOGIN
    to_addr = 'Mr. Poster <%s>' % config.TRELLO_EMAIL
    subj = 'New events for ' + org

    msg = "From: %s\nTo: %s\nSubject: %s\n\n%s" % (from_addr, to_addr, subj, msg_text)
    server.sendmail(from_addr, to_addr, msg)
