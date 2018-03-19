from itertools import chain
from typing import List

from layout.containers.geometry import GeometryRect
from layout.containers.sizeConfig import PORT_HEIGHT


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

    def __init__(self, parent: "LNode", name: str, direction, side):
        self.originObj = None
        self.parent = parent
        self.name = name
        self.direction = direction
        self.geometry = None
        self.outgoingEdges = []
        self.incomingEdges = []
        self.children = []
        self.side = side

        self.portDummy = None
        self.insideConnections = False

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
                if e.isSelfLoop():
                    continue
                yield e
        else:
            return it

    def initDim(self, width, x=0, y=0):
        g = self.geometry = GeometryRect(x, y, width, PORT_HEIGHT)
        return g.y + g.height

    def translate(self, x, y):
        self.geometry.x += x
        self.geometry.y += y
        assert not self.children

    def _getDebugName(self) -> List[str]:
        names = []
        p = self
        while True:
            if p is None:
                break
            names.append(p.name)
            p = p.parent
        return list(reversed(names))

    def getPredecessorPorts(self):
        for e in self.incomingEdges:
            yield e.src

    def getSuccessorPorts(self):
        for e in self.outgoingEdges:
            yield e.dst

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, ".".join(self._getDebugName()))
