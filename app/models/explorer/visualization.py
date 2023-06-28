from typing import Union

from app.models.explorer.link import Link
from app.models.explorer.node import Node


class Visualization:
    def __init__(self):
        self._focus: Union[Node, None] = None
        self._nodes = set()
        self._links = set()

    def focus(self, node: Node):
        self._focus = node
        self.add_node(node)

    def add_node(self, node: Node):
        self._nodes.add(node)

    def add_link(self, link: Link):
        self._links.add(link)

    def link_to_node(self, target: Node, type_: str):
        if self._focus is None:
            raise MissingFocusNode('Require focus node')
        link = Link.from_dict({'source': self._focus.id, 'target': target.id, 'type': type_})
        self.add_link(link)

    def link_from_node(self, source: Node, type_: str):
        if self._focus is None:
            raise MissingFocusNode('Require focus node')
        link = Link.from_dict({'source': source.id, 'target': self._focus.id, 'type': type_})
        self.add_link(link)

    def to_dict(self):
        data = {'nodes': [], 'links': []}
        if self._focus:
            data['focusedNode'] = self._focus.id

        for node in self._nodes:
            data['nodes'].append(node.to_dict())

        for link in self._links:
            data['links'].append(link.to_dict())

        return data


class MissingFocusNode(Exception):
    ...
