import config
import requests
import parse_logger
import mimetypes
import base64
from bs4 import BeautifulSoup
from evendate_api import post_org_to_evendate
import datetime
import mincult_api


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
        "Дворцы культуры и клубы": "Клубы и Бары",
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

    def prepare_description(description):
        if len(description) > 250:
            return description[:250]
        return description

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

    def prepare_location(org_json):
        place = org_json["address"]
        region = place["region"]["name"]
        city = place["city"]["type"] + " " + place["city"]["name"]
        street = place["street"]["type"] + " " + place["street"]["name"]
        house = place["house"]["type"] + " " + place["house"]["name"]

        return "{}, {}, {}, {}".format(region, city, street, house)

    default_address = prepare_location(org_desc)

    type_id = get_type(convert_type_to_evendate(org_desc["category"]["name"]))

    def prepare_link(place_id):
        return "https://all.culture.ru/public/places/{}".format(place_id)

    detail_info_url = prepare_link(org_desc["_id"])

    def prepare_img_link():
        "https://all.culture.ru/uploads/{name}".format(name=org_desc["image"]["name"])

    locale = org_desc["locale"]["_id"]
    try:
        city_id = get_evendate_city_id_from_mincult(locale)
    except KeyError:
        print("can't get evendate city_id for", locale)
        raise ValueError("illegal locale_id " + str(locale))

    def get_img(url):
        img_raw = requests.get(url, allow_redirects=True)
        content_type = img_raw.headers['content-type']
        extension = mimetypes.guess_extension(content_type)
        if extension == ".jpe":
            extension = ".jpeg"
        img = "data:{};base64,".format(content_type) + base64.b64encode(img_raw.content).decode("utf-8")
        filename = "image" + extension
        return img, filename

    def get_default_img(img_name="evendate.png", ext="png"):
        with open("images/" + img_name, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        image_horizontal = "data:image/{};base64,".format(ext) + encoded_string.decode("utf-8")
        return image_horizontal, img_name

    try:
        img, img_filename = get_img(prepare_img_link())
    except Exception:
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


def write_orgs_to_file(org_dict, exist_org_dict):
    file_name = "orgs.txt"
    f = open(file_name, 'a+')
    # todo need contract cause min_id input is int, but ouput can be str!!!
    for min_id, even_id in org_dict.items():
        if min_id not in exist_org_dict.keys():
            f.write(datetime.datetime.now().strftime("%y.%m.%d|%H:%M:%S ") + min_id + " " + even_id + "\n")
            print("added " + min_id)
    f.close()


def add_org(place_ids):
    exist_orgs = parse_logger.read_ors_from_file()
    added_orgs = dict()
    error_orgs = list()
    for place_id in place_ids:
        # todo temp to str
        if str(place_id) in exist_orgs.keys():
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
        else:
            error_orgs.append(place_id)
    write_orgs_to_file(added_orgs, exist_orgs)
    parse_logger.fast_send_email("Added orgs from mincult " + str(len(added_orgs)),
                                 prepare_msg_text(added_orgs, error_orgs))


def prepare_msg_text(done_dict, error_list):
    text = ""
    for min_id, even_id in done_dict.items():
        text += "ADDED min_id:{} | evendate_id:{}\r\n".format(min_id, even_id)
    for min_id in error_list:
        text += "ERROR min_id:{}\r\n".format(min_id)
    return text


def get_evendate_city_id_from_mincult(locale_id):
    return {2579: 1,  # msk
            205: 3,  # sevastopol
            203: 4,  # piter
            739: 5,  # novosib
            2002: 6,  # ekb
            1310: 7,  # nizh novgorod
            1722: 8,  # kazan
            }[locale_id]


def collect_orgs_from_events():
    # msk, piter, novosib, ekb, nizh novgorod, kazan, sevastopol
    locales = [2579, 203, 739, 2002, 1310, 1722, 205]
    categories = ["kinoteatry", "koncertnye-ploshchadki", "kulturnoe-nasledie",
                  "muzei-i-galerei", "parki", "teatry"]
    # "cirki", "dvorcy-kultury-i-kluby", "pamyatniki", "obrazovatelnye-uchrezhdeniya"
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
    org_ids = collect_orgs_from_events()
    add_org(org_ids)
