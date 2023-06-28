import copy


class Link:
    def __init__(self, id_):
        self.id = id_
        self.type: str = ''
        self.source: str = ''
        self.target: str = ''

    @classmethod
    def from_dict(cls, json_dict):
        id_ = f"{json_dict['source']}_{json_dict['target']}"
        link = Link(id_)
        link.source = json_dict['source']
        link.target = json_dict['target']
        link.type = json_dict.get('type')
        return link

    def to_dict(self):
        return copy.deepcopy(self.__dict__)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
