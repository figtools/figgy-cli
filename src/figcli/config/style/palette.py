from typing import Tuple, Any

from sty import fg, FgRegister, rs


class Palette:
    # Default palette colors
    BLUE: Tuple = (5, 156, 205)
    GREEN: Tuple = (51, 222, 136)
    RED: Tuple = (240, 70, 87)
    YELLOW: Tuple = (249, 149, 72)
    ORANGE: Tuple = (232, 149, 39)

    BL_HX: str = '#%02x%02x%02x' % BLUE
    GR_HX: str = '#%02x%02x%02x' % GREEN
    RD_HX: str = '#%02x%02x%02x' % RED
    YL_HX: str = '#%02x%02x%02x' % YELLOW
    OG_HX: str = '#%02x%02x%02x' % ORANGE

    def __init__(self, blue=BLUE, green=GREEN, red=RED, yellow=YELLOW, orange=ORANGE):
        if isinstance(blue, Tuple):
            fg.blue = fg(*blue)
            fg.green = fg(*green)
            fg.red = fg(*red)
            fg.yellow = fg(*yellow)
            fg.orange = fg(*orange)

            # Prompt Toolkit HEX colors
            self.bl: str = '#%02x%02x%02x' % blue
            self.gr: str = '#%02x%02x%02x' % green
            self.rd: str = '#%02x%02x%02x' % red
            self.yl: str = '#%02x%02x%02x' % yellow
            self.og: str = '#%02x%02x%02x' % orange

        else:
            fg.blue = fg(blue)
            fg.green = fg(green)
            fg.red = fg(red)
            fg.yellow = fg(yellow)
            fg.orange = fg(orange)

            # Prompt Toolkit HEX colors
            self.bl: str = '#%02x%02x%02x' % Palette.BLUE
            self.gr: str = '#%02x%02x%02x' % Palette.GREEN
            self.rd: str = '#%02x%02x%02x' % Palette.RED
            self.yl: str = '#%02x%02x%02x' % Palette.YELLOW
            self.og: str = '#%02x%02x%02x' % Palette.ORANGE

        self.fg_bl: FgRegister = fg.blue
        self.fg_gr: FgRegister = fg.green
        self.fg_rd: FgRegister = fg.red
        self.fg_yl: FgRegister = fg.yellow
        self.fg_og: FgRegister = fg.orange
        self.rs = rs.all
