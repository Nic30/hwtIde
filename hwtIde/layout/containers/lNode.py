from itertools import chain
from typing import List, Union

from hwt.hdl.portItem import PortItem
from hwt.synthesizer.interface import Interface
from layout.containers.constants import PortSide, PortType, NodeType,\
    PortConstraints
from layout.containers.geometry import GeometryRect
from layout.containers.lPort import LPort
from layout.containers.sizeConfig import UNIT_HEADER_OFFSET, PORT_HEIGHT,\
    width_of_str


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

    def iterSides(self):
        yield self.north
        yield self.east
        yield self.south
        yield self.west

    def getPorts(self, direction):
        for p in self.iterPorts():
            if p.direction == direction:
                yield p

    def initPortDegrees(self):
        indeg = 0
        outdeg = 0
        for p in self.iterPorts():
            d = p.direction
            for e in p.iterEdges():
                if not e.isSelfLoop():
                    if d == PortType.INPUT:
                        indeg += 1
                    elif d == PortType.OUTPUT:
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
            max(len(self.west), len(self.east)) * PORT_HEIGHT
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
                       direction: PortType,
                       name: str):
        if direction == PortType.OUTPUT:
            side = PortSide.WEST
        elif direction == PortType.INPUT:
            side = PortSide.EAST
        else:
            raise ValueError(direction)

        p = self.addPort(name, direction, side)
        p.originObj = origin
        self.graph._node2lnode[origin] = p
        return p

    def addPort(self, name, direction: PortType, side: PortSide):
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
        self.type = NodeType.EXTERNAL_PORT
