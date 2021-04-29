import curses
from collections import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

import npyscreen
from botocore.exceptions import ClientError
from npyscreen import MLTreeMultiSelect, NPSTreeData, NPSApp, Form, TreeLineSelectable, BoxTitle, MultiLine

from figcli.commands.config.delete import Delete
from figcli.commands.config.get import Get
from figcli.commands.config_context import ConfigContext
from figcli.commands.types.config import ConfigCommand
from figgy.data.dao.ssm import SsmDao
from figcli.io.input import Input
from figcli.io.output import OutUtils
from figcli.svcs.config import ParameterUndecryptable, ConfigService
from figcli.svcs.observability.anonymous_usage_tracker import AnonymousUsageTracker
from figcli.svcs.observability.version_tracker import VersionTracker
from figcli.utils.utils import *
from figcli.utils.utils import Utils
from figcli.views.rbac_limited_config import RBACLimitedConfigView

log = logging.getLogger(__name__)


class Browse(ConfigCommand, npyscreen.NPSApp):

    def __init__(self, ssm_init: SsmDao, cfg_svc: ConfigService, colors_enabled: bool, context: ConfigContext,
                 get_command: Get, delete_command: Delete, config_view: RBACLimitedConfigView):
        super().__init__(browse, colors_enabled, context)
        self._ssm = ssm_init
        self._get = get_command
        self._cfg_svc = cfg_svc
        self._config_view = config_view
        self.selected_ps_paths = []
        self.deleted_ps_paths = []
        self.dirs = set()
        self._utils = Utils(colors_enabled)
        self._delete = delete_command
        self.prefix = context.prefix

    def add_children(self, prefix: str, td_node: NPSTreeData, all_children: set = None,
                     first_children: set = None):
        """
        Looks up all children at `prefix` and recursively adds them to the TreeData node.
        Adds all children to the TreeData node passed in, and recurses down the tree of children.

        Once the original total lookup of all PS nodes is done, all_children and first_children are progressively
        filtered and passed down with smaller data sets as the tree is built.
        Args:
            prefix: Prefix to query and built a tree from. I.E. /app
            td_node: The node to append found first children too
            all_children: List of ALL children of the passed in prefix's node.
            first_children:  List of the FIRST children of the passed in prefix's node.
                            (Immediate children, not grandchildren)
        """
        with ThreadPoolExecutor(max_workers=10) as pool:
            first_res = None
            all_res = None
            if first_children is None:
                first_res = pool.submit(self._config_view.get_config_names, prefix=prefix, one_level=True)

            if all_children is None:
                all_res = pool.submit(self._config_view.get_config_names, prefix=prefix)

            if first_res is not None:
                first_children = set(first_res.result())

            if all_res is not None:
                all_children = set(all_res.result())

        diff_children = all_children.difference(first_children)
        child_dirs = set(list(map(lambda x: f"{prefix}/{x.replace(f'{prefix}/', '', 1).split('/')[0]}", diff_children)))
        self.dirs = self.dirs | child_dirs

        for child in sorted(first_children):
            child_name = child.replace(prefix, '', 1)
            if child_name != '/':
                td_node.newChild(content=child_name, selectable=True, expanded=False)

        for child_dir in sorted(child_dirs):
            child_name = child_dir.replace(prefix, '', 1)
            if child_name != '/':
                grand_children = set(list(filter(lambda x: x.startswith(f'{prefix}{child_name}/'), all_children)))
                calculated_first_children = set(list(filter(
                    lambda x: len(x.split('/')) == len(prefix.split('/')) + 2, grand_children)))

                dir_node = td_node.newChild(content=child_dir.replace(prefix, '', 1), selectable=False, expanded=False)
                self.add_children(child_dir, dir_node, all_children=grand_children,
                                  first_children=calculated_first_children)

    @AnonymousUsageTracker.track_command_usage
    def _browse(self):
        browse_app = BrowseApp(self, self._config_view, self._cfg_svc)
        browse_app.run()

    def _print_val(self, path, val, desc):
        if val is not None:
            print(f"\r\n{self.c.fg_bl}Key:{self.c.rs} {path}")
            print(f"{self.c.fg_bl}Value:{self.c.rs} {val}\r\n")
            desc = desc if desc else DESC_MISSING_TEXT
            print(f"{self.c.fg_bl}Description:{self.c.rs} {desc}\r\n")

    def _safe_delete(self, ps_name: str):
        try:
            self._ssm.delete_parameter(ps_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                return

        print(f"{self.c.fg_gr}Deleted: {ps_name}{self.c.rs}")

    def _perform_deletions(self) -> None:
        deleted = []  # type: List[str]
        for path in self.deleted_ps_paths:
            if path in self.dirs:
                all_children = set(list(map(lambda x: x['Name'],
                                            self._ssm.get_all_parameters([path], option='Recursive'))))
                delete_children = Input.y_n_input(f"You have selected a DIRECTORY to delete: {path}. "
                                                  f"Do you want to delete ALL children of: {path}?", default_yes=False)

                if delete_children:
                    for child in all_children:
                        if self._delete.delete_param(child):
                            deleted.append(child)
            else:
                if path not in deleted:
                    delete_it = Input.y_n_input(f"Delete {path}? ", default_yes=True)

                    if delete_it:
                        if self._delete.delete_param(path):
                            deleted.append(path)

    def _print_values(self) -> None:
        for path in self.selected_ps_paths:
            if path in self.dirs:
                notify, selection = False, ''
                print(f"\r\nIt appears you selected a directory: {path}.")
                while not self._utils.is_valid_selection(selection, notify):
                    selection = input(f"Would you like to print values for all children of {path}? (Y/n): ")
                    selection = selection if selection != '' else 'y'
                if selection.lower() == 'y':
                    all_children = set(list(map(lambda x: x['Name'],
                                                self._ssm.get_all_parameters([path], option='Recursive'))))
                    for child in all_children:
                        val, desc = self._get.get_val_and_desc(child)
                        self._print_val(child, val, desc)
            else:
                val, desc = self._get.get_val_and_desc(path)
                self._print_val(path, val, desc)

    @AnonymousUsageTracker.track_command_usage
    @VersionTracker.notify_user
    def execute(self):
        self._browse()
        self._perform_deletions()
        self._print_values()


class SelectedValueBox(BoxTitle):
    """Creates box around Lookup Box"""
    _contained_widget = MultiLine


class DeletableNPSTreeData(NPSTreeData):
    """
    Extends NPSTreeData class to add deleted property so we may mark individual nodes as deleted.
    """

    def __init__(self, content=None, parent=None, selected=False, selectable=True,
                 highlight=False, expanded=True, ignoreRoot=True, sort_function=None, deleted=False):
        super().__init__(content=content, parent=parent, selected=selected, selectable=selectable,
                         highlight=highlight, expanded=expanded, ignoreRoot=ignoreRoot,
                         sort_function=sort_function)
        self.deleted = deleted


class BrowseApp(NPSApp):
    """
    Extends NPSApp class to add support for getting a list of deleted tree nodes that were marked for deletion.
    """
    BUFFER = 3
    SELECTED = 'SELECTED'
    TO_DELETE = 'TO_DELETE"'

    def __init__(self, browse: Browse, config_view: RBACLimitedConfigView, cfg: ConfigService):
        self._browse = browse
        self._config_view = config_view
        self._cfg = cfg
        self.value_box = None
        self.browse_box = None
        self.select_state_box = None
        self.selected_params = {}

    def main(self):
        global npy_form
        self._browse_box = Form(
            name="Browse Parameters: - 'e' to expand, 'c' to collapse, <s> to select, <d> to delete, "
                 "<Tab> & <Shift+Tab> moves cursor between `OK` and `Tree` views.")

        # Value Box Relative Location
        val_relx, val_rely = int(self._browse_box.columns / 2) * -1, int(self._browse_box.lines - 1) * -1
        val_max_height = int(self._browse_box.lines / 2) - self.BUFFER
        val_max_width = int(self._browse_box.columns / 2) - self.BUFFER

        # Selection Box Relative Location
        sel_relx, sel_rely = int(self._browse_box.columns / 2) * -1, int(self._browse_box.lines / 2 + 1) * -1
        sel_max_height = int(self._browse_box.lines / 2) - self.BUFFER
        sel_max_width = int(self._browse_box.columns / 2) - self.BUFFER

        tree = self._browse_box.add(LogicalMLTree, on_select_callable=self.on_select,
                                    on_delete_callable=self.on_delete,
                                    max_width=self._browse_box.columns + val_relx - self.BUFFER)

        self.value_box = self._browse_box.add_widget(SelectedValueBox, name="Parameter Value: ", relx=val_relx,
                                                     rely=val_rely,
                                                     max_height=val_max_height, max_width=val_max_width,
                                                     allow_filtering=False,
                                                     editable=False)

        self.select_state_box = self._browse_box.add_widget(SelectedValueBox, name="Selections: ", relx=sel_relx,
                                                            rely=sel_rely,
                                                            max_height=sel_max_height, max_width=sel_max_width,
                                                            allow_filtering=False,
                                                            editable=False)

        td = DeletableNPSTreeData(content='Root', selectable=True, expanded=True, ignoreRoot=True)
        start = Utils.millis_since_epoch()
        children = []
        if self._browse.prefix:
            prefix_child = td.newChild(content=self._browse.prefix, selectable=False, expanded=False)
            children = [prefix_child]
        else:
            log.info(f"--{prefix.name} missing, defaulting to normal browse tree.")

            for namespace in self._config_view.get_authorized_namespaces():
                child = td.newChild(content=namespace, selectable=False, expanded=False)
                children.append(child)

        for child in children:
            self._browse.dirs.add(child.getContent())

        futures = []

        with ThreadPoolExecutor(max_workers=10) as pool:
            for child in children:
                futures.append(pool.submit(self._browse.add_children, child.getContent(), child))

        for future in as_completed(futures):
            pass

        tree.values = td
        self._browse_box.edit()
        selection_objs = tree.get_selected_objects(return_node=True)

        for selection in selection_objs:
            full_path = ''
            while selection._parent is not None:
                full_path = selection.content + full_path
                selection = selection._parent
            self._browse.selected_ps_paths.append(full_path)

        delete_objs = tree.get_objects_to_delete(return_node=True)
        for selection in delete_objs:
            full_path = ''
            while selection._parent is not None:
                full_path = selection.content + full_path
                selection = selection._parent
            self._browse.deleted_ps_paths.append(full_path)

    def generate_selections(self) -> List:
        selects = [key for key in self.selected_params.keys() if self.selected_params[key] == self.SELECTED]
        deletes = [key for key in self.selected_params.keys() if self.selected_params[key] == self.TO_DELETE]

        select_prefix = ["", "Selections: ", "---"] if selects else []
        delete_prefix = ["", "To Delete: ", "---"] if deletes else []

        return select_prefix + selects + delete_prefix + deletes

    def on_delete(self, ps_name):
        if self.selected_params.get(ps_name) == self.TO_DELETE:
            del self.selected_params[ps_name]
        else:
            self.selected_params[ps_name] = self.TO_DELETE

        self.select_state_box.values = self.generate_selections()
        self.select_state_box.update()

    def on_select(self, ps_name: str, update: bool = True):
        """
        Lookup and update the value form when a user selects an item in the DisplayBox
        """

        # Only update query box on selects
        if update:
            self.value_box.name = ps_name
            try:
                val, desc, = self._cfg.get_parameter_with_description(ps_name)
            except ParameterUndecryptable:
                val = "Undecryptable"
                desc = "You do not have access to decrypt this parameter."
            except TypeError:
                return  # No parameter found

            val = f"> {val}" if val else ''
            desc = f"> {desc}" if desc else ''

            if val or desc:
                line_length = int(self._browse_box.columns / 2) - self.BUFFER
                val_lines = OutUtils.to_lines(val, line_length)
                desc_lines = OutUtils.to_lines(desc, line_length)
                self.value_box.values = ["",
                                         "Value: ",
                                         f"---",
                                         ] + val_lines + [
                                            "",
                                            "Description: ",
                                            f"---",

                                        ] + desc_lines

                self.value_box.update()

        # Update selection box
        if self.selected_params.get(ps_name) == self.SELECTED:
            del self.selected_params[ps_name]
        else:
            self.selected_params[ps_name] = self.SELECTED

        self.select_state_box.values = self.generate_selections()
        self.select_state_box.update()


class TreeLineMultiFunctionSelect(TreeLineSelectable):
    """
    Extends functionality of TreeLineSelectable to provide DELETE toggling
    """
    CAN_DELETE_DELETED = '[DELETE]'
    CANNOT_SELECT_DELETED = '[DELETE_DIR]'

    def _print_select_controls(self):
        SELECT_DISPLAY = None

        if self._tree_real_value.selectable:
            if self.value.deleted:
                SELECT_DISPLAY = self.CAN_DELETE_DELETED
            elif self.value.selected:
                SELECT_DISPLAY = self.CAN_SELECT_SELECTED
            else:
                SELECT_DISPLAY = self.CAN_SELECT
        else:
            if self.value.deleted:
                SELECT_DISPLAY = self.CANNOT_SELECT_DELETED
            elif self.value.selected:
                SELECT_DISPLAY = self.CANNOT_SELECT_SELECTED
            else:
                SELECT_DISPLAY = self.CANNOT_SELECT

        if self.do_colors():
            attribute_list = self.parent.theme_manager.findPair(self, 'CONTROL')
        else:
            attribute_list = curses.A_NORMAL

        # python2 compatibility
        if isinstance(SELECT_DISPLAY, bytes):
            SELECT_DISPLAY = SELECT_DISPLAY.decode()

        self.add_line(self.rely,
                      self.left_margin + self.relx,
                      SELECT_DISPLAY,
                      self.make_attributes_list(SELECT_DISPLAY, attribute_list),
                      self.width - self.left_margin,
                      )

        return len(SELECT_DISPLAY)


class LogicalMLTree(MLTreeMultiSelect):
    _contained_widgets = TreeLineMultiFunctionSelect

    """
    Sets ups Logical instead of insane key bindings for ML Tree Viewer.

    Also disables select_cascades by default.
    
    Also provides ability to set `delete` on nodes, and query all deleted nodes
    """

    def __init__(self, screen, on_select_callable: Callable, on_delete_callable: Callable,
                 select_cascades=False, *args, **keywords):
        super(MLTreeMultiSelect, self).__init__(screen, select_cascades=select_cascades, *args, **keywords)
        self.select_cascades = select_cascades
        self._on_select_callable = on_select_callable
        self._on_delete_callable = on_delete_callable

    def set_up_handlers(self):
        super(MLTreeMultiSelect, self).set_up_handlers()
        self.handlers.update({
            ord('c'): self.h_collapse_tree,
            ord('e'): self.h_expand_tree,
            ord('C'): self.h_collapse_all,
            ord('E'): self.h_expand_all,
            ord('d'): self.h_delete,
            ord('s'): self.h_select,
            ord('r'): self.h_refresh
        })

    def get_path(self, value):
        full_path = ''
        while value._parent is not None:
            full_path = value.content + full_path
            value = value._parent

        return full_path

    def h_select(self, ch):
        vl = self.values[self.cursor_line]
        vl_to_set = not vl.selected
        vl.deleted = False

        if self.select_cascades:
            for v in self._walk_tree(vl, only_expanded=False, ignore_root=False):
                if v.selectable:
                    v.selected = vl_to_set
        else:
            vl.selected = vl_to_set

        self._on_select_callable(self.get_path(vl), update=vl_to_set)

        if self.select_exit:
            self.editing = False
            self.how_exited = True
        self.display()

    def h_refresh(self, ch):
        npyscreen.blank_terminal()
        npy_form.edit()
        # npy_form.useable_space

    def h_delete(self, ch):
        vl = self.values[self.cursor_line]
        vl_to_set = not vl.deleted
        vl.selected = False

        if self.select_cascades:
            for v in self._walk_tree(vl, only_expanded=False, ignore_root=False):
                if v.selectable:
                    v.deleted = vl_to_set
        else:
            vl.deleted = vl_to_set
        if self.select_exit:
            self.editing = False
            self.how_exited = True

        self._on_delete_callable(self.get_path(vl))
        self.display()

    def get_objects_to_delete(self, return_node=True):
        for v in self._walk_tree(self._myFullValues, only_expanded=False, ignore_root=False):
            if v.deleted:
                if return_node:
                    yield v
                else:
                    yield self._get_content(v)
