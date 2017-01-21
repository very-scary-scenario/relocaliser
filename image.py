import cairocffi as cairo
from cairosvg import svg2png
from io import BytesIO
import os

# Yes going through cairo to a png and then back into cairo again
# But all SVG libraries are hot garbage and most don't work at all
# This one at least works, but doesn't render to an object, only a file
# So we're stuck with the roundtrip.

# Set of languages for which we have a flag
known_langs = set([filename[:-4] for filename in os.listdir("flags")
                   if filename != "unknown.svg"])

def generate_image(steps, filename):
    # Set all the constants!
    # Possibly a better way to achieve this?
    top_margin = 75
    left_margin = 100
    right_margin = 150
    bottom_margin = 100
    step = 100

    width = 800
    height = step * len(steps) + bottom_margin

    background_colour = (0, 0, 0)

    font_size = 48
    flag_height = 64 # TODO: Work out how to read this from the file
    flag_width = 64 # ditto

    font_name = "Helvetica"
    font_slant = cairo.FONT_SLANT_NORMAL
    font_weight = cairo.FONT_WEIGHT_NORMAL
    font_colour = (1, 1, 1)

    text_indent = 36
    text_hposition = left_margin + flag_width + text_indent
    text_width = width - text_hposition - right_margin

    image = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    context = cairo.Context(image)

    # Create the background
    context.set_source_rgb(*background_colour)

    # Need to leave one pixel transparent to prevent Twitter JPEGing us
    context.rectangle(0, 0, width, height - 1)
    context.fill()
    context.rectangle(0, height - 1, width - 1, 1)
    context.fill()
    context = cairo.Context(image)
    
    for i, (lang, title) in enumerate(steps):
        if lang in known_langs:
            flag = "flags/" + lang + ".svg"
        else:
            flag = "flags/unknown.svg"
        flag = BytesIO(svg2png(url=flag, ))
        flag = cairo.ImageSurface.create_from_png(flag)
        context.set_source_surface(flag, left_margin, top_margin + step * i)
        context.paint()
        
        # Here we recreate the context because Cairo
        # gives us no text otherwise
        # If there's an easier way I don't know it.
        context = cairo.Context(image)
        context.set_source_rgb(*font_colour)

        # We will need to generalise this if the Yandex API ever supports CJK
        context.select_font_face(font_name, font_slant, font_weight)
        context.set_font_size(font_size)
        (title_dx, title_dy, 
         title_width, title_height, *_) = context.text_extents(title)
        if title_width > text_width:
            context.set_font_size(font_size * text_width / title_width)

        text_vpos = (top_margin + step * i + flag_height / 2
                     - title_dy - title_height / 2)
        context.move_to(text_hposition - title_dx, text_vpos)
        context.show_text(title)
        
    image.write_to_png(filename)


if __name__ == "__main__":
    steps = [("ru", "ру́сский язы"),
             ("ja", "こんにちは"),
             ("en", "Done!")]
    generate_image(steps, "test.png")
