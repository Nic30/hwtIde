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
    # a normal node is created from a node of the original graph.
    NORMAL = 0
    # a dummy node created to split a long edge.
    LONG_EDGE = 1
    # a node representing an external port.
    EXTERNAL_PORT = 2
    # a dummy node created to cope with ports at the northern or southern side.
    NORTH_SOUTH_PORT = 3
    # a dummy node to represent a mid-label on an edge.
    LABEL = 4
    # a dummy node originating from a node spanning multiple layers.
    BIG_NODE = 5
    # a dummy node representing a breaking point used to 'wrap' graphs.
    BREAKING_POINT = 6


class PortType(Enum):
    INPUT = INTF_DIRECTION.SLAVE
    OUTPUT = INTF_DIRECTION.MASTER


class PortSide(Enum):
    EAST = 0
    WEST = 1
    SOUTH = 2
    NORTH = 3

    @staticmethod
    def opposite(side):
        d = {PortSide.EAST: PortSide.WEST,
             PortSide.WEST: PortSide.EAST,
             PortSide.SOUTH: PortSide.NORTH,
             PortSide.NORTH: PortSide.SOUTH}
        return d[side]


class PortConstraints(Enum):
    # Undefined constraints.
    UNDEFINED = 0
    # All ports are free.
    FREE = 1
    # The side is fixed for each port.
    FIXED_SIDE = 2
    # The side is fixed for each port, and the order of ports is fixed for
    # each side.
    FIXED_ORDER = 3
    # The side is fixed for each port, the order or ports is fixed for each side and
    # the relative position of each port must be preserved. That means if the node is
    # resized by factor x, the port's position must also be scaled by x.
    FIXED_RATIO = 4
    # The exact position is fixed for each port.
    FIXED_POS = 5

    def isPosFixed(self):
        """
        Returns whether the position of the ports is fixed. Note that this is not true
        if port ratios are fixed.

        @return true if the position is fixed
        """
        return self == PortConstraints.FIXED_POS

    def isRatioFixed(self):
        """
        Returns whether the ratio of port positions is fixed. Note that this is not true
        if the port positions are fixed.

        @return true if the ratio is fixed
        """
        return self == PortConstraints.FIXED_RATIO

    def isOrderFixed(self):
        """
        Returns whether the order of ports is fixed.

        @return true if the order of ports is fixed
        """
        return (self == PortConstraints.FIXED_ORDER
                or self == PortConstraints.FIXED_RATIO
                or self == PortConstraints.FIXED_POS)

    def isSideFixed(self):
        """
        Returns whether the sides of ports are fixed.

        @see PortSide
        @return true if the port sides are fixed
        """
        return self == PortConstraints.FREE and self != PortConstraints.UNDEFINED


class EdgeRouting(Enum):
    # undefined edge routing.
    UNDEFINED = 0
    # polyline edge routing.
    POLYLINE = 1
    # orthogonal edge routing.
    ORTHOGONAL = 2
    # splines edge routing.
    SPLINES = 4


class LPort():
    """
    Port for component in component diagram

    :ivar originObj: original object which this node represents
    :ivar parent: parent unit of this port
    :ivar name: name of this port
    :ivar direction: direction of this port
    :ivar geometry: absolute geometry in layout
    :ivar children: list of children ports, before interface connecting phase
            (when routing this list is empty and childrens are directly on parent LNode)
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
            if isinstance(p, LNode):
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

    def getPredecessorPorts(self):
        for e in self.incomingEdges:
            yield e.src

    def getSuccessorPorts(self):
        for e in self.outgoingEdges:
            yield e.dst

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, ".".join(self._getDebugName()))


class LNode():
    """
    Component for component diagram

    :ivar originObj: original object which this node represents
    :ivar name: name of this unit
    :ivar class_name: name of class of this unit

    :ivar NORTH: list of LPort for on  top side.
    :ivar EAST: list of LPort for on right side.
    :ivar SOUTH: list of LPort for on bottom side.
    :ivar WEST: list of LPort for on left side.
    """

    def __init__(self, graph: "Layout", name: str= None):
        self.originObj = None
        self.name = name

        self.west = []
        self.east = []
        self.north = []
        self.south = []

        self.geometry = None
        self.parent = None

        # {PortItem: LPort}
        self.graph = graph
        self.childGraphs = []

        # used by cycle breaker
        self.indeg = 0
        self.outdeg = 0
        self.mark = 0
        # used by layerer
        self.normHeight = None
        self.nestedGraph = None
        self.type = NodeType.NORMAL

        self.layer = None
        self.inLayerSuccessorConstraint = []
        self.portConstraints = PortConstraints.UNDEFINED
        self.inLayerLayoutUnit = self
        self.nestedLgraph = None
        self.compoundNode = False
        self.origin = None
        self.extPortSide = None
        self.barycenterAssociates = None

    def setOriginObj(self, obj):
        self.originObj = obj

    def iterPorts(self):
        return chain(self.north, self.east, self.south, self.west)

    def getPorts(self, direction):
        for p in self.iterPorts():
            if p.direction == direction:
                yield p

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

        if self.south or self.north:
            raise NotImplementedError()

        port_width = width / 2
        _y = y + UNIT_HEADER_OFFSET
        for i in self.east:
            _y = i.initDim(port_width, x=x, y=_y)

        _y = y + UNIT_HEADER_OFFSET
        for o in self.west:
            _y = o.initDim(port_width, x=x + port_width, y=_y)

    def translate(self, x, y):
        self.geometry.x += x
        self.geometry.y += y
        for p in self.iterPorts():
            p.translate(x, y)

    def addPortFromHdl(self, origin: Union[Interface, PortItem],
                       direction: INTF_DIRECTION,
                       name: str):
        if direction == INTF_DIRECTION.MASTER:
            side = PortSide.WEST
        elif direction == INTF_DIRECTION.SLAVE:
            side = PortSide.EAST
        else:
            raise ValueError()

        p = self.addPort(name, direction, side)
        p.originObj = origin
        self.graph._node2lnode[origin] = p
        return p

    def addPort(self, name, direction: INTF_DIRECTION, side: PortSide):
        port = LPort(self, name, direction, side)
        self.getPortSideView(side).append(port)
        return port

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

        # if not self.portSidesCached:
        #    # If not explicitly cached, this will be repeated each time.
        #    # However, this has the same complexity as filtering by side.
        #    self.findPortIndices()
        #
        #indices = self.portSideIndices[side]
        # if indices is None:
        #    return []
        # else:
        #    # We must create a new sublist each time,
        #    # because the order of the ports on one side can change.
        #    return self.ports[indices[0]:indices[1]]

    def setLayer(self, layer):
        self.layer = layer

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)


class LayoutExternalPort(LNode):
    def __init__(self, graph: "Layout", name: str=None, direction=None):
        super(LayoutExternalPort, self).__init__(graph, name)
        self.direction = direction


class LNodeLayer(list):
    def __init__(self, graph: "Layout" = None):
        self.graph = graph
        self.inGraphIndex = len(graph.layers)

    def append(self, v):
        v.layer = self
        return list.append(self, v)

    def extend(self, iterable):
        for v in iterable:
            self.append(v)


class LEdge():
    def __init__(self, signal: RtlSignal, name: str):
        self.name = name
        self.signal = signal
        self.src = None
        self.srcNode = None
        self.dst = None
        self.dstNode = None
        self.reversed = False

    def setSrcDst(self, src: LPort, dst: LPort):
        self.src = src
        self.srcNode = src.getNode()
        self.dst = dst
        self.dstNode = dst.getNode()
        src.outgoingEdges.append(self)
        dst.incomingEdges.append(self)

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
        self.childGraphs = []
        self.parent = None
        self.parentLnode = None
        self.graphProperties = set()
        self.edgeRouting = None
        self.random = None

        # The graph contains comment boxes.
        self.p_comments = False
        # The graph contains dummy nodes representing external ports.
        self.p_externalPorts = False
        # The graph contains hyperedges.
        self.p_hyperedges = False
        # The graph contains hypernodes (nodes that are marked as such).
        self.p_hypernodes = False
        # The graph contains ports that are not free for positioning.
        self.p_nonFreePorts = False
        # The graph contains ports on the northern or southern side.
        self.p_northSouthPorts = False
        # The graph contains self-loops.
        self.p_selfLoops = False
        # The graph contains node labels.
        self.p_centerLabels = False
        # The graph contains head or tail edge labels.
        self.p_endLabels = False
        # The graph's nodes are partitioned.
        self.p_partitions = False

    def getLayerlessNodes(self):
        """
        Returns the list of nodes that are not currently assigned to a layer.
        """
        return self.nodes

    def add_stm_as_unit(self, stm: HdlStatement) -> LNode:
        u = LNode(self, name=stm.__class__.__name__)
        u.setOriginObj(stm)
        self._node2lnode[stm] = u
        u.addPort("out", INTF_DIRECTION.MASTER, PortSide.WEST)
        u.addPort("in",  INTF_DIRECTION.SLAVE,  PortSide.EAST)
        self.nodes.append(u)
        return u

    def add_node(self, origin: Unit, name: str) -> LNode:
        n = LNode(self, origin._name)
        n.originObj = origin

        self.nodes.append(n)
        return n

    def add_edge(self, signal, name, src: LPort, dst: LPort):
        e = LEdge(signal, name)
        e.setSrcDst(src, dst)
        self.edges.append(e)
        return e


def getParentUnit(intf):
    while isinstance(intf._parent, Interface):
        intf = intf._parent

    return intf._parent
