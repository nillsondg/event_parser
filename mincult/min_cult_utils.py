def prepare_location(addr_json):
    place = addr_json
    region = place["region"]["name"]
    try:
        city = place["city"]["type"] + place["city"]["name"]
    except KeyError:
        city = place["city"]["name"]

    try:
        street = place["street"]["type"] + place["street"]["name"]
    except KeyError:
        street = place["street"]["name"]

    try:
        house = place["house"]["type"] + place["house"]["name"]
    except KeyError:
        try:
            house = place["house"]["name"]
        except KeyError:
            house = ""

    return "{}, {}, {}, {}".format(region, city, street, house)
