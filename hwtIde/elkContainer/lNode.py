from itertools import chain
from typing import List, Generator

from elkContainer.constants import PortSide, PortType,\
    NodeType, PortConstraints, LayerConstraint
from elkContainer.lPort import LPort
from elkContainer.lEdge import LEdge


class LNode():
    """
    Component for component diagram

    :ivar originObj: original object which this node represents
    :ivar name: name of this unit
    :ivar class_name: name of class of this unit

    :ivar north: list of LPort for on  top side.
    :ivar east: list of LPort for on right side.
    :ivar south: list of LPort for on bottom side.
    :ivar west: list of LPort for on left side.
    """

    def __init__(self, parent: "LNode"=None, name: str= None,
                 originObj=None, node2lnode=None):
        super(LNode, self).__init__()
        if name is not None:
            assert isinstance(name, str)
        self.originObj = originObj
        self.name = name

        self.west = []
        self.east = []
        self.north = []
        self.south = []

        self.parent = parent

        self.portConstraints = PortConstraints.FIXED_ORDER
        self.children = []
        self.origin = None
        self._node2lnode = node2lnode

    def iterPorts(self) -> Generator[LPort, None, None]:
        return chain(self.north, self.east, self.south, self.west)

    def getPortSideView(self, side) -> List["LPort"]:
        """
        Returns a sublist view for all ports of given side.

        :attention: Use this only after port sides are fixed!

        This is currently the case after running the {@link org.eclipse.elk.alg.layered.intermediate.PortListSorter}.
        Non-structural changes to this list are reflected in the original list. A structural modification is any
        operation that adds or deletes one or more elements; merely setting the value of an element is not a structural
        modification. Sublist indices can be cached using {@link LNode#cachePortSides()}.

        :param side: a port side
        :return: an iterable for the ports of given side
        """
        if side == PortSide.WEST:
            return self.west
        elif side == PortSide.EAST:
            return self.east
        elif side == PortSide.NORTH:
            return self.north
        elif side == PortSide.SOUTH:
            return self.south
        else:
            raise ValueError(side)

    def add_port(self, name, direction: PortType, side: PortSide):
        port = LPort(self, direction, side, name=name)
        self.getPortSideView(side).append(port)
        return port

    def add_node(self, name: str=None, originObj=None,
                 portConstraint=PortConstraints.FIXED_ORDER) -> "LNode":
        n = LNode(self, name=name, originObj=originObj,
                  node2lnode=self._node2lnode)
        n.portConstraints = portConstraint
        if self._node2lnode is not None:
            self._node2lnode[originObj] = n
        self.children.append(n)
        return n

    def add_edge(self, src: LPort, dst: LPort, name=None, originObj=None):
        e = LEdge(name, originObj=originObj)
        e.setSrcDst(src, dst)
        return e

    def toElkJson(self, idStore):
        d = {
            "id": idStore[self],
            "name": self.name,
            "width": 200,
            "height": 20 * sum(1 for _ in self.iterPorts()),
            "ports": [p.toElkJson(idStore) for p in self.iterPorts()],
            "properties": {
                "portConstraints": self.portConstraints.name
            }
        }
        if self.children:
            nodes = []
            edges = set()
            for p in self.iterPorts():
                edges.update(p.iterEdges())
            for ch in self.children:
                nodes.append(ch.toElkJson(idStore))
                for p in ch.iterPorts():
                    edges.update(p.iterEdges())
            d["nodes"] = nodes
            d["links"] = [e.toElkJson(idStore) for e in edges]
        return d

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)


class LayoutExternalPort(LNode):
    def __init__(self, parent: "LNode", name: str=None,
                 direction=None, node2lnode=None):
        super(LayoutExternalPort, self).__init__(
            parent=parent, name=name, node2lnode=node2lnode)
        self.direction = direction
        self.type = NodeType.EXTERNAL_PORT
        if direction == PortType.INPUT:
            self.layeringLayerConstraint = LayerConstraint.FIRST
        elif direction == PortType.OUTPUT:
            self.layeringLayerConstraint = LayerConstraint.LAST
        else:
            raise ValueError(direction)
