from itertools import chain
from typing import List


class LPort():
    """
    Port for component in component diagram

    :ivar originObj: original object which this node represents
    :ivar parent: parent unit of this port
    :ivar name: name of this port
    :ivar direction: direction of this port
    :ivar geometry: absolute geometry in layout
    :ivar children: list of children ports, before interface connecting phase
            (when routing this list is empty and children are directly on parent LNode)
    """

    def __init__(self, parent: "LNode", direction, side, name: str=None):
        super(LPort, self).__init__()
        self.originObj = None
        self.parent = parent
        self.name = name
        self.direction = direction

        self.outgoingEdges = []
        self.incomingEdges = []
        self.children = []
        self.side = side

    def getNode(self):
        p = self
        while True:
            p = p.parent
            if not isinstance(p, LPort):
                return p

    def iterEdges(self, filterSelfLoops=False):
        it = chain(self.incomingEdges, self.outgoingEdges)
        if filterSelfLoops:
            for e in it:
                if not e.isSelfLoop:
                    yield e
        else:
            yield from it

    def _getDebugName(self) -> List[str]:
        names = []
        p = self
        while True:
            if p is None:
                break
            name = p.name
            if name is None:
                name = "<Unnamed>"
            names.append(name)
            p = p.parent
        return list(reversed(names))

    def toElkJson(self, idStore):
        return {
            "id": idStore[self],
            "properties": {
                "portSide": self.side.name
            }
        }

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, ".".join(self._getDebugName()))
