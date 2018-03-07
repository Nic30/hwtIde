from itertools import chain
from typing import List

from hwt.hdl.constants import INTF_DIRECTION
from hwt.hdl.portItem import PortItem
from hwt.hdl.statements import HdlStatement
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import walkPhysInterfaces
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from layout.geometry import GeometryRect


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


class LayoutPort():
    """
    Port for component in component diagram

    :ivar portItem: original object which this node represents
    :ivar parent: parent unit of this port
    :ivar on_parent_index: index of this port on parent
    :ivar name: name of this port
    :ivar direction: direction of this port
    :ivar geometry: absolute geometry in layout
    """

    def __init__(self, portItem: PortItem, parent: "LayoutNode",
                 on_parent_index: int, name: str, direction):
        self.portItem = portItem
        self.parent = parent
        self.on_parent_index = on_parent_index
        self.name = name
        self.direction = direction
        self.geometry = None
        self.connectedEdges = []

    def getNode(self):
        p = self
        while True:
            p = p.parent
            if isinstance(p, LayoutNode):
                return p

    def initDim(self, width, x=0, y=0):
        _y = y + self.on_parent_index * PORT_HEIGHT
        self.geometry = GeometryRect(x, _y, width, PORT_HEIGHT)

    def translate(self, x, y):
        self.geometry.x += x
        self.geometry.y += y

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

    :ivar unit: original object which this node represents
    :ivar name: name of this unit
    :ivar class_name: name of class of this unit
    :ivar inputs: list of LayoutPort for each input of this unit
    :ivar outputs: list of LayoutPort for each output of this unit
    """

    def __init__(self, unit: Unit, name: str, class_name: str):
        self.unit = unit
        self.name = name
        self.class_name = class_name
        self.inputs = []
        self.outputs = []
        self.geometry = None
        self.parent = None

        # {PortItem: LayoutPort}
        self._port_obj_map = {}

        # used by cycle breaker
        self.indeg = 0
        self.outdeg = 0
        self.mark = 0
        # used by layerer
        self.normHeight = None

    def initPortDegrees(self):
        indeg = 0
        outdeg = 0
        for p in self.inputs:
            for e in p.connectedEdges:
                if not e.isSelfLoop():
                    indeg += 1

        for p in self.outputs:
            for e in p.connectedEdges:
                if not e.isSelfLoop():
                    outdeg += 1

        self.indeg = indeg
        self.outdeg = outdeg

    def getIncomingEdges(self):
        raise NotImplementedError()

    def getOutgoingEdges(self):
        raise NotImplementedError()

    def initDim(self, x=0, y=0):
        label_w = width_of_str(self.name)
        port_w = max(*map(lambda p: width_of_str(p.name),
                          chain(self.inputs, self.outputs)),
                     label_w / 2)
        width = max(port_w, label_w)
        height = UNIT_HEADER_OFFSET + \
            max(len(self.inputs), len(self.outputs)) * PORT_HEIGHT
        self.geometry = GeometryRect(x, y, width, height)

        port_width = width / 2
        for i in self.inputs:
            i.initDim(port_width, x=x, y=y + UNIT_HEADER_OFFSET)

        for o in self.outputs:
            o.initDim(port_width, x=x+port_width, y=y + UNIT_HEADER_OFFSET)

    def translate(self, x, y):
        self.geometry.x += x
        self.geometry.y += y
        for p in chain(self.inputs, self.outputs):
            p.translate(x, y)

    def add_port(self, intf: Interface, reverse_dir=False):
        d = intf._direction
        if d == INTF_DIRECTION.MASTER:
            if reverse_dir:
                portArr = self.inputs
            else:
                portArr = self.outputs
            pi = intf._sigInside.endpoints[0]
        elif d == INTF_DIRECTION.SLAVE:
            if reverse_dir:
                portArr = self.outputs
            else:
                portArr = self.inputs
            pi = intf._sigInside.drivers[0]
        else:
            raise Exception()

        assert isinstance(pi, PortItem)
        p = LayoutPort(pi, self, len(portArr), intf._name, d)
        portArr.append(p)
        self._port_obj_map[pi] = p

    @classmethod
    def fromIntfUnit(cls, u: Unit):
        self = cls(u, u._name, u.__class__.__name__)
        for intf in u._interfaces:
            self.add_port(intf)

        return self

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)


class LayoutExternalPort(LayoutNode):
    def __init__(self, intf):
        super(LayoutExternalPort, self).__init__(
            intf, intf._name, intf.__class__.__name__)
        self.add_port(intf, reverse_dir=True)
        self.direction = intf._direction


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
        u = LayoutNode(stm, stm.__class__.__name__,
                       stm.__class__.__name__)
        self._node2lnode[stm] = u
        u.outputs.append(LayoutPort(None, u, 0, "out", INTF_DIRECTION.MASTER))
        u.inputs.append(LayoutPort(None, u, 0, "in", INTF_DIRECTION.SLAVE))
        self.nodes.append(u)
        return u

    def add_unit(self, u: Unit) -> LayoutNode:
        n = LayoutNode.fromIntfUnit(u)
        self._node2lnode[u] = n
        self._node2lnode.update(n._port_obj_map)
        self.nodes.append(n)
        return n

    def add_port(self, intf: Interface) -> LayoutExternalPort:
        n = LayoutExternalPort(intf)
        self._node2lnode[intf] = n
        self._node2lnode.update(n._port_obj_map)
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

