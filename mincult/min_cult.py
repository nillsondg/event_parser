import datetime
import evendate_api
from parse_logger import fast_send_email, log_loading_mincult_error, log_preparing_mincult_error, \
    log_loading_mincult_event_error
from bs4 import BeautifulSoup
from mincult.mincult_api import get_org_events, post_stats, get_event_from_mincult
from evendate_api import format_evendate_event_url
import time
from utils import get_img
from mincult import min_cult_utils
from file_keeper import read_mincult_events_from_file, write_mincult_event_to_file, read_mincult_ors_from_file, \
    write_canceled_events_to_file, read_canceled_events_from_file


def get_eventdesc_from_mincult(org_id, event_json):
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

    location = min_cult_utils.prepare_location(event_json["places"][0]["address"])

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
            if day[0].day != day[1].day:
                end_time = "23:59"
                event_date2 = day[1].strftime('%Y-%m-%d')
                start_time2 = "00:00"
                end_time2 = day[1].strftime('%H:%M')
                date2 = {"event_date": event_date2, "start_time": start_time2, "end_time": end_time2}
                new_dates.append(date2)
            if end_time == "00:00":
                end_time = "23:59"
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

    img, filename = get_img(img_url)

    def prepare_detail_url():
        def get_default_url(id):
            url_format = "https://all.culture.ru/public/events/{id}"
            url = url_format.format(id=id)
            return url

        url = ""
        try:
            for info in event_json['externalInfo']:
                if "culture.ru" in info["url"]:
                    return info["url"]
                if "mkrj.ru" in info["url"]:
                    url = info["url"]
            if url is not None:
                return url
            else:
                return get_default_url(event_json["_id"])
        except KeyError:
            return get_default_url(event_json["_id"])

    detail_url = prepare_detail_url()

    res = {"organization_id": org_id, "title": title, "dates": prepare_evendate_dates(dates), "location": location,
           "description": prepare_desc(description), "is_free": is_free, "min_price": price,
           "tags": tags,
           "detail_info_url": detail_url,
           "image_horizontal": img,
           "filenames": {'horizontal': filename}}
    return res


def process_org(place_id, org_id):
    done_events = read_mincult_events_from_file(place_id)
    error_list = list()
    done_list = list()
    updated_list = list()
    # todo update

    try:
        events_json = get_org_events(place_id)
    except Exception as e:
        log_loading_mincult_error(place_id, e)
        return done_list, error_list

    for event in events_json["events"]:
        _id = event["_id"]
        if _id in done_events.keys():
            continue
        try:
            event_desc = get_eventdesc_from_mincult(org_id, event)
        except Exception as e:
            log_preparing_mincult_error(_id, e)
            return done_list, error_list

        evendate_url, evendate_id = evendate_api.post_event_to_evendate(event_desc)
        if evendate_url is not None:
            write_mincult_event_to_file(place_id, _id, evendate_id)
            done_list.append(evendate_url)
        else:
            error_list.append("place_id: {}, _id: {}".format(place_id, _id))

    return done_list, error_list


def sync_stats(place_id, org_id):
    done_events = read_mincult_events_from_file(place_id)
    error_list = list()
    done_list = list()
    canceled_events = read_canceled_events_from_file()

    stats = {"items": []}
    for mincult_id, evendate_id in done_events.items():
        if mincult_id in canceled_events.keys():
            print("Skip event mincult_id {}, evendate_id: {}".format(mincult_id, evendate_id))
            continue
        event_stats = evendate_api.get_stats(evendate_id)
        if event_stats is None:
            error = "Error getting stats to mincult for event mincult_id {}, evendate_id: {}".format(mincult_id,
                                                                                                     evendate_id)
            error_list.append(error)
            return False, error
        prepared_stats = prepare_stats(mincult_id, evendate_id, event_stats)
        stats["items"].append(prepared_stats)
        done_list.append(evendate_api.format_evendate_event_url(evendate_id))
    if len(stats["items"]) == 0:
        error = "Nothing to sync for mincult_id: {}, evendate_id: {}".format(place_id, org_id)
        print(error)
        return True, error
    res = post_stats(stats)
    if res is not None:
        print(get_update_stats_res(res))
        print("synced stats for org mincult_id: {}, evendate_id: {}".format(place_id, org_id))
        print("Synced stats for {}".format(len(done_list)))
        if check_non_found_events_exist(res):
            cancel_removed_events([place_id])
        return True, get_update_stats_res(res)
    else:
        error = "Error posting stats to mincult for org mincult_id {}, evendate_id: {}".format(place_id, org_id)
        error_list.append(error)
        print(error)
        return False, error


def get_update_stats_res(res_json):
    return "Updated: {}. Not Found: {}".format(res_json["result"]["updated"]["count"],
                                               res_json["result"]["notFound"]["count"])


def check_non_found_events_exist(res_json):
    if res_json["result"]["notFound"]["count"] > 0:
        return True
    else:
        return False


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
    exist_orgs = read_mincult_ors_from_file()
    done_stat_list = []
    error_stat_list = []
    done_list = []
    error_list = []
    updated_list = []
    for min_id, even_id in exist_orgs.items():
        res_sync = sync_stats(min_id, even_id)
        if res_sync[0]:
            done_stat_list.append((min_id, res_sync[1]))
        else:
            error_stat_list.append((min_id, res_sync[1]))
        done, errors = process_org(min_id, even_id)
        done_list.extend(done)
        error_list.extend(errors)
    fast_send_email(prepare_msg_sync_header(done_stat_list, error_stat_list),
                    prepare_msg_sync_text(done_stat_list, error_stat_list))
    fast_send_email(prepare_msg_header(done_list, error_list), prepare_msg_text(done_list, error_list, updated_list))


def update_org(place_id, org_id):
    done_events = read_mincult_events_from_file(place_id)
    error_list = list()
    done_list = list()

    for min_id, even_id in done_events.items():
        result = update_event(org_id, min_id, even_id)
        if result is not None:
            done_list.append("min_id: {}, even_id: {}".format(min_id, even_id))
        else:
            error_list.append("place_id: {}, _id: {}".format(place_id, min_id))

    return done_list, error_list


def update_event(org_id, min_id, even_id):
    try:
        event_json = get_event_from_mincult(min_id)
    except Exception as e:
        log_loading_mincult_event_error(min_id, e)
        return False

    try:
        event_desc = get_eventdesc_from_mincult(org_id, event_json)
    except Exception as e:
        log_preparing_mincult_error(min_id, e)
        return False

    evendate_url, evendate_id = evendate_api.put_event_to_evendate(even_id, event_desc)

    if evendate_url is not None:
        return True
    else:
        return False


def update_all():
    exist_orgs = read_mincult_ors_from_file()
    done_list = []
    error_list = []
    for min_id, even_id in exist_orgs.items():
        done, errors = update_org(min_id, even_id)
        done_list.extend(done)
        error_list.extend(errors)
    fast_send_email(prepare_msg_update_header(done_list, error_list),
                    prepare_msg_update_text(done_list, error_list))


def prepare_msg_header(done_list, error_list):
    return "Added events from Min cult +{}/-{}".format(len(done_list), len(error_list))


def prepare_msg_sync_header(done_list, error_list):
    return "Synced stats with Min cult +{}/-{}".format(len(done_list), len(error_list))


def prepare_msg_update_header(done_list, error_list):
    return "Updated events with Min cult +{}/-{}".format(len(done_list), len(error_list))


def prepare_msg_text(done_list, error_list, update_list):
    text = ""
    for url in done_list:
        text += "ADDED {}\r\n".format(url)
    for url in error_list:
        text += "ERROR {}\r\n".format(url)
    for url in update_list:
        text += "UPDATED {}\r\n".format(url)
    return text


def prepare_msg_sync_text(done_list, error_list):
    text = ""
    for min_id, msg in done_list:
        text += "SYNCED {} | {}\r\n".format(min_id, msg)
    for min_id, error_msg in error_list:
        text += "ERROR {} | {}\r\n".format(min_id, error_msg)
    return text


def prepare_msg_update_text(done_list, error_list):
    text = ""
    for url in done_list:
        text += "UPDATED {}\r\n".format(url)
    for url in error_list:
        text += "ERROR {}\r\n".format(url)
    return text


def cancel_removed_events(place_ids):
    def cancel_event(min_event_id, event_id):
        canceled = evendate_api.cancel_event(event_id)[0]
        if canceled:
            write_canceled_events_to_file({min_event_id: event_id})
            print("Canceled")
            fast_send_email("Canceled event", "CANCELED min_id {} | even_id {}".format(min_event_id, event_id))
        else:
            print("Error canceling")

    removed_events = []
    for place_id in place_ids:
        done_events = read_mincult_events_from_file(place_id)
        for min_id, even_id in done_events.items():
            res = get_event_from_mincult(min_id)
            if res is None:
                removed_events.append("NotFound min_id {} | even_id {}".format(min_id, even_id))
                cancel_event(min_id, even_id)
    for removed in removed_events:
        print(removed + "\r\n")
    print("NotFound len = " + str(len(removed_events)))
