import config
import json
import requests
import parse_logger
import mimetypes
import base64
from bs4 import BeautifulSoup
from evendate_api import post_org_to_evendate


def get_org_from_mincult(place_id):
    print("getting org from mincult for", str(place_id))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    url = "https://all.culture.ru/api/2.3/places/{place_id}"

    res_url = url.format(place_id=place_id, headers=headers)
    r = requests.get(res_url)
    print(r.status_code, r.reason)
    if r.status_code == 200:
        org_json = json.loads(r.content.decode('utf-8'))
        return org_json


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

    site_url = org_desc["contacts"]["website"]
    vk_url = org_desc["contacts"]["vkontakte"]
    facebook_url = org_desc["contacts"]["facebook"]

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
           "email": config.MY_EMAIL
           }
    return org

# todo create in cycle and post result
# post_org_to_evendate(prepare_org(get_org_from_mincult(9757)["place"]))
