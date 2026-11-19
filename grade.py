# One shared look for every photo: clean contrast, a touch of warmth (matches the sand/cream palette),
# lifted colour and gentle sharpening. Mild by design so already-good shots are not over-cooked.
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
def grade(im, sharpen=False):
    im = im.convert('RGB')
    ac = ImageOps.autocontrast(im, cutoff=(0.4, 0.4), preserve_tone=True)
    im = Image.blend(im, ac, 0.6)                       # de-haze, but only part-way
    im = ImageEnhance.Color(im).enhance(1.10)
    im = ImageEnhance.Contrast(im).enhance(1.04)
    r, g, b = im.split()                                # slight warm shift, same for all photos
    r = r.point(lambda v: min(255, int(v * 1.025 + 1)))
    b = b.point(lambda v: int(v * 0.975))
    im = Image.merge('RGB', (r, g, b))
    if not sharpen:                                     # phone shots are already sharp; sharpening only bloats them
        return im
    rad = 0.8 if im.width <= 800 else 1.0
    return im.filter(ImageFilter.UnsharpMask(radius=rad, percent=40, threshold=4))
