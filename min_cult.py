import requests
import datetime
import mimetypes, base64
import evendate_api
from parse_logger import fast_send_email, log_loading_mincult_error, read_ors_from_file
from bs4 import BeautifulSoup
from mincult_api import get_org_json, post_stats
from evendate_api import format_evendate_event_url
import time
from utils import crop_img_to_16x9

mincult_folder = "mincult_events/"


def read_events_from_file(place_id):
    exist_ids = dict()
    try:
        with open(mincult_folder + str(place_id) + ".txt") as f:
            for line in f:
                mincult_id = int(line.strip().split(' ')[1])
                evendate_id = int(line.strip().split(' ')[2])
                exist_ids[mincult_id] = evendate_id
    except IOError:
        pass
    return exist_ids


def write_url_to_file(place_id, mincult_id, evendate_id):
    f = open(mincult_folder + str(place_id) + ".txt", 'a+')
    f.write(datetime.datetime.now().strftime("%y.%m.%d|%H:%M:%S ") + str(mincult_id) + " " + str(evendate_id) + "\n")
    f.close()


def get_eventdesc_from_mincult(place_id, org_id, event_json):
    title = event_json["name"]
    description = event_json["description"]
    is_free = event_json["isFree"]
    price = event_json["price"]
    price = price if price is not None else 0

    def prepare_tags():
        tags = []
        for tag in event_json["tags"]:
            tags.append(tag["name"])
            if len(tags) >= 5:
                break
        return tags

    tags = prepare_tags()

    def prepare_location():
        place = event_json["places"][0]["address"]
        region = place["region"]["name"]
        city = place["city"]["type"] + " " + place["city"]["name"]
        street = place["street"]["type"] + " " + place["street"]["name"]
        try:
            house = place["house"]["type"] + place["house"]["name"]
        except KeyError:
            house = place["house"]["name"]

        return "{}, {}, {}, {}".format(region, city, street, house)

    location = prepare_location()

    def prepare_dates():
        dates = []
        for seance in event_json["seances"]:
            dates.append(
                (datetime.datetime.fromtimestamp(seance["start"] / 1000),
                 datetime.datetime.fromtimestamp(seance["end"] / 1000)))
        return dates

    dates = prepare_dates()

    img_format = "https://all.culture.ru/uploads/{name}"
    img_url = img_format.format(name=event_json["image"]["name"])

    def prepare_evendate_dates(dates):
        new_dates = []
        for day in dates:
            event_date = day[0].strftime('%Y-%m-%d')
            start_time = day[0].strftime('%H:%M')
            end_time = day[1].strftime('%H:%M')
            date = {"event_date": event_date, "start_time": start_time, "end_time": end_time}
            new_dates.append(date)
        return new_dates

    def cleanhtml(raw_html):
        soup = BeautifulSoup(raw_html, "lxml")
        return soup.get_text()

    def prepare_desc(desc):
        desc = cleanhtml(desc)
        desc = desc.replace("  ", " ")
        if len(desc) > 2000:
            return desc[:2000]
        return desc

    def get_public_date():
        public_date = datetime.datetime.today() \
            .replace(day=datetime.datetime.today().day, hour=14, minute=0, second=0, microsecond=0)
        public_date += datetime.timedelta(days=1)
        return public_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    def get_img(url):
        res = requests.get(url, allow_redirects=True)
        content_type = res.headers['content-type']
        extension = mimetypes.guess_extension(content_type)
        if extension == ".jpe":
            extension = ".jpeg"
        img = "data:{};base64,".format(content_type) + base64.b64encode(crop_img_to_16x9(res.content)) \
            .decode("utf-8")
        filename = "image" + extension
        return img, filename

    img, filename = get_img(img_url)
    detail_url_format = "https://all.culture.ru/public/events/{id}"
    detail_url = detail_url_format.format(id=event_json["_id"])

    res = {"organization_id": org_id, "title": title, "dates": prepare_evendate_dates(dates), "location": location,
           "description": prepare_desc(description), "is_free": is_free, "price": price,
           "tags": tags,
           "detail_info_url": detail_url, "public_at": get_public_date(),
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def prepare_msg_text(done_list, error_list, update_list):
    text = ""
    for url in done_list:
        text += "ADDED " + url + "\r\n"
    for url in error_list:
        text += "ERROR " + url + "\r\n"
    for url in update_list:
        text += "UPDATED " + url + "\r\n"
    return text


def prepare_msg_sync_text(done_list, error_list):
    text = ""
    for url in done_list:
        text += "SYNCED " + url + "\r\n"
    for url in error_list:
        text += "ERROR " + url + "\r\n"
    return text


def process_org(place_id, org_id):
    done_events = read_events_from_file(place_id)
    error_list = list()
    done_list = list()
    updated_list = list()
    # todo update

    try:
        events_json = get_org_json(place_id)
    except Exception as e:
        log_loading_mincult_error(place_id, e)
        return

    for event in events_json["events"]:
        event_desc = get_eventdesc_from_mincult(place_id, org_id, event)
        _id = event["_id"]
        if _id not in done_events.keys():
            evendate_url, evendate_id = evendate_api.post_event_to_evendate(event_desc)
            if evendate_url is not None:
                write_url_to_file(place_id, _id, evendate_id)
                done_list.append(evendate_url)
            else:
                error_list.append("place_id: {}, _id: {}".format(place_id, _id))

    fast_send_email(str(place_id), prepare_msg_text(done_list, error_list, updated_list))


def sync_stats(place_id, org_id):
    done_events = read_events_from_file(place_id)
    error_list = list()
    done_list = list()

    stats = {"items": []}
    for mincult_id, evendate_id in done_events.items():
        event_stats = evendate_api.get_stats(evendate_id)
        prepared_stats = prepare_stats(mincult_id, evendate_id, event_stats)
        stats["items"].append(prepared_stats)
        done_list.append(evendate_api.format_evendate_event_url(evendate_id))

    res = post_stats(stats)
    if res is not None:
        print_update_stats_res(res)
        print("synced stats for org mincult_id: {}, evendate_id: {}".format(place_id, org_id))
        print("Synced stats for {}".format(len(done_list)))
        return True
    else:
        error_list.append(
            "Error posting stats to mincult for org mincult_id {}, evendate_id: {}".format(place_id, org_id))
        return False


def print_update_stats_res(res_json):
    print("Updated: {}. Not Found: {}".format(res_json["result"]["updated"]["count"],
                                              res_json["result"]["notFound"]["count"]))


def prepare_stats(min_event_id, event_id, evendate_stats_json):
    # evendate format
    # "{'fave': [{'value': 0, 'time_value': 1516725004}], 'view_detail': [{'value': 9, 'time_value': 1516725004}]}"
    time_now = int(round(time.time() * 1000))
    min_stats = {
        "entity": {
            "_id": min_event_id,
            "type": "events"
        },
        "views": evendate_stats_json["view_detail"][0]["value"],
        "likes": evendate_stats_json["fave"][0]["value"],
        "url": format_evendate_event_url(event_id),
        "statuses": ["published"],
        "updateDate": time_now
    }
    return min_stats


def process_all():
    exist_orgs = read_ors_from_file()
    done_list = []
    error_list = []
    for min_id, even_id in exist_orgs.items():
        res_sync = sync_stats(min_id, even_id)
        if res_sync:
            done_list.append(min_id)
        else:
            error_list.append(min_id)
        process_org(min_id, even_id)
    fast_send_email(prepare_msg_header(done_list, error_list), prepare_msg_sync_text(done_list, error_list))


def prepare_msg_header(done_list, error_list):
    return "Synced stats with Min cult +{}/-{}".format(len(done_list), len(error_list))
