from itertools import chain
from typing import List, Union

from hwt.hdl.constants import INTF_DIRECTION
from hwt.hdl.portItem import PortItem
from hwt.hdl.statements import HdlStatement
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from layout.geometry import GeometryRect
from enum import Enum


UNIT_HEADER_OFFSET = 20
PORT_HEIGHT = 20
PORT_X_PADDING = 20
UNIT_PADDING = 5

# http://rtsys.informatik.uni-kiel.de/%7Ebiblio/downloads/theses/msp-dt.pdf


def width_of_str(s):
    return len(s) * 12


class LayoutIdCtx(dict):
    # {LayoutObj: int}
    def __getitem__(self, obj):
        try:
            return dict.__getitem__(self, obj)
        except KeyError:
            pass

        return self._register(obj)

    def _register(self, obj) -> int:
        i = len(self)
        self[obj] = i
        return i


class NodeType(Enum):
    NORMAL = 0
    NORTH_SOUTH_PORT = 1
    EXTERNAL_PORT = 2


class PortType(Enum):
    INPUT = 0
    OUTPUT = 1


class LayoutPort():
    """
    Port for component in component diagram

    :ivar portItem: original object which this node represents
    :ivar parent: parent unit of this port
    :ivar name: name of this port
    :ivar direction: direction of this port
    :ivar geometry: absolute geometry in layout
    :ivar children: list of children ports, before interface connecting phase
            (when routing this list is empty and childrens are directly on parent LayoutNode)
    """

    def __init__(self, portItem: PortItem, parent: "LayoutNode", name: str, direction):
        self.portItem = portItem
        self.parent = parent
        self.name = name
        self.direction = direction
        self.geometry = None
        self.connectedEdges = []
        self.children = []

    def getNode(self):
        p = self
        while True:
            p = p.parent
            if isinstance(p, LayoutNode):
                return p

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

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, ".".join(self._getDebugName()))


class LayoutNode():
    """
    Component for component diagram

    :ivar origin: original object which this node represents
    :ivar name: name of this unit
    :ivar class_name: name of class of this unit
    :ivar right: list of LayoutPort for on right border of this node
    :ivar left: list of LayoutPort for on left border of this node
    """

    def __init__(self, origin: Unit, name: str, objMap):
        self.origin = origin
        self.name = name
        self.left = []
        self.right = []
        self.geometry = None
        self.parent = None

        # {PortItem: LayoutPort}
        self._port_obj_map = objMap

        # used by cycle breaker
        self.indeg = 0
        self.outdeg = 0
        self.mark = 0
        # used by layerer
        self.normHeight = None
        self.nestedGraph = None
        self.type = NodeType.NORMAL

    def iterPorts(self):
        return chain(self.left, self.right)

    def initPortDegrees(self):
        indeg = 0
        outdeg = 0
        for p in self.iterPorts():
            for e in p.connectedEdges:
                if not e.isSelfLoop():
                    d = p.direction
                    if d == INTF_DIRECTION.SLAVE:
                        indeg += 1
                    elif d == INTF_DIRECTION.MASTER:
                        outdeg += 1
                    else:
                        raise TypeError(d)

        self.indeg = indeg
        self.outdeg = outdeg

    def initDim(self, x=0, y=0):
        label_w = width_of_str(self.name)
        port_w = max(*map(lambda p: width_of_str(p.name),
                          self.iterPorts()),
                     label_w / 2)
        width = max(port_w, label_w)
        height = UNIT_HEADER_OFFSET + \
            max(len(self.left), len(self.right)) * PORT_HEIGHT
        self.geometry = GeometryRect(x, y, width, height)

        port_width = width / 2
        _y = y + UNIT_HEADER_OFFSET
        for i in self.left:
            _y = i.initDim(port_width, x=x, y=_y)

        _y = y + UNIT_HEADER_OFFSET
        for o in self.right:
            _y = o.initDim(port_width, x=x + port_width, y=_y)

    def translate(self, x, y):
        self.geometry.x += x
        self.geometry.y += y
        for p in self.iterPorts():
            p.translate(x, y)

    def add_port(self, origin: Union[Interface, PortItem], direction,
                 name: str):
        if direction == INTF_DIRECTION.MASTER:
            portArr = self.right
        elif direction == INTF_DIRECTION.SLAVE:
            portArr = self.left
        else:
            raise ValueError()

        p = LayoutPort(origin, self, name, direction)
        portArr.append(p)
        self._port_obj_map[origin] = p
        return p

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)


class LayoutExternalPort(LayoutNode):
    def __init__(self, origin, name, direction, objMap):
        super(LayoutExternalPort, self).__init__(
            origin, name, objMap)
        self.direction = direction


class LayoutNodeLayer(list):
    def __init__(self, parent: "Layout"):
        self.parent = parent
        parent.layers.append(self)

    def append(self, v):
        v.layer = self
        return list.append(self, v)

    def extend(self, iterable):
        for v in iterable:
            self.append(v)


class LayoutEdge():
    def __init__(self, signal: RtlSignal, name: str):
        self.name = name
        self.signal = signal
        self.src = None
        self.srcNode = None
        self.dst = None
        self.dstNode = None
        self.reversed = False

    def setSrcDst(self, src: LayoutPort, dst: LayoutPort):
        self.src = src
        self.srcNode = src.getNode()
        self.dst = dst
        self.dstNode = dst.getNode()
        src.connectedEdges.append(self)
        dst.connectedEdges.append(self)

    def reverse(self):
        self.src, self.dst = self.dst, self.src
        self.srcNode, self.dstNode = self.dstNode, self.srcNode
        self.reversed = not self.reversed

    def isSelfLoop(self):
        """
        :return: True if source is same node as destination
        """
        return self.srcNode is self.dstNode

    def __repr__(self):
        return "<%s, %r -> %r>" % (self.__class__.__name__, self.src, self.dst)


class Layout():
    def __init__(self):
        self.edges = []
        self.nodes = []
        self.layers = []

        # node to layout node
        self._node2lnode = {}

    def getLayerlessNodes(self):
        """
        Returns the list of nodes that are not currently assigned to a layer.
        """
        return self.nodes

    def add_stm_as_unit(self, stm: HdlStatement) -> LayoutNode:
        u = LayoutNode(stm, stm.__class__.__name__, self._node2lnode)
        self._node2lnode[stm] = u
        u.right.append(LayoutPort(None, u, "out", INTF_DIRECTION.MASTER))
        u.left.append(LayoutPort(None, u, "in", INTF_DIRECTION.SLAVE))
        self.nodes.append(u)
        return u

    def add_node(self, origin: Unit, name: str) -> LayoutNode:
        n = LayoutNode(origin, origin._name, self._node2lnode)
        self.nodes.append(n)
        return n

    def add_edge(self, signal, name, src: LayoutPort, dst: LayoutPort):
        e = LayoutEdge(signal, name)
        e.setSrcDst(src, dst)
        self.edges.append(e)
        return e


def getParentUnit(intf):
    while isinstance(intf._parent, Interface):
        intf = intf._parent

    return intf._parent
