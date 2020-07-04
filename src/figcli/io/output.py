from dataclasses import dataclass
from typing import Tuple, List

from figcli.config.style.color import Color
from figcli.config.style.terminal_factory import TerminalFactory

MAX_LINE_LENGTH = 52


class Notification:
    message: str
    color: Color

    def __init__(self, message: str, color: Color):
        self.message = message
        self.color = color
        self._lines = None
        self._dashes = None

    @property
    def lines(self):
        if self._lines:
            return self._lines

        message = self.message
        lines = []
        while len(message) > 0 or not lines:
            split_idx = min(MAX_LINE_LENGTH, len(message) - 1)
            print()
            while message[split_idx] != " " and " " in message and len(message) > MAX_LINE_LENGTH:
                split_idx = split_idx - 1

            lines.append(message[:split_idx])
            message = message[split_idx + 1:]

        self._lines = lines
        return self._lines

    @property
    def dashes(self):
        if self._dashes:
            return self._dashes

        lines = self.lines
        longest_line = max([len(line) for line in lines])
        dashes = ["-" for i in range(0, longest_line + 8)]
        dash_str = "".join(dashes)

        self._dashes = dash_str
        return self._dashes

    def print_notification(self, dash_color, text_color):
        print(f'{dash_color}{self.dashes}{self.color.rs}')
        for line in self.lines:
            print(f'    {text_color}{line}{self.color.rs}    ')
        print(f'{dash_color}{self.dashes}{self.color.rs}')

    def notify(self):
        self.print_notification(self.color.fg_yl, self.color.fg_bl)

    def warn(self):
        self.print_notification(self.color.fg_yl, self.color.fg_yl)

    def success(self):
        self.print_notification(self.color.fg_gr, self.color.fg_bl)

    def error(self):
        self.print_notification(self.color.fg_yl, self.color.fg_rd)


class Output:
    """
    Contains utilities around IO
    """

    def __init__(self, colors_enabled=False):
        self.c = TerminalFactory(colors_enabled).instance().get_colors()

    def notify(self, message: str):
        Notification(message=message, color=self.c).notify()

    def warn(self, message: str):
        Notification(message=message, color=self.c).warn()

    def success(self, message: str):
        Notification(message=message, color=self.c).success()

    def error(self, message: str):
        Notification(message=message, color=self.c).error()
