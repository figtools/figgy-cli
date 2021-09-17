from figcli.config.style.color import Color
from figcli.config.style.terminal_factory import TerminalFactory

MAX_LINE_LENGTH = 52


class OutUtils:
    @staticmethod
    def to_lines(text: str, max_length):
        """Break a string along word boundaries into lines.
           DO NOT PUT PRINT STATEMENTS IN HERE (Breaks list, and it's dumb)
        """
        if not text:
            return []

        lines = []
        while len(text) > 0 or not lines:
            split_idx = min(max_length, len(text) - 1)
            if split_idx == max_length:
                while text[split_idx] != " " and " " in text and len(text) > max_length:
                    split_idx = split_idx - 1

                lines.append(text[:split_idx])
                text = text[split_idx + 1:]
            else:
                lines.append(text)
                text = ''

        return lines


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

        self._lines = OutUtils.to_lines(self.message, MAX_LINE_LENGTH)
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

    def h2(self, dash_color, text_color, accent_color):
        """
        Heading 2 prints.
        Text color = all text will be in this color except [[test contained in brackets]] which will be accent_color.
        """
        print(f'\n{dash_color}{self.dashes}{self.color.rs}')
        for line in self.lines:
            line = line.replace("[[", f'{self.color.rs}{accent_color}').replace("]]", f'{self.color.rs}{text_color}')
            print(f'    {text_color}{line}{self.color.rs}    ')
        print(f'{dash_color}{self.dashes}{self.color.rs}')

    def p(self, text_color, accent_color):
        """
        Standard colored prints - 'p' is for 'paragraph' like in html/css
        Text color = all text will be in this color except [[test contained in brackets]] which will be accent_color.
        """
        self.message = self.message \
            .replace("[[", f'{self.color.rs}{accent_color}') \
            .replace("]]", f'{self.color.rs}{text_color}')

        print(f"{text_color}{self.message}{self.color.rs}")

    def notify_h2(self):
        self.h2(self.color.fg_yl, self.color.fg_bl, self.color.fg_yl)

    def warn_h2(self):
        self.h2(self.color.fg_yl, self.color.fg_yl, self.color.fg_bl)

    def success_h2(self):
        self.h2(self.color.fg_gr, self.color.fg_bl, self.color.fg_gr)

    def error_h2(self):
        self.h2(self.color.fg_yl, self.color.fg_rd, self.color.fg_bl)

    def notify(self):
        self.p(self.color.fg_bl, self.color.fg_yl)

    def warn(self):
        self.p(self.color.fg_yl, self.color.fg_bl)

    def success(self):
        self.p(self.color.fg_gr, self.color.fg_bl)

    def error(self):
        self.p(self.color.fg_rd, self.color.fg_yl)

    def print(self):
        self.p('', self.color.fg_bl)

    def print_h2(self):
        self.h2('', '', '')


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
        Notification(message=message, color=self.c).print()

    def print_h2(self, message: str):
        Notification(message=message, color=self.c).print_h2()
