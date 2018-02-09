import smtplib
import config
from transliterate import translit


def log_catalog_error(org, e):
    print("ERROR PARSING CATALOG", e)
    fast_send_email("Error parsing catalog for " + org, "ERROR PARSING CATALOG " + str(e))


def log_event_parsing_error(url, e):
    print("ERROR PARSING EVENT", e)
    fast_send_email("Error parsing " + url, "ERROR PARSING EVENT " + str(e))


def log_posting_error(url, error_text):
    print("ERROR POSTING EVENT", error_text)
    fast_send_email("Error posting " + url, "ERROR POSTING EVENT " + error_text)


def log_updating_error(url, error_text):
    print("ERROR UPDATING EVENT", error_text)
    fast_send_email("Error updating " + url, "ERROR UPDATING EVENT " + error_text)


def log_posting_org_error(url, error_text):
    print("ERROR POSTING ORG", error_text)
    fast_send_email("Error posing org " + url, "ERROR POSTING ORG " + error_text)


def log_getting_event_stats_error(event_id, error_text):
    print("ERROR GETTING STATS ", error_text)
    fast_send_email("Error getting stats for event " + event_id, "ERROR GETTING STATS " + error_text)


def log_loading_mincult_error(place_id, e):
    print("ERROR LOADING MINCULT EVENTS", e)
    fast_send_email("Error loading mincult org " + str(place_id), "ERROR LOADING MINCULT EVENTS " + str(e))


def log_loading_mincult_event_error(event_id, e):
    print("ERROR LOADING MINCULT EVENT", e)
    fast_send_email("Error loading mincult event " + str(event_id), "ERROR LOADING MINCULT EVENT " + str(e))


def log_preparing_mincult_error(place_id, e):
    print("ERROR PREPARING MINCULT EVENT", e)
    fast_send_email("Error preparing mincult event " + str(place_id), "ERROR PREPARING MINCULT EVENTS " + str(e))


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
