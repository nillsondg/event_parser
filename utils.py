def crop_img_to_16x9(img_raw):
    from PIL import Image
    from io import BytesIO
    image = Image.open(BytesIO(img_raw))
    width = image.size[0]
    height = image.size[1]

    aspect = width / float(height)

    ideal_width = 1280
    ideal_height = 720

    ideal_aspect = ideal_width / float(ideal_height)

    if aspect > ideal_aspect:
        # Then crop the left and right edges:
        new_width = int(ideal_aspect * height)
        offset = (width - new_width) / 2
        resize = (offset, 0, width - offset, height)
    else:
        # ... crop the top and bottom:
        new_height = int(width / ideal_aspect)
        offset = (height - new_height) / 2
        resize = (0, offset, width, height - offset)

    thumb = image.crop(resize).resize((ideal_width, ideal_height), Image.ANTIALIAS)
    img_crop_raw = BytesIO()
    thumb.convert('RGB').save(img_crop_raw, format='PNG')
    return img_crop_raw.getvalue()


# todo remove evendate context
def get_img(url):
    import requests
    import mimetypes
    import base64
    res = requests.get(url, allow_redirects=True)
    content_type = res.headers['content-type']
    extension = mimetypes.guess_extension(content_type)
    if extension == ".jpe":
        extension = ".jpeg"
    if extension is None and content_type == 'image/jpg':
        extension = ".jpg"
    img = "data:{};base64,".format(content_type) + base64.b64encode(crop_img_to_16x9(res.content)).decode("utf-8")
    filename = "image" + extension
    return img, filename


def get_default_img(img_name="evendate.png", ext="png"):
    import base64
    with open("images/" + img_name, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    image_horizontal = "data:image/{};base64,".format(ext) + encoded_string.decode("utf-8")
    return image_horizontal, img_name


def prepare_img(img, extension):
    import base64
    img = "data:{};base64,".format(extension) + base64.b64encode(img).decode("utf-8")
    filename = "image." + extension
    return img, filename
