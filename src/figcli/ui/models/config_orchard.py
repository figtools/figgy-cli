from typing import List, Set

from pydantic import BaseModel

from figcli.ui.models.config_tree_data import ConfigTreeData


class ConfigOrchard(BaseModel):
    trees: List[ConfigTreeData] = []

    def add_tree(self, tree: ConfigTreeData):
        self.trees.append(tree)

    @staticmethod
    def build_orchard(config_names: Set[str]):
        orchard: ConfigOrchard = ConfigOrchard()
        root_nodes = set(["/" + x.split('/')[1] for x in config_names])
        missing_dirs = set()

        # add all directories from the provided names as new names
        for cfg_name in config_names:
            cfg_list = cfg_name.split("/")
            for i in range(0, len(cfg_list)):
                new_dir = "/".join(cfg_list[0:i])
                missing_dirs.add(new_dir)

        config_names = config_names | missing_dirs
        for node in root_nodes:
            data_node = ConfigTreeData(full_name=node)
            orchard.trees.append(data_node)
            children = set([x for x in config_names if x.startswith(data_node.full_name)])
            orchard.add_children(data_node, children)

        orchard.trees = sorted(orchard.trees)

        return orchard

    def add_children(self, node: ConfigTreeData, children: Set[str]):
        for child in children:
            parent_dir = "/".join(child.split("/")[:-1])
            if parent_dir == node.full_name:
                new_child = ConfigTreeData(full_name=child)
                node.add_child(new_child)
                new_children = set([x for x in children if x.startswith(new_child.full_name)])
                self.add_children(new_child, new_children)
                node.children = sorted(node.children)
