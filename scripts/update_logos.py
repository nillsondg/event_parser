from evendate_api import *
from utils import prepare_img
from logo_generator import generate_logo

update_ids = []

for org_id in update_ids:
    org = get_org(org_id, "site_url,description")[0]
    if org is None:
        print("error with org id", org_id)
    logo, logo_filename = prepare_img(generate_logo(org["short_name"]), "png")
    org["logo"] = logo
    org["logo_filename"] = logo_filename
    url = update_org_in_evendate(org_id, org)[0]
    if url is None:
        print("error update org id", org_id)
