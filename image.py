import os
from typing import List, Tuple

from argostranslate.translate import Language
from selenium.webdriver import Chrome as WebDriver, ChromeOptions as Options

KNOWN_LANGS = set([
    filename[:-4] for filename in os.listdir("flags") if filename != "unknown.svg"
])

WIDTH = 800
STEP_SIZE = 100
VERTICAL_MARGIN = 175

HERE = os.path.realpath(os.path.join(__file__, '..'))


def _generate_image(driver: WebDriver, steps: List[Tuple[Language, str]], filename: str) -> None:
    driver.set_window_size(WIDTH, STEP_SIZE * len(steps) + VERTICAL_MARGIN)
    driver.get(f'file:{os.path.join(HERE, "summary.html")}')
    driver.execute_script("""ingestSteps(["hello", "there"])""")

    with open(filename, 'wb') as png:
        png.write(driver.get_screenshot_as_png())


def generate_image(steps: List[Tuple[Language, str]], filename: str) -> None:
    options = Options()
    options.headless = True
    try:
        driver = WebDriver(options=options)
        _generate_image(driver, steps, filename)
    finally:
        driver.quit()


if __name__ == "__main__":
    from argostranslate.translate import get_installed_languages
    from random import choice

    phrases = [
        "ру́сский язы",
        "こんにちは",
        "안녕하세요",
        "Done!",
    ]
    generate_image([(
        choice(get_installed_languages()), phrases[i % len(phrases)]
    ) for i in range(10)], "test.png")
