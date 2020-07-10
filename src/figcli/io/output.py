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
            if split_idx == MAX_LINE_LENGTH:
                while message[split_idx] != " " and " " in message and len(message) > MAX_LINE_LENGTH:
                    split_idx = split_idx - 1

                lines.append(message[:split_idx])
                message = message[split_idx + 1:]
            else:
                lines.append(message)
                message = ''

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

    def h2(self, dash_color, text_color):
        """
        Heading 2 prints.
        """
        print(f'{dash_color}{self.dashes}{self.color.rs}')
        for line in self.lines:
            print(f'    {text_color}{line}{self.color.rs}    ')
        print(f'{dash_color}{self.dashes}{self.color.rs}')

    def p(self, text_color):
        """
        Standard colored prints - 'p' is for 'paragraph' like in html/css
        """
        print(f"{text_color}{self.message}{self.color.rs}")

    def notify_h2(self):
        self.h2(self.color.fg_yl, self.color.fg_bl)

    def warn_h2(self):
        self.h2(self.color.fg_yl, self.color.fg_yl)

    def success_h2(self):
        self.h2(self.color.fg_gr, self.color.fg_bl)

    def error_h2(self):
        self.h2(self.color.fg_yl, self.color.fg_rd)

    def notify(self):
        self.p(self.color.fg_bl)

    def warn(self):
        self.p(self.color.fg_yl)

    def success(self):
        self.p(self.color.fg_bl)

    def error(self):
        self.p(self.color.fg_rd)


class Output:
    """
    Contains utilities around IO
    """

    def __init__(self, colors_enabled=False):
        self.c = TerminalFactory(colors_enabled).instance().get_colors()

    def notify_h2(self, message: str):
        Notification(message=message, color=self.c).notify_h2()

    def warn_h2(self, message: str):
        Notification(message=message, color=self.c).warn_h2()

    def success_h2(self, message: str):
        Notification(message=message, color=self.c).success_h2()

    def error_h2(self, message: str):
        Notification(message=message, color=self.c).error_h2()

    def notify(self, message: str):
        Notification(message=message, color=self.c).notify()

    def warn(self, message: str):
        Notification(message=message, color=self.c).warn()

    def success(self, message: str):
        Notification(message=message, color=self.c).success()

    def error(self, message: str):
        Notification(message=message, color=self.c).error()

    def print(self, message: str):
        print(message)

