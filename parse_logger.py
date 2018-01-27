import datetime
import smtplib
import config
from transliterate import translit

events_folder = "events/"
events_desc_folder = "events_desc/"


def __read_events_from_file(folder, file_name):
    exist_urls = set()
    try:
        with open(folder + file_name) as f:
            for line in f:
                exist_urls.add(line.strip().split(' ')[1])
    except IOError:
        pass
    return exist_urls


def __read_urls_from_file(folder, file_name):
    exist_urls = set()
    try:
        with open(folder + file_name) as f:
            for line in f:
                exist_urls.add(line.strip())
    except IOError:
        pass
    return exist_urls


def write_url_to_file(folder, file_name, url):
    f = open(folder + file_name, 'a+')
    f.write(datetime.datetime.now().strftime("%y.%m.%d|%H:%M:%S ") + url + "\n")
    f.close()


def read_completed_urls(file_name):
    return __read_events_from_file(events_desc_folder, file_name)


def read_checked_urls(file_name):
    return __read_events_from_file(events_folder, file_name)


def read_ignored_urls():
    return __read_urls_from_file(events_desc_folder, "_ignore.txt")


# min cult
def read_ors_from_file():
    exist_orgs = dict()
    file_name = "orgs.txt"
    try:
        with open(file_name) as f:
            for line in f:
                date, min_id, even_id = line.strip().split(' ')
                exist_orgs[min_id] = even_id
    except IOError:
        pass
    return exist_orgs


def log_catalog_error(org, e):
    print("ERROR PARSING CATALOG", e)
    fast_send_email("Error parsing catalog for " + org, "ERROR PARSING CATALOG " + str(e))


def log_event_parsing_error(url, e):
    print("ERROR PARSING EVENT", e)
    fast_send_email("Error parsing " + url, "ERROR PARSING EVENT " + str(e))


def log_posting_error(url, error_text):
    print("ERROR POSTING EVENT", error_text)
    fast_send_email("Error posting " + url, "ERROR POSTING EVENT " + error_text)


def log_posting_org_error(url, error_text):
    print("ERROR POSTING ORG", error_text)
    fast_send_email("Error posing org " + url, "ERROR POSTING ORG " + error_text)


def log_getting_event_stats_error(event_id, error_text):
    print("ERROR GETTING STATS ", error_text)
    fast_send_email("Error getting stats for event " + event_id, "ERROR GETTING STATS " + error_text)



def log_loading_mincult_error(place_id, e):
    print("ERROR LOADING MINCULT EVENTS", e)
    fast_send_email("Error loading mincult org " + str(place_id), "ERROR LOADING MINCULT EVENTS " + str(e))


def get_email_server():
    if config.SMTP_SERVER == 'smtp.yandex.ru':
        server = smtplib.SMTP_SSL(config.SMTP_SERVER)
    else:
        server = smtplib.SMTP(config.SMTP_SERVER, 25)
    server.login(config.EMAIL_LOGIN, config.EMAIL_PASS)
    return server


def fast_send_email(header, msg):
    send_email(get_email_server(), header, msg)


def send_email(server, header, msg_text):
    if msg_text == "":
        return
    from_addr = 'Mr. Parser <%s>' % config.EMAIL_LOGIN
    to_addr = 'Mr. Poster <%s>' % config.TRELLO_EMAIL
    subj = header
    msg = "From: %s\nTo: %s\nSubject: %s\n\n%s" % (from_addr, to_addr, subj, msg_text)
    server.sendmail(from_addr, to_addr, translit(msg, 'ru', reversed=True))
