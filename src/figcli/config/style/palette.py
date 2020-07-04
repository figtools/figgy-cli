from dataclasses import dataclass
from sty import fg, FgRegister


@dataclass
class Palette:
    # Default pallete colors
    BLUE = (52, 213, 235)
    GREEN = (51, 222, 136)
    RED = (240, 70, 87)
    YELLOW = (240, 240, 70)
    ORANGE = (232, 149, 39)

    def __init__(self, blue=BLUE, green=GREEN, red=RED, yellow=YELLOW, orange=ORANGE):
        self.fg_bl: FgRegister = fg(*blue)
        self.fg_gr: FgRegister = fg(*green)
        self.fg_rd: FgRegister = fg(*red)
        self.fg_yl: FgRegister = fg(*yellow)
        self.fg_og: FgRegister = fg(*orange)

        # Prompt Toolkit HEX colors
        self.bl: str = '#%02x%02x%02x' % blue
        self.gr: str = '#%02x%02x%02x' % green
        self.rd: str = '#%02x%02x%02x' % red
        self.yl: str = '#%02x%02x%02x' % yellow
        self.og: str = '#%02x%02x%02x' % orange

        self.rs = fg.rs