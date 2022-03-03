from io import BytesIO
import os
from typing import List, Tuple

from argostranslate.translate import Language
import cairocffi as cairo
import pangocairocffi as pangocairo
import pangocffi as pango
from cairosvg import svg2png

# Yes going through cairo to a png and then back into cairo again
# But all SVG libraries are hot garbage and most don't work at all
# This one at least works, but doesn't render to an object, only a file
# So we're stuck with the roundtrip.

# Set of languages for which we have a flag
known_langs = set([filename[:-4] for filename in os.listdir("flags")
                   if filename != "unknown.svg"])

PANGO_SCALE = pango.units_from_double(1)

RESCALE_WIDTH = True
TRIM_EXCESS_WIDTH = False
FONT_PROPS = {
    'name': 'FreeSans',
    'colour': (1, 1, 1),
    'default_size': 48,
    'max_aspect_ratio': 0.7,
    'min_size': 8,
    'rescale_text': False
}


def get_text(
        context: cairo.Context,
        text: str,
        text_width,
        max_aspect_ratio: float = FONT_PROPS['max_aspect_ratio'],
        font_size: float = FONT_PROPS['default_size']
) -> pango.Layout:
    layout = pangocairo.create_layout(context)
    desc = pango.FontDescription()
    desc.set_family(FONT_PROPS['name'])
    desc.set_size(font_size * PANGO_SCALE)
    layout.set_font_description(desc)

    layout.set_width(text_width * PANGO_SCALE)
    layout.set_wrap(pango.WrapMode.WORD)
    layout.set_markup(text)
    layout.set_alignment(pango.Alignment.LEFT)

    font_scale_step = 0.9
    while FONT_PROPS['rescale_text'] and (
            layout.get_extents()[1].height
            > layout.get_extents()[1].width * max_aspect_ratio
    ) and (
            (font_size := font_scale_step * font_size) >=
            FONT_PROPS['min_size']
    ):
        desc.set_size(int(font_size * PANGO_SCALE))
        layout.set_font_description(desc)

    # Ensure that RTL text doesn't get a big gap
    layout.set_width(layout.get_extents()[1].width)
    return layout


def place_text(
        image: cairo.surfaces.ImageSurface,
        text: str,
        left_edge_distance: float,
        top_edge_distance: float,
        width: float
) -> None:
    context = cairo.Context(image)
    layout = get_text(context, text, width)
    ink_box, log_box = layout.get_extents()

    text_width, text_height = (log_box.width / PANGO_SCALE,
                               log_box.height / PANGO_SCALE)

    context.move_to(left_edge_distance, top_edge_distance)
    context.set_source_rgb(*FONT_PROPS['colour'])
    pangocairo.show_layout(context, layout)
    context.fill()

    return text_width, text_height


def place_flag(
        image: cairo.surfaces.ImageSurface,
        lang: Language,
        left_edge_distance: float,
        top_edge_distance: float
) -> None:
    context = cairo.Context(image)
    if lang.code in known_langs:
        flag = "flags/" + lang.code + ".svg"
    else:
        flag = "flags/unknown.svg"
    flag = BytesIO(svg2png(url=flag, ))
    flag = cairo.ImageSurface.create_from_png(flag)
    context.set_source_surface(flag, left_edge_distance, top_edge_distance)
    context.paint()


def get_text_layouts(
        steps: List[Tuple[Language, str]],
        text_width: float
) -> List[pango.Layout]:
    buf_width, buf_height = 50, 50
    buffer = cairo.ImageSurface(cairo.FORMAT_ARGB32, buf_width, buf_height)
    context = cairo.Context(buffer)

    return [get_text(context, text, text_width) for _, text in steps]


def get_full_text_height(
        steps: List[Tuple[Language, str]],
        text_width: float
) -> float:
    layouts = get_text_layouts(steps, text_width)
    heights = [layout.get_extents()[1].height for layout in layouts]
    return sum(heights) / PANGO_SCALE


def get_max_text_width(
        steps: List[Tuple[Language, str]],
        text_area_width: float
) -> float:
    layouts = get_text_layouts(steps, text_area_width)
    widths = [layout.get_extents()[1].width for layout in layouts]
    return max(widths) / PANGO_SCALE


def get_image_dimensions(
        steps: List[Tuple[Language, str]],
        text_hposition: float,
        right_margin: float,
        top_margin: float,
        bottom_margin: float,
        row_pad: float
) -> Tuple[float, float]:
    max_aspect_ratio = 1.5
    width_step = 50

    # Start one step below the actual width to avoid having to fudge
    width = 800 - width_step
    height = None

    while (
            (height is None)
            or (RESCALE_WIDTH and height / width > max_aspect_ratio)
    ):
        width = int(width + width_step)
        text_width = width - text_hposition - right_margin
        height = int(
            get_full_text_height(steps, text_width) + (len(steps) - 1) * row_pad
            + top_margin + bottom_margin
        )

    if TRIM_EXCESS_WIDTH:
        # Currently this does not work, as setting the width to the one
        # reported by Cairo causes the text to actually not fit and wrap
        # longer.
        # TODO: Make this work to avoid unsightly black borders.
        text_width = get_max_text_width(steps, text_width)
        width = int(text_width + text_hposition + right_margin + 1)
    return width, height


def generate_image(steps: List[Tuple[Language, str]], filename: str) -> None:
    # Set all the constants!
    # Possibly a better way to achieve this?
    top_margin = 75
    left_margin = 100
    right_margin = 70
    bottom_margin = 100
    row_pad = 40

    width = 800

    background_colour = (0, 0, 0)

    flag_height = 64  # TODO: Work out how to read this from the file
    flag_width = 64  # ditto

    text_indent = 36
    text_hposition = left_margin + flag_width + text_indent

    width, height = get_image_dimensions(
        steps, text_hposition, right_margin, top_margin, bottom_margin, row_pad
    )
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

    vertical_position = top_margin

    for lang, title in steps:
        _, text_height = place_text(
            image, title, text_hposition, vertical_position, text_width
        )
        flag_top_distance = (
            vertical_position + text_height / 2 - flag_height / 2
        )
        place_flag(image, lang, left_margin, flag_top_distance)
        vertical_position += text_height + row_pad

    image.write_to_png(filename)


if __name__ == "__main__":
    from argostranslate.translate import get_installed_languages
    from random import choice

    phrases = [
        "ру́сский язы",
        "こんにちは",
        "This entry is too long to fit cleanly on one line, and should be wrapped",
        "안녕하세요",
        "مرحبًا",
        "Done!",
    ]
    generate_image([(
        choice(get_installed_languages()), phrases[i % len(phrases)]
    ) for i in range(10)], "test.png")
