import json
import time
import requests
import config


def get_org_json(place_id):
    print("getting events from mincult for", str(place_id))
    url = "https://all.culture.ru/api/2.3/events?places={place_id}&status=accepted&start={start_timestamp}"

    res_url = url.format(place_id=place_id, start_timestamp=int(time.time()))
    r = requests.get(res_url)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        events_json = json.loads(r.content.decode('utf-8'))
        return events_json
    else:
        return None


def post_stats(stats_json):
    url = "https://all.culture.ru/api/2.2/import?apiKey={}".format(config.MINCULT_KEY)
    headers = {'Content-type': "application/json"}
    r = requests.post(url, data=json.dumps(stats_json), headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        res_json = json.loads(r.content.decode('utf-8'))
        return res_json
    else:
        return None
