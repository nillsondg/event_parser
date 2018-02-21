from mincult.mincult_api import get_events_in_category
from mincult.org_creator import add_orgs


def collect_orgs_from_events(locales, categories):
    orgs = set()
    for locale in locales:
        for category in categories:
            res_json = get_events_in_category(category, locale)
            for event in res_json["events"]:
                # if len(event["places"]) > 1:
                #   print("got places > 1")
                for org in event["places"]:
                    try:
                        orgs.add(org["_id"])
                    except KeyError:
                        pass
    return orgs


def bulk_add_orgs():
    locales = [2579, 1641, 205, 203, 739, 2002, 1310, 1722, 2591,
               805, 1572, 1643, 1170, 718, 1495, 552, 2568, 1449,
               2196, 1469, 2038]
    categories = ["koncertnye-ploshchadki", "kulturnoe-nasledie",
                  "muzei-i-galerei", "parki", "teatry"]
    # "kinoteatry", "cirki", "dvorcy-kultury-i-kluby", "pamyatniki", "obrazovatelnye-uchrezhdeniya"
    org_ids = collect_orgs_from_events(locales, categories)
    add_orgs(org_ids)
