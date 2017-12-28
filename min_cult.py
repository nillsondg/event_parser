import requests
import json
import time
import datetime
import mimetypes, base64
import event_creator
from parse_logger import send_email_for_org, get_email_server, log_loading_mincult_error

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


def get_org_json(place_id):
    print("getting events from mincult for", str(place_id))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    url = "https://all.culture.ru/api/2.3/events?places={place_id}&status=accepted&start={start_timestamp}"

    res_url = url.format(place_id=place_id, start_timestamp=int(time.time()), headers=headers)
    r = requests.get(res_url)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        events_json = json.loads(r.content.decode('utf-8'))
        return events_json


def get_eventdesc_from_mincult(place_id, event_json):
    org_id = get_evendate_org_id(place_id)
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
        house = place["house"]["type"] + " " + place["house"]["name"]

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

    def prepare_desc(desc):
        if len(desc) > 2000:
            return desc[:2000]
        return desc

    def get_public_date():
        public_date = datetime.datetime.today() \
            .replace(day=datetime.datetime.today().day, hour=14, minute=0, second=0, microsecond=0)
        public_date += datetime.timedelta(days=1)
        return public_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    def get_img(url):
        img_raw = requests.get(url, allow_redirects=True)
        content_type = img_raw.headers['content-type']
        extension = mimetypes.guess_extension(content_type)
        if extension == ".jpe":
            extension = ".jpeg"
        img = "data:{};base64,".format(content_type) + base64.b64encode(img_raw.content).decode("utf-8")
        filename = "image" + extension
        return img, filename

    img, filename = get_img(img_url)
    detail_url_format = "https://all.culture.ru/api/2.2/events/{id}"
    detail_url = detail_url_format.format(id=event_json["_id"])

    res = {"organization_id": org_id, "title": title, "dates": prepare_evendate_dates(dates), "location": location,
           "description": prepare_desc(description), "is_free": is_free, "price": price, "tags": tags,
           "detail_info_url": detail_url, "public_at": get_public_date(),
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def prepare_msg_text(done_list, error_list, update_list):
    text = ""
    for res_url, url in done_list:
        text += "ADDED " + res_url + "\r\n"
    for url in error_list:
        text += "ERROR " + url + "\r\n"
    for url in update_list:
        text += "UPDATED " + url + "\r\n"
    return text


def process_org(place_id):
    done_events = read_events_from_file(place_id)
    error_list = list()
    done_list = list()
    update_list = list()
    # todo update

    try:
        events_json = get_org_json(place_id)
    except Exception as e:
        log_loading_mincult_error(place_id, e)
        return

    for event in events_json["events"]:
        event_desc = get_eventdesc_from_mincult(place_id, event)
        _id = event["_id"]
        if _id not in done_events.keys():
            evendate_url, evendate_id = event_creator.post_to_evendate(event_desc)
            if evendate_url is not None:
                write_url_to_file(place_id, _id, evendate_id)
                done_list.append(evendate_url)
            else:
                error_list.append("place_id: {}, _id: {}".format(place_id, _id))

    send_email_for_org(get_email_server(), place_id, prepare_msg_text(done_list, error_list, update_list))


def get_evendate_org_id(place_id):
    return {
        6201: 253
    }[place_id]


def process_all():
    # Кусково
    process_org(6201)
