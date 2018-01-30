import config
import parse_logger
import base64
from bs4 import BeautifulSoup
from evendate_api import post_org_to_evendate, update_org_in_evendate
from mincult import mincult_api, min_cult_utils
from file_keeper import write_mincult_orgs_to_file, read_mincult_ors_from_file, read_mincult_ignored_orgs
from utils import get_img, get_default_img


def get_type(type):
    return {
        "Университеты": 1,
        "Парки": 2,
        "Музеи": 3,
        "Современные музеи": 11,
        "Театры": 4,
        "Концерты": 5,
        "Кинотеатры": 6,
        "Антикафе": 8,
        "Клубы и Бары": 7,
        "Дополнительное образование": 10,
        "Активный отдых": 22,
        "Ассоциации": 20,
        "Общественные организации": 21
    }[type]


def convert_type_to_evendate(min_type):
    return {
        "Библиотеки": "Дополнительное образование",
        "Дворцы культуры и клубы": "Музеи",
        "Кинотеатры": "Кинотеатры",
        "Концертные площадки": "Концерты",
        "Культурное наследие": "Музеи",
        "Музеи и галереи": "Музеи",
        "Образовательные учреждения": "Дополнительное образование",
        "Памятники": "Музеи",
        "Парки": "Парки",
        "Театры": "Театры",
        "Цирки": "Театры",
        "Прочее": "Общественные организации",
    }[min_type]


def prepare_org(org_desc):
    name = org_desc["name"]

    def prepare_short_name(name):
        if len(name) > 30:
            return name[:30]
        return name

    short_name = prepare_short_name(org_desc["name"])

    def cleanhtml(raw_html):
        soup = BeautifulSoup(raw_html, "lxml")
        return soup.get_text()

    def prepare_description(desc):
        if len(desc) > 250:
            return desc[:250]
        return desc

    description = prepare_description(cleanhtml(org_desc["description"]))

    try:
        site_url = org_desc["contacts"]["website"]
    except KeyError:
        site_url = ""
    try:
        vk_url = org_desc["contacts"]["vkontakte"]
    except KeyError:
        vk_url = ""
    try:
        facebook_url = org_desc["contacts"]["facebook"]
    except KeyError:
        facebook_url = ""

    default_address = min_cult_utils.prepare_location(org_desc["address"])

    type_id = get_type(convert_type_to_evendate(org_desc["category"]["name"]))

    def prepare_link(place_id):
        return "https://all.culture.ru/public/places/{}".format(place_id)

    detail_info_url = prepare_link(org_desc["_id"])

    def prepare_img_link():
        return "https://all.culture.ru/uploads/{name}".format(name=org_desc["image"]["name"])

    locale = org_desc["locale"]["_id"]
    try:
        city_id = get_evendate_city_id_from_mincult(locale)
    except KeyError:
        print("can't get evendate city_id for", locale)
        raise ValueError("illegal locale_id " + str(locale))

    try:
        img, img_filename = get_img(prepare_img_link())
    except Exception as e:
        print(e)
        img, img_filename = get_default_img()

    def get_default_logo(img_name="evendate_logo_mini.png", ext="png"):
        with open("images/" + img_name, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        image_horizontal = "data:image/{};base64,".format(ext) + encoded_string.decode("utf-8")
        return image_horizontal, img_name

    logo, logo_filename = get_default_logo()

    org = {"name": name,
           "short_name": short_name,
           "description": description,
           "site_url": site_url,
           "default_address": default_address,
           "vk_url": vk_url,
           "facebook_url": facebook_url,
           "type_id": type_id,
           "background": img,
           "background_filename": img_filename,
           "logo": logo,
           "logo_filename": logo_filename,
           "detail_info_url": detail_info_url,
           "email": config.MY_EMAIL,
           "city_id": city_id
           }
    return org


def add_orgs(place_ids):
    exist_orgs = read_mincult_ors_from_file()
    ignore_orgs = read_mincult_ignored_orgs()
    added_orgs = dict()
    error_orgs = list()
    for place_id in place_ids:
        if place_id in exist_orgs.keys() or place_id in ignore_orgs:
            print("skip", place_id)
            continue
        try:
            prepared_org = prepare_org(mincult_api.get_org_from_mincult(place_id)["place"])
        except Exception as e:
            print(e)
            error_orgs.append(place_id)
            continue
        evendate_url, evendate_id = post_org_to_evendate(prepared_org)
        if evendate_url is not None:
            added_orgs[place_id] = evendate_id
            write_mincult_orgs_to_file({place_id: evendate_id}, exist_orgs)
        else:
            error_orgs.append(place_id)
    parse_logger.fast_send_email("Added orgs from mincult " + str(len(added_orgs)),
                                 prepare_msg_text(added_orgs, error_orgs))


def update_orgs(place_ids):
    updated_orgs = dict()
    error_orgs = list()
    for place_id, evendate_id in place_ids.items():
        try:
            prepared_org = prepare_org(mincult_api.get_org_from_mincult(place_id)["place"])
        except Exception as e:
            print(e)
            error_orgs.append(place_id)
            continue
        evendate_url, evendate_id = update_org_in_evendate(evendate_id, prepared_org)
        if evendate_url is not None:
            updated_orgs[place_id] = evendate_id
        else:
            error_orgs.append(place_id)
    parse_logger.fast_send_email("Updated orgs from mincult " + str(len(updated_orgs)),
                                 prepare_update_msg_text(updated_orgs, error_orgs))


def prepare_msg_text(done_dict, error_list):
    text = ""
    for min_id, even_id in done_dict.items():
        text += "ADDED min_id:{} | evendate_id:{}\r\n".format(min_id, even_id)
    for min_id in error_list:
        text += "ERROR min_id:{}\r\n".format(min_id)
    return text


def prepare_update_msg_text(done_dict, error_list):
    text = ""
    for min_id, even_id in done_dict.items():
        text += "UPDATED min_id:{} | evendate_id:{}\r\n".format(min_id, even_id)
    for min_id in error_list:
        text += "ERROR min_id:{}\r\n".format(min_id)
    return text


def get_evendate_city_id_from_mincult(locale_id):
    return {2579: 1,  # msk
            1641: 2,  # Saratov
            205: 3,  # Sevastopol
            203: 4,  # piter
            739: 5,  # novosib
            2002: 6,  # ekb
            1310: 7,  # nizh novgorod
            1722: 8,  # kazan
            2591: 9,  # Chelyabinsk
            805: 10,  # Omsk
            1572: 11,  # Samara
            1643: 12,  # Rostov-on-Don
            1170: 13,  # Ufa
            718: 14,  # Krasnoyarsk
            1495: 15,  # Perm
            552: 16,  # Voronezh
            2568: 17,  # Volgograd
            1449: 18,  # Krasnodar
            2196: 19,  # Нальчик
            1469: 20,  # Сочи
            2038: 21,  # Калининград
            }[locale_id]


def collect_orgs_from_events(locales, categories):
    orgs = set()
    for locale in locales:
        for category in categories:
            res_json = mincult_api.get_events_in_category(category, locale)
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


def bulk_update_orgs():
    def read_update_orgs_from_file():
        exist_orgs = dict()
        file_name = "update.txt"
        try:
            with open(file_name) as f:
                for line in f:
                    date, min_id, even_id = line.strip().split(' ')
                    exist_orgs[int(min_id)] = int(even_id)
        except IOError:
            pass
        return exist_orgs

    org_ids = read_update_orgs_from_file()
    update_orgs(org_ids)
