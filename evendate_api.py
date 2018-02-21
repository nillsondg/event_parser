import config
import requests
import parse_logger
import json


def post_event_to_evendate(event_desc):
    print("posting " + event_desc['detail_info_url'])
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.post("https://evendate.io/api/v1/events/", data=json.dumps(event_desc), headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        event = json.loads(r.text)["data"]
        evendate_url = format_evendate_event_url(event["event_id"])
        print("POSTED " + evendate_url)
        return evendate_url, event["event_id"]
    else:
        text = r.text.encode().decode("unicode_escape")
        parse_logger.log_posting_error(event_desc['detail_info_url'], text)
        return None, None


def put_event_to_evendate(event_id, event_desc):
    print("updating " + event_desc['detail_info_url'])
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.put("https://evendate.io/api/v1/events/{}".format(event_id),
                     data=json.dumps(event_desc), headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        event = json.loads(r.text)["data"]
        evendate_url = format_evendate_event_url(event["event_id"])
        print("UPDATED " + evendate_url)
        return evendate_url, event["event_id"]
    else:
        text = r.text.encode().decode("unicode_escape")
        parse_logger.log_posting_error(event_desc['detail_info_url'], text)
        return None, None


def cancel_event(event_id):
    print("cancelling event {}".format(event_id))
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.put("https://evendate.io/api/v1/events/{}/status?canceled=true".format(event_id), headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        updated = bool(json.loads(r.text)["status"])
        print("UPDATED event {}".format(event_id))
        return updated, event_id
    else:
        text = r.text.encode().decode("unicode_escape")
        parse_logger.log_posting_error("event {}".format(event_id), text)
        return None, None


def format_evendate_event_url(event_id):
    return "https://evendate.io/event/{}".format(event_id)


def get_org(org_id, fields):
    print("getting org {}".format(org_id))
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.get("https://evendate.io/api/v1/organizations/{}?fields={}".format(org_id, fields), headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        org = json.loads(r.text, strict=False)["data"][0]
        evendate_url = format_evendate_org_url(org["id"])
        print("GOT", evendate_url)
        return org, org["id"]
    else:
        text = r.text.encode().decode("unicode_escape")
        parse_logger.log_posting_org_error("org {}".format(org_id), text)
        return None, None


def post_org_to_evendate(org_desc):
    print("posting " + org_desc['site_url'])
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.post("https://evendate.io/api/v1/organizations/", data=json.dumps(org_desc), headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        org = json.loads(r.text)["data"]
        evendate_url = format_evendate_org_url(org["organization_id"])
        print("POSTED " + evendate_url)
        return evendate_url, org["organization_id"]
    else:
        text = r.text.encode().decode("unicode_escape")
        parse_logger.log_posting_org_error(org_desc['site_url'], text)
        return None, None


def update_org_in_evendate(org_id, org_desc):
    print("updating", org_id)
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.put("https://evendate.io/api/v1/organizations/{}".format(org_id), data=json.dumps(org_desc),
                     headers=headers)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        org = json.loads(r.text)["data"]
        evendate_url = format_evendate_org_url(org["organization_id"])
        print("UPDATED " + evendate_url)
        return evendate_url, org["organization_id"]
    else:
        text = r.text.encode().decode("unicode_escape")
        parse_logger.log_posting_org_error("org {}".format(org_id), text)
        return None, None


def format_evendate_org_url(org_id):
    return "https://evendate.io/organization/{}".format(org_id)


def get_stats(event_id):
    print("getting stats for event " + str(event_id))
    headers = {'Authorization': config.AUTH_TOKEN}
    r = requests.get(_format_stat_api_url(event_id), headers=headers)
    print(r.status_code, r.reason)
    text = r.text.encode().decode("unicode_escape")
    if r.status_code == 200:
        try:
            stats = json.loads(r.text)["data"]
        except TypeError:
            parse_logger.log_getting_event_stats_error(str(event_id), text)
            return None
        return stats
    else:
        parse_logger.log_getting_event_stats_error(str(event_id), text)
        return None


def _format_stat_api_url(event_id):
    return "http://evendate.io/api/v1/statistics/events/{}?scale=overall&fields=fave,view_detail".format(str(event_id))
