from typing import Set

from hwt.hdl.assignment import Assignment
from hwt.hdl.constants import INTF_DIRECTION
from hwt.hdl.portItem import PortItem
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.unit import Unit
from layout.containers import Layout, LPort, LayoutExternalPort, LNode,\
    LEdge


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


def _add_port(lep: LayoutExternalPort, lp: LPort, intf: Interface,
              reverseDirection=False):
    """
    add port to LPort for interface
    """
    origin = origin_obj_of_port(intf)
    d = intf._direction
    if reverseDirection:
        d = INTF_DIRECTION.opposite(d)

    new_lp = LPort(origin, lp, intf._name, d, lp.side)
    if intf._interfaces:
        for child_intf in intf:
            _add_port(new_lp, child_intf, reverseDirection=reverseDirection)

    lp.children.append(new_lp)
    new_lp.parent = lp
    lep._port_obj_map[origin] = new_lp

    return new_lp


def add_port_to_unit(ln: LNode, intf: Interface, reverseDirection=False):
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


def get_single_edge(ports) -> LEdge:
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


def get_connected_node(port: LPort):
    assert len(port.connectedEdges) == 1
    e = port.connectedEdges[0]
    raise NotImplementedError()
    if e.src is port:
        raise NotImplementedError()
    else:
        assert e.dst is port


def count_directly_connected(port: LPort, result: dict) -> int:
    """
    Count how many ports are directly connected to other nodes

    :return: cumulative sum of port counts
    """
    edges = port.connectedEdges
    if port.children:
        ch_cnt = 0
        assert not edges, (port, port.children, edges)
        for ch in port.children:
            ch_cnt += count_directly_connected(ch, result)
        return ch_cnt
    elif not edges:
        print("Warning", port, "not connected")
    else:
        assert len(edges) == 1, (port, len(edges))
        e = edges[0]
        if e.src.name != e.dst.name:
            return

        if e.src is port:
            p = e.dst.parent
        else:
            assert e.dst is port
            p = e.src.parent

        if not isinstance(p, LNode):
            cons = result.get(p, [])
            cons.append((port, e))
            result[p] = cons

        return 1


def port_try_reduce(la: Layout,
                    port: LPort,
                    edges_to_remove: Set[LNode]):
    """
    Check if majority of children is connected to same port
    if it is the case reduce children and connect this port instead children
    """
    if not port.children:
        return

    for p in port.children:
        port_try_reduce(la, p, edges_to_remove)

    target_nodes = {}
    ch_cnt = count_directly_connected(port, target_nodes)
    if not target_nodes:
        # disconnected port
        return

    new_target, children_edge_to_destroy = max(target_nodes.items(),
                                               key=lambda x: len(x[1]))
    cnt = len(children_edge_to_destroy)
    if cnt < ch_cnt / 2 or cnt == 1 and ch_cnt == 2:
        # too small to few shared connection to reduce
        return

    children_to_destroy = set()
    on_target_children_to_destroy = set()
    for child, edge in children_edge_to_destroy:
        if child.direction == INTF_DIRECTION.MASTER:
            target_ch = edge.dst
        else:
            target_ch = edge.src
        assert target_ch.parent is new_target

        # disconnect selected children from this port and target
        children_to_destroy.add(child)
        on_target_children_to_destroy.add(target_ch)

        edges_to_remove.add(edge)
        for p in (child, target_ch):
            p.connectedEdges.remove(edge)

    # destroy children of new target and this port if possible
    port.children = list(where(port.children,
                               lambda ch: ch not in children_to_destroy))
    new_target.children = list(where(new_target.children,
                                     lambda ch: ch not in on_target_children_to_destroy))

    # connect this port to new target as it was connected by children before
    if port.direction == INTF_DIRECTION.MASTER:
        la.add_edge(None, "[TODO] name of merged connection", port, new_target)
    elif port.direction == INTF_DIRECTION.SLAVE:
        la.add_edge(None, "[TODO] name of merged connection", new_target, port)
    else:
        raise NotImplementedError(port.direction)


def flatten_port(port: LPort):
    yield port
    if port.children:
        for ch in port.children:
            yield from flatten_port(ch)
        port.children.clear()


def flatten_ports(la: Layout):
    """
    Flatten ports to simplify layout generation

    :attention: children property is destroyed, parent property stays same
    """
    for u in la.nodes:
        new_inputs = []
        new_outputs = []
        for i in u.left:
            for new_i in flatten_port(i):
                new_inputs.append(new_i)

        for o in u.right:
            for new_o in flatten_port(o):
                new_outputs.append(new_o)

        u.left = new_inputs
        u.right = new_outputs


def resolve_shared_connections(la: Layout):
    """
    Walk all ports on all nodes and group subinterface connections to only parent interface
    connection if it is possible
    """
    edges_to_remove = set()
    for u in la.nodes:
        for i in u.left:
            port_try_reduce(la, i, edges_to_remove)

        for o in u.right:
            port_try_reduce(la, o, edges_to_remove)

    for e in edges_to_remove:
        la.edges.remove(e)


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
    resolve_shared_connections(la)
    flatten_ports(la)

    for n in la.nodes:
        n.initDim()

    return la
