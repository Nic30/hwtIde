import os
from typing import Set, List

from hwt.hdl.assignment import Assignment
from hwt.hdl.constants import INTF_DIRECTION
from hwt.hdl.portItem import PortItem
from hwt.interfaces.std import Signal
from hwt.pyUtils.arrayQuery import single
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl
from hwtLib.amba.axis import AxiStream
from hwtLib.samples.hierarchy.simpleSubunit import SimpleSubunit
from hwtLib.samples.simple import SimpleUnit
from hwtLib.samples.simpleAxiStream import SimpleUnitAxiStream
from layout.containers import Layout, LayoutPort, LayoutExternalPort, LayoutNode,\
    LayoutEdge
from layout.examples import LinearDualSubunit, DualSubunit
from layout.greedyCycleBreaker import GreedyCycleBreaker
from layout.minWidthLayerer import MinWidthLayerer
from layout.toMxGraph import ToMxGraph
from layout.toSvg import ToSvg
import xml.etree.ElementTree as etree


def origin_obj_of_port(intf):
    d = intf._direction
    if intf._interfaces:
        origin = intf
    elif d == INTF_DIRECTION.MASTER:
        # has hierarchy
        origin = intf._sigInside.endpoints[0]
        assert isinstance(origin, PortItem), (intf, origin)
    elif d == INTF_DIRECTION.SLAVE:
        origin = intf._sigInside.drivers[0]
        assert isinstance(origin, PortItem), (intf, origin)
    else:
        raise ValueError(d)

    return origin


def _add_port(lep: LayoutExternalPort, lp: LayoutPort, intf: Interface, reverseDirection=False):
    """
    add port to LayoutPort for interface
    """
    origin = origin_obj_of_port(intf)
    d = intf._direction
    if reverseDirection:
        d = INTF_DIRECTION.opposite(d)

    new_lp = LayoutPort(origin, lp, intf._name, d)
    if intf._interfaces:
        for child_intf in intf:
            _add_port(new_lp, child_intf, reverseDirection=reverseDirection)

    lp.children.append(new_lp)
    new_lp.parent = lp
    lep._port_obj_map[origin] = new_lp

    return new_lp


def add_port_to_unit(ln: LayoutNode, intf: Interface, reverseDirection=False):
    origin = origin_obj_of_port(intf)

    d = intf._direction
    if reverseDirection:
        d = INTF_DIRECTION.opposite(d)

    p = ln.add_port(origin,
                    d,
                    intf._name)
    for _intf in intf._interfaces:
        _add_port(ln, p, _intf, reverseDirection=reverseDirection)


def add_port(la: Layout, intf: Interface):
    """
    Add LayoutExternalPort for interface
    """
    origin = origin_obj_of_port(intf)
    ext_p = LayoutExternalPort(
        origin, intf._name,
        INTF_DIRECTION.opposite(intf._direction),
        la._node2lnode)
    la.nodes.append(ext_p)
    add_port_to_unit(ext_p, intf, reverseDirection=True)

    return ext_p


def get_single_edge(ports) -> LayoutEdge:
    assert len(ports) == 1
    ce = ports[0].connectedEdges
    assert len(ce) == 1
    return ce[0]


def reduce_useless_assignments(la: Layout):
    do_update = False
    for n in la.nodes:
        if isinstance(n.origin, Assignment) and not n.origin.indexes:
            if not do_update:
                edges = set(la.edges)
                nodes = set(la.nodes)
                do_update = True

            nodes.remove(n)
            in_e = get_single_edge(n.left)
            out_e = get_single_edge(n.right)
            edges.remove(out_e)

            in_e.dst.connectedEdges.remove(in_e)
            in_e.dst = out_e.dst
            in_e.dstNode = out_e.dstNode
            out_e.dst.connectedEdges.remove(out_e)
            out_e.dst.connectedEdges.append(in_e)

    if do_update:
        la.edges = list(edges)
        la.nodes = list(nodes)


def get_connected_node(port: LayoutPort):
    assert len(port.connectedEdges) == 1
    e = port.connectedEdges[0]
    raise NotImplementedError()
    if e.src is port:
        raise NotImplementedError()
    else:
        assert e.dst is port


def count_directly_connected(port: LayoutPort, result: dict) -> int:
    """
    Count how many ports are directly connected to other nodes

    :return: cumulative sum of port counts
    """
    edges = port.connectedEdges
    if port.children:
        ch_cnt = 0
        assert not edges, (port, edges)
        for ch in port.children:
            ch_cnt += count_directly_connected(ch, result)
        return ch_cnt
    elif not edges:
        print("Warning", port, "not connected")
    else:
        assert len(edges) == 1, (port, len(edges))
        e = edges[0]
        if e.src is port:
            p = e.dst.parent
        else:
            assert e.dst is port
            p = e.src.parent

        if not isinstance(p, LayoutNode):
            result[p] = result.get(p, 0) + 1

        return 1


def port_try_reduce(port: LayoutPort,
                    nodes_to_remove: Set[LayoutNode],
                    edges_to_remove: Set[LayoutNode],
                    new_edges: List[LayoutEdge]):
    """
    Check if majority of children is connected to same port
    if it is the case reduce children and connect this port instead children
    """
    if not port.children:
        return

    for p in port.children:
        port_try_reduce(p, nodes_to_remove, edges_to_remove, new_edges)

    target_nodes = {}
    ch_cnt = count_directly_connected(port, target_nodes)
    if not target_nodes:
        return

    n, cnt = max(target_nodes.items(), key=lambda x: x[1])
    if cnt < ch_cnt / 2 or cnt == 1 and ch_cnt == 2:
        return

    # disconnect selected children and destroy them if possible
    # destroy childrens of new target if possible
    # connect this port to new target as it was connected by childrens before
    print("[TODO] reduce children of", port)


def flatten_port(port: LayoutPort):
    yield port
    if port.children:
        for ch in port.children:
            yield from flatten_port(ch)
        port.children.clear()


def resolve_child_ports(la: Layout):
    """
    Walk all ports on all nodes and group subinterface connections to only parent interface
    connection if it is possible otherwise flatten ports to simplify layout generation
    """
    nodes_to_remove = set()
    edges_to_remove = set()
    new_edges = []
    for u in la.nodes:
        new_inputs = []
        new_outputs = []
        for i in u.left:
            port_try_reduce(i, nodes_to_remove, edges_to_remove, new_edges)
            for new_i in flatten_port(i):
                new_inputs.append(new_i)

        for o in u.right:
            port_try_reduce(o, nodes_to_remove, edges_to_remove, new_edges)
            for new_o in flatten_port(o):
                new_outputs.append(new_o)

        u.left = new_inputs
        u.right = new_outputs

    for n in nodes_to_remove:
        la.nodes.remove(n)

    for e in edges_to_remove:
        la.edges.remove(e)

    la.edges.extend(new_edges)


def Unit_to_Layout(u: Unit) -> Layout:
    """
    Build Layout instance from Unit instance

    :attention: unit has to be synthesized
    """

    la = Layout()
    toL = la._node2lnode
    # create subunits
    for su in u._units:
        n = la.add_node(su, su._name)
        for intf in su._interfaces:
            add_port_to_unit(n, intf)

    # create subunits from statements
    for stm in u._ctx.statements:
        n = la.add_stm_as_unit(stm)
        toL.update(n._port_obj_map)

    # create ports
    for intf in u._interfaces:
        add_port(la, intf)

    # connect nets
    for s in u._ctx.signals:
        if not s.hidden:
            assert len(s.drivers) == 1, s
            stm = s.drivers[0]
            la_stm = toL[stm]
            if isinstance(stm, PortItem):
                src = la_stm
            else:
                src = la_stm.right[0]

            for stm in s.endpoints:
                la_stm = toL[stm]
                if isinstance(stm, PortItem):
                    dst = la_stm
                else:
                    dst = la_stm.left[0]
                la.add_edge(s, s.name, src, dst)

    reduce_useless_assignments(la)
    resolve_child_ports(la)

    for n in la.nodes:
        n.initDim()

    return la


if __name__ == "__main__":
    #u = LinearDualSubunit()
    u = DualSubunit(AxiStream)
    toRtl(u)
    g = Unit_to_Layout(u)
    cycleBreaker = GreedyCycleBreaker()
    cycleBreaker.process(g)

    layer = MinWidthLayerer()
    layer.process(g)

    if not g.layers:
        nodes = g.nodes
        nodes.sort(key=lambda n: n.mark)
        for n in nodes:
            g.layers.append([n, ])
    x_step = max(g.nodes, key=lambda x: x.geometry.width).geometry.width + 100
    y_step = max(
        g.nodes, key=lambda x: x.geometry.height).geometry.height + 100

    x_offset = 0
    for i, nodes in enumerate(g.layers):
        nodes.sort(key=lambda n: n.mark)
        y_offset = 0
        for n in nodes:
            n.translate(x_offset, y_offset)
            y_offset += y_step
        x_offset += x_step

    g.width = x_offset
    g.height = y_offset

    def asSvg():
        with open(os.path.expanduser("~/test.svg"), "wb") as f:
            root = ToSvg().Layout_toSvg(g)
            s = etree.tostring(root)
            f.write(s)

    def asMxGraph():
        with open(os.path.expanduser("~/test.xml"), "wb") as f:
            root = ToMxGraph().Layout_toMxGraph(g)
            s = etree.tostring(root)
            f.write(s)

    asMxGraph()
    asSvg()
