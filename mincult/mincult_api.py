import json
import time
import requests
import config


def get_org_events(place_id):
    print("getting events from mincult for", str(place_id))
    url = "https://all.culture.ru/api/2.3/events?places={place_id}&status=accepted&start={start_timestamp}"

    res_url = url.format(place_id=place_id, start_timestamp=int(time.time() * 1000))
    print(res_url)
    r = requests.get(res_url)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        events_json = json.loads(r.content.decode('utf-8'))
        return events_json
    else:
        return None


def get_org_from_mincult(place_id):
    print("getting org from mincult for", str(place_id))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    url = "https://all.culture.ru/api/2.3/places/{place_id}"

    res_url = url.format(place_id=place_id, headers=headers)
    print(res_url)
    r = requests.get(res_url)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        org_json = json.loads(r.content.decode('utf-8'))
        return org_json
    else:
        return None


def post_stats(stats_json):
    url = "https://all.culture.ru/api/2.3/import?apiKey={}".format(config.MINCULT_KEY)
    headers = {'Content-type': "application/json"}
    print(url)
    r = requests.post(url, data=json.dumps(stats_json), headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        res_json = json.loads(r.content.decode('utf-8'))
        return res_json
    else:
        return None


def get_events_in_category(category, locale):
    print("getting events from min cult for", category, "in locale", locale)
    url = "https://all.culture.ru/api/2.3/events?status=accepted&start={}&locales={}&placeCategory={}&limit=50"

    res_url = url.format(int(time.time() * 1000), locale, category)
    print(res_url)
    r = requests.get(res_url)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        res_json = json.loads(r.content.decode('utf-8'))
        return res_json
    else:
        return None
