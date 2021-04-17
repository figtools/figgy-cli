import curses
import weakref
from typing import Callable

import npyscreen
from figgy.models.run_env import RunEnv
from npyscreen import BoxTitle, MultiLine, TextCommandBox
from prompt_toolkit.completion import WordCompleter

from figcli.commands.config.get import Get
from figcli.commands.config_context import ConfigContext
from figcli.commands.types.config import ConfigCommand
from figcli.io.output import OutUtils
from figcli.svcs.config import ConfigService, ParameterUndecryptable
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker
from figcli.utils.utils import *
from figcli.views.rbac_limited_config import RBACLimitedConfigView

QUIT_CODES = [':q', 'quit', 'exit', ":wq", "q", "/quit", "/q"]


class List(ConfigCommand):

    def __init__(self, config_view: RBACLimitedConfigView, cfg: ConfigService, config_completer_init: WordCompleter,
                 colors_enabled: bool, config_context: ConfigContext, get: Get):
        super().__init__(list_com, colors_enabled, config_context)
        self._view = config_view
        self._cfg = cfg
        self._config_completer = config_completer_init
        self._get = get
        self._utils = Utils(colors_enabled)

    def _list(self):
        app = ListApp(self._view, self._cfg, self.context.run_env)
        app.run()

    @VersionTracker.notify_user
    @AnonymousUsageTracker.track_command_usage
    def execute(self):
        self._list()


class ActionControllerSearch(npyscreen.ActionControllerSimple):
    """
    Adds filter functionality to the select box at the bottom.
    """

    def create(self):
        self.add_action('^/.*', self.set_search, True)

    def set_search(self, command_line, widget_proxy, live):
        self.parent.value.set_filter(command_line[1:])
        self.parent.wMain.values = self.parent.value.get()
        self.parent.wMain.display()


class SelectBox(TextCommandBox):
    """
    Select box at the bottom of the list view.
    """

    def __init__(self, screen, *args, **keywords):
        super().__init__(screen, *args, **keywords)
        self.value = "/"

    def h_execute_command(self, *args, **keywords):
        for val in QUIT_CODES:
            val == self.value and exit(0)

        if self.history:
            self._history_store.append(self.value)
            self._current_history_index = False
        self.parent.action_controller.process_command_complete(self.value, weakref.proxy(self))
        self.value = ''


class SelectedValueBox(BoxTitle):
    """Creates box around Value"""
    _contained_widget = MultiLine


class LegendBox(BoxTitle):
    """Creates box around Legend"""
    _contained_widget = MultiLine


class SelectableMultiline(MultiLine):
    """
    Main list-view display box that allows users to select options
    """

    def set_select_callback(self, callback: Callable):
        self.select_callback = callback

    def h_select(self, ch):
        self.value = self.cursor_line
        self.select_callback(self.values[self.value])

        if self.select_exit:
            self.editing = False
            self.how_exited = True

    def set_up_handlers(self):
        super(MultiLine, self).set_up_handlers()
        self.handlers.update({
            curses.KEY_UP: self.h_cursor_line_up,
            ord('s'): self.h_select,
            ord('k'): self.h_cursor_line_up,
            curses.KEY_LEFT: self.h_cursor_line_up,
            curses.KEY_DOWN: self.h_cursor_line_down,
            ord('j'): self.h_cursor_line_down,
            curses.KEY_RIGHT: self.h_cursor_line_down,
            'd': self.h_cursor_page_down,
            'u': self.h_cursor_page_up,
            curses.ascii.TAB: self.h_exit_down,
            curses.ascii.NL: self.h_select_exit,
            curses.KEY_HOME: self.h_cursor_beginning,
            curses.KEY_END: self.h_cursor_end,
            ord('g'): self.h_cursor_beginning,
            ord('G'): self.h_cursor_end,
            ord('x'): self.h_select,
            curses.ascii.SP: self.h_select,
            curses.ascii.ESC: self.h_exit_escape,
            curses.ascii.CR: self.h_select_exit,
        })

        if self.allow_filtering:
            self.handlers.update({
                ord('F'): self.h_set_filter,
                ord('L'): self.h_clear_filter,
                ord('n'): self.move_next_filtered,
                ord('N'): self.move_previous_filtered,
                ord('p'): self.move_previous_filtered,

            })

        if self.exit_left:
            self.handlers.update({
                curses.KEY_LEFT: self.h_exit_left
            })

        if self.exit_right:
            self.handlers.update({
                curses.KEY_RIGHT: self.h_exit_right
            })

        self.complex_handlers = [
            # (self.t_input_isprint, self.h_find_char)
        ]


class FiggyListForm(npyscreen.FormMuttActive):
    BUFFER = 1
    BUFFER_LEFT = 3
    LEGEND = [
        "",
        "< TAB > - Swap between Select / Filter",
        "< s, ENTER > - Select + Lookup a fig.",
        "< ↑, k > - Up",
        "< ↓, j > - Down",
        "< u > - Page Up",
        "< d > - Page Down",
        "< F > - Find - Select window only",
        ""
    ]

    """
    Form wrapper for entire list view
    """

    ACTION_CONTROLLER = ActionControllerSearch
    COMMAND_WIDGET_CLASS = SelectBox
    MAIN_WIDGET_CLASS = SelectableMultiline

    def __init__(self, cfg: ConfigService, *args, **keywords):
        super().__init__(*args, **keywords)

        # Legend Box Relative Location
        leg_relx, leg_rely = int(self.columns / 2) * -1 + self.BUFFER_LEFT, int(self.lines + self.BUFFER) * -1
        leg_max_height = len(self.LEGEND) + 2
        leg_max_width = int(self.columns / 2) - self.BUFFER - self.BUFFER_LEFT

        # Value Box Relative Location
        val_relx, val_rely = int(self.columns / 2) * - 1 + self.BUFFER_LEFT, int(self.lines / 2 + self.BUFFER) * -1
        val_max_height, val_max_width = int(self.lines / 2), int(self.columns / 2) - self.BUFFER - self.BUFFER_LEFT

        self.legend_box = self.add_widget(LegendBox, name="Legend", relx=leg_relx, rely=leg_rely,
                                          max_height=leg_max_height, max_width=leg_max_width,
                                          allow_filtering=False, editable=False, values=self.LEGEND)

        self.value_box = self.add_widget(SelectedValueBox, name="Parameter Value: ", relx=val_relx, rely=val_rely,
                                         max_height=val_max_height, max_width=val_max_width, allow_filtering=False,
                                         editable=False)

        self.wMain.set_select_callback(self.update_value_box)
        self._cfg = cfg

    def update_value_box(self, ps_name: str):
        """
        Lookup and update the value form when a user selects an item in the DisplayBox
        """
        self.value_box.name = ps_name
        self.value_box.update()

        try:
            val, desc, = self._cfg.get_parameter_with_description(ps_name)
        except ParameterUndecryptable:
            val = "Undecryptable"
            desc = "You do not have access to decrypt this parameter."

        desc = desc if desc else ''
        desc_lines = OutUtils.to_lines(desc, int(self.columns / 2 - self.BUFFER - self.BUFFER_LEFT))
        self.value_box.values = ["",
                                 "Value: ",
                                 f"    > {val}",
                                 "",
                                 "Description: ",
                                 f"---",
                                 "",
                                 ] + desc_lines

        self.value_box.update()

    def create(self):
        MAXY, MAXX = self.lines, int(self.columns / 2)

        self.wStatus1 = self.add(self.__class__.STATUS_WIDGET_CLASS, rely=0,
                                 relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                 editable=False,
                                 )

        if self.__class__.MAIN_WIDGET_CLASS:
            self.wMain = self.add(self.__class__.MAIN_WIDGET_CLASS,
                                  rely=self.__class__.MAIN_WIDGET_CLASS_START_LINE,
                                  relx=self.BUFFER_LEFT, max_height=-3, max_width=MAXX, editable=True
                                  )

        self.wStatus2 = self.add(self.__class__.STATUS_WIDGET_CLASS, rely=MAXY - 2 - self.BLANK_LINES_BASE,
                                 relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                 editable=False, )

        if not self.__class__.COMMAND_WIDGET_BEGIN_ENTRY_AT:
            self.wCommand = self.add(self.__class__.COMMAND_WIDGET_CLASS, name=self.__class__.COMMAND_WIDGET_NAME,
                                     rely=MAXY - 1 - self.BLANK_LINES_BASE, relx=0, )
        else:
            self.wCommand = self.add(
                self.__class__.COMMAND_WIDGET_CLASS, name=self.__class__.COMMAND_WIDGET_NAME,
                rely=MAXY - 1 - self.BLANK_LINES_BASE, relx=self.BUFFER_LEFT,
                begin_entry_at=self.__class__.COMMAND_WIDGET_BEGIN_ENTRY_AT,
                allow_override_begin_entry_at=self.__class__.COMMAND_ALLOW_OVERRIDE_BEGIN_ENTRY_AT)

        self.wStatus1.important = True
        self.wStatus2.important = True
        self.nextrely = 2

    def draw_form(self):
        MAXY, MAXX = self.lines, int(self.columns / 2)  # self.curses_pad.getmaxyx()
        self.curses_pad.hline(0, 0, curses.ACS_HLINE, MAXX)
        self.curses_pad.hline(MAXY - 2 - self.BLANK_LINES_BASE, 0, curses.ACS_HLINE, MAXX)


class ListApp(npyscreen.NPSApp):
    """
    List application wrapper for List form.
    """

    def __init__(self, view: RBACLimitedConfigView, cfg: ConfigService, env: RunEnv):
        self._view = view
        self._env = env
        self._cfg = cfg

    def main(self):
        F = FiggyListForm(self._cfg)
        F.wStatus1.value = f"Figs"
        F.wStatus2.value = "Filter: </search-query> <quit>"
        F.value.set_values(self._view.get_config_names())
        F.wMain.values = F.value.get()
        F.edit()
