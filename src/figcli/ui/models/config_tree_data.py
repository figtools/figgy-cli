from typing import List, Optional, Any

from pydantic import BaseModel


class ConfigTreeData(BaseModel):
    full_name: str
    node_name: Optional[str]
    dir_name: Optional[str]
    children: Optional[List["ConfigTreeData"]] = []

    def __init__(self, full_name: str, **data: Any):
        super().__init__(full_name=full_name, **data)
        self.node_name = full_name.split("/")[-1]
        self.full_name = full_name
        self.dir_name = "/".join(full_name.split("/")[:-1]) + "/"
        self.children: List["ConfigTreeData"] = []

    def add_child(self, child: "ConfigTreeData"):
        self.children.append(child)

    def __gt__(self, o: "ConfigTreeData"):
        return self.node_name > o.node_name
