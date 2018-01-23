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
    thumb.save(img_crop_raw, format='PNG')
    return img_crop_raw.getvalue()
