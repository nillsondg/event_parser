import config
import requests
import parse_logger
import json


def post_event_to_evendate(event_desc):
    print("posting " + event_desc['detail_info_url'])
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.post("https://evendate.io/api/v1/events/", data=json.dumps(event_desc), headers=headers)
    print(r.status_code, r.reason)
    text = r.text.encode().decode("unicode_escape")
    if r.status_code == 200:
        event = json.loads(text)["data"]
        evendate_url = format_evendate_event_url(event["event_id"])
        print("POSTED " + evendate_url)
        return evendate_url, event["event_id"]
    else:
        parse_logger.log_posting_error(event_desc['detail_info_url'], text)
        return None, None


def format_evendate_event_url(event_id):
    return "https://evendate.io/event/" + str(event_id)


def post_org_to_evendate(org_desc):
    print("posting " + org_desc['site_url'])
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.post("https://evendate.io/api/v1/organizations/", data=json.dumps(org_desc), headers=headers)
    print(r.status_code, r.reason)
    text = r.text.encode().decode("unicode_escape")
    if r.status_code == 200:
        org = json.loads(text)["data"]
        evendate_url = format_evendate_org_url(org["organization_id"])
        print("POSTED " + evendate_url)
        return evendate_url, org["organization_id"]
    else:
        parse_logger.log_posting_org_error(org_desc['site_url'], text)
        return None, None


def update_org_in_evendate(org_id, org_desc):
    print("updating " + org_desc['site_url'])
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.put("https://evendate.io/api/v1/organizations/{}".format(org_id), data=json.dumps(org_desc),
                     headers=headers)
    print(r.status_code, r.reason)
    text = r.text.encode().decode("unicode_escape")
    if r.status_code == 200:
        org = json.loads(text)["data"]
        evendate_url = format_evendate_org_url(org["organization_id"])
        print("UPDATED " + evendate_url)
        return evendate_url, org["organization_id"]
    else:
        parse_logger.log_posting_org_error(org_desc['site_url'], text)
        return None, None


def format_evendate_org_url(org_id):
    return "https://evendate.io/organization/" + str(org_id)


def get_stats(event_id):
    print("getting stats for event " + str(event_id))
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.get(_format_stat_api_url(event_id), headers=headers)
    print(r.status_code, r.reason)
    text = r.text.encode().decode("unicode_escape")
    if r.status_code == 200:
        try:
            stats = json.loads(text)["data"]
        except TypeError:
            parse_logger.log_getting_event_stats_error(str(event_id), text)
            return None
        return stats
    else:
        parse_logger.log_getting_event_stats_error(str(event_id), text)
        return None


def _format_stat_api_url(event_id):
    return "http://evendate.io/api/v1/statistics/events/{}?scale=overall&fields=fave,view_detail".format(str(event_id))
