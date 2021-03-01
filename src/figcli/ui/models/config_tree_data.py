from dataclasses import dataclass
from typing import List


@dataclass
class ConfigTreeData:
    node_name: str
    full_name: str
    dir_name: str
    children: List["ConfigTreeData"]

    def __init__(self, full_name: str):
        self.node_name = full_name.split("/")[-1]
        self.full_name = full_name
        self.dir_name = "/".join(full_name.split("/")[:-1]) + "/"
        self.children: List["ConfigTreeData"] = []

    def add_child(self, child: "ConfigTreeData"):
        self.children.append(child)

    def __gt__(self, o: "ConfigTreeData"):
        return self.node_name > o.node_name
