from layout.containers.lNode import LNode
from layout.containers.constants import PortType, PortSide
from hwt.hdl.statements import HdlStatement
from layout.containers.lPort import LPort
from layout.containers.lEdge import LEdge
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.unit import Unit


class LNodeLayer(list):
    def __init__(self, graph: "Layout" = None):
        self.graph = graph
        self.inGraphIndex = len(graph.layers)
        self.graph.layers.append(self)

    def append(self, v):
        v.layer = self
        return list.append(self, v)

    def extend(self, iterable):
        for v in iterable:
            self.append(v)


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

        self.thoroughness = 1

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
        u.addPort("out", PortType.OUTPUT, PortSide.WEST)
        u.addPort("in",  PortType.INPUT,  PortSide.EAST)
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

    def append_layer(self, nodes):
        layer = LNodeLayer(self)
        layer.extend(nodes)
        return layer


def getParentUnit(intf):
    while isinstance(intf._parent, Interface):
        intf = intf._parent

    return intf._parent
