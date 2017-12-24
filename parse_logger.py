import datetime
import event_creator

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
    event_creator.fast_send_email(org, "ERROR PARSING CATALOG " + str(e))


def log_event_error(org, e):
    print("ERROR PARSING EVENT", e)
    event_creator.fast_send_email(org, "ERROR PARSING EVENT " + str(e))
