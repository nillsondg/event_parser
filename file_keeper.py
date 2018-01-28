import datetime

events_folder = "events/"
events_desc_folder = "events_desc/"
mincult_folder = "mincult/"
mincult_events_folder = "mincult_events/"


def __read_urls_from_file(folder, file_name):
    exist_urls = set()
    try:
        with open(folder + file_name) as f:
            for line in f:
                exist_urls.add(line.strip().split(' ')[1])
    except IOError:
        pass
    return exist_urls


def __read_ignore_urls_from_file(folder, file_name):
    exist_urls = set()
    try:
        with open(folder + file_name) as f:
            for line in f:
                exist_urls.add(line.strip())
    except IOError:
        pass
    return exist_urls


def __write_url_to_file(folder, file_name, url):
    f = open(folder + file_name, 'a+')
    f.write(datetime.datetime.now().strftime("%y.%m.%d|%H:%M:%S ") + url + "\n")
    print("added " + url)
    f.close()


def write_events_to_file(file_name, url_set, exist_url_set):
    f = open(events_folder + file_name, 'a+')
    for url in url_set:
        if url not in exist_url_set:
            f.write(datetime.datetime.now().strftime("%y.%m.%d|%H:%M:%S ") + url + "\n")
            print("added " + url)
    f.close()


def write_completed_url(file_name, url):
    __write_url_to_file(events_desc_folder, file_name, url)


def read_completed_urls(file_name):
    return __read_urls_from_file(events_desc_folder, file_name)


def read_checked_urls(file_name):
    return __read_urls_from_file(events_folder, file_name)


def read_ignored_urls():
    return __read_ignore_urls_from_file(events_desc_folder, "_ignore.txt")


# min cult
def read_mincult_ors_from_file():
    exist_orgs = dict()
    file_name = mincult_folder + "orgs.txt"
    try:
        with open(file_name) as f:
            for line in f:
                date, min_id, even_id = line.strip().split(' ')
                exist_orgs[int(min_id)] = int(even_id)
    except IOError:
        pass
    return exist_orgs


def write_mincult_orgs_to_file(org_dict, exist_org_dict):
    file_name = mincult_folder + "orgs.txt"
    f = open(file_name, 'a+')
    for min_id, even_id in org_dict.items():
        if min_id not in exist_org_dict.keys():
            f.write(datetime.datetime.now().strftime("%y.%m.%d|%H:%M:%S ") + str(min_id) + " " + str(even_id) + "\n")
            print("added " + min_id)
    f.close()


def read_mincult_events_from_file(place_id):
    exist_ids = dict()
    try:
        with open(mincult_events_folder + str(place_id) + ".txt") as f:
            for line in f:
                date, min_id, even_id = line.strip().split(' ')
                exist_ids[int(min_id)] = int(even_id)
    except IOError:
        pass
    return exist_ids


def write_mincult_event_to_file(place_id, mincult_id, evendate_id):
    f = open(mincult_events_folder + str(place_id) + ".txt", 'a+')
    f.write(datetime.datetime.now().strftime("%y.%m.%d|%H:%M:%S ") + str(mincult_id) + " " + str(evendate_id) + "\n")
    f.close()
