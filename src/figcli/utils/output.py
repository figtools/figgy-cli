from figcli.config.style.terminal_factory import TerminalFactory

MAX_LINE_LENGTH = 42


class Output:

    def __init__(self, colors_enabled=False):
        self.c = TerminalFactory(colors_enabled).instance().get_colors()

    def notify(self, message: str):
        lines = []

        while len(message) > MAX_LINE_LENGTH or not lines:
            split_idx = MAX_LINE_LENGTH
            while message[split_idx] != " ":
                split_idx = split_idx - 1

            lines.append(message[:split_idx])
            message = message[split_idx + 1:]

        longest_line = max([len(line) for line in lines])
        dashes = ["-" for i in range(0, longest_line + 8)]
        dash_str = "".join(dashes)

        print(f'{self.c.fg_yl}{dash_str}{self.c.rs}')
        for line in lines:
            print(f'    {self.c.fg_bl}{line}{self.c.rs}    ')
        print(f'{self.c.fg_yl}{dash_str}{self.c.rs}')
