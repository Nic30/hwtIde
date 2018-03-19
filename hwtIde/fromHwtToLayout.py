from typing import Set, List, Union

from hwt.hdl.assignment import Assignment
from hwt.hdl.portItem import PortItem
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.unit import Unit
from layeredGraphLayouter.containers.lNode import LayoutExternalPort, LNode
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.containers.lGraph import Layout
from layeredGraphLayouter.containers.lEdge import LEdge
from layeredGraphLayouter.containers.constants import PortType, PortSide
from hwt.hdl.constants import INTF_DIRECTION
from hwt.hdl.statements import HdlStatement


def getParentUnit(intf):
    while isinstance(intf._parent, Interface):
        intf = intf._parent

    return intf._parent


def PortType_from_dir(direction):
    if direction == INTF_DIRECTION.SLAVE:
        return PortType.INPUT
    elif direction == INTF_DIRECTION.MASTER:
        return PortType.OUTPUT
    else:
        raise ValueError(direction)


def origin_obj_of_port(intf):
    d = intf._direction
    d = PortType_from_dir(d)

    if intf._interfaces:
        origin = intf
    elif d == PortType.OUTPUT:
        # has hierarchy
        origin = intf._sigInside.endpoints[0]
        assert isinstance(origin, PortItem), (intf, origin)
    elif d == PortType.INPUT:
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
    d = PortType_from_dir(d)

    if reverseDirection:
        d = PortType.opposite(d)

    new_lp = LPort(lp, intf._name, d, lp.side)
    new_lp.originObj = origin
    if intf._interfaces:
        for child_intf in intf:
            _add_port(new_lp, child_intf, reverseDirection=reverseDirection)

    lp.children.append(new_lp)
    new_lp.parent = lp
    lep.graph._node2lnode[origin] = new_lp

    return new_lp


def add_port_to_unit(ln: LNode, intf: Interface, reverseDirection=False):
    origin = origin_obj_of_port(intf)

    d = intf._direction
    d = PortType_from_dir(d)
    if reverseDirection:
        d = PortType.opposite(d)

    p = LNode_addPortFromHdl(ln, origin,
                             d,
                             intf._name)
    for _intf in intf._interfaces:
        _add_port(ln, p, _intf, reverseDirection=reverseDirection)


def add_port(la: Layout, intf: Interface):
    """
    Add LayoutExternalPort for interface
    """
    d = PortType_from_dir(intf._direction)
    ext_p = LayoutExternalPort(
        la, intf._name,
        PortType.opposite(d))
    ext_p.originObj = origin_obj_of_port(intf)
    la.nodes.append(ext_p)
    add_port_to_unit(ext_p, intf, reverseDirection=True)

    return ext_p


def get_single_edge(ports) -> LEdge:
    assert len(ports) == 1
    p = ports[0]
    ce = p.incomingEdges
    if ce:
        assert not p.outgoingEdges
    else:
        ce = p.outgoingEdges

    assert len(ce) == 1

    return ce[0]


def reduce_useless_assignments(la: Layout):
    do_update = False
    for n in la.nodes:
        if isinstance(n.originObj, Assignment) and not n.originObj.indexes:
            if not do_update:
                edges = set(la.edges)
                nodes = set(la.nodes)
                do_update = True

            nodes.remove(n)
            in_e = get_single_edge(n.east)
            out_e = get_single_edge(n.west)
            edges.remove(out_e)

            in_e.dst.incomingEdges.remove(in_e)
            in_e.dst = out_e.dst
            in_e.dstNode = out_e.dstNode
            out_e.dst.incomingEdges.remove(out_e)
            out_e.dst.incomingEdges.append(in_e)

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
    inEdges = port.incomingEdges
    outEdges = port.outgoingEdges

    if port.children:
        ch_cnt = 0
        assert not inEdges, (port, port.children, inEdges)
        assert not outEdges, (port, port.children, outEdges)

        for ch in port.children:
            ch_cnt += count_directly_connected(ch, result)

        return ch_cnt

    elif not inEdges and not outEdges:
        print("Warning", port, "not connected")
        return 0
    else:
        assert len(inEdges) + len(outEdges) == 1, (port,
                                                   len(inEdges), len(outEdges))
        if inEdges:
            e = inEdges[0]
        else:
            e = outEdges[0]

        if e.src.name != e.dst.name:
            return 0

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
        if child.direction == PortType.OUTPUT:
            target_ch = edge.dst
        elif child.direction == PortType.INPUT:
            target_ch = edge.src
        else:
            raise ValueError(child.direction)

        assert target_ch.parent is new_target

        # disconnect selected children from this port and target
        children_to_destroy.add(child)
        on_target_children_to_destroy.add(target_ch)

        edges_to_remove.add(edge)
        for p in (child, target_ch):
            removed = False
            try:
                p.incomingEdges.remove(edge)
                removed = True
            except ValueError:
                pass
            try:
                p.outgoingEdges.remove(edge)
                removed = True
            except ValueError:
                pass
            assert removed

    # destroy children of new target and this port if possible
    port.children = list(where(port.children,
                               lambda ch: ch not in children_to_destroy))
    new_target.children = list(where(new_target.children,
                                     lambda ch: ch not in on_target_children_to_destroy))

    # connect this port to new target as it was connected by children before
    # [TODO] names for new edges
    if port.direction == PortType.OUTPUT:
        la.add_edge(port, new_target)
    elif port.direction == PortType.INPUT:
        la.add_edge(new_target, port)
    else:
        raise NotImplementedError(port.direction)


def flatten_port(port: LPort):
    yield port
    if port.children:
        for ch in port.children:
            yield from flatten_port(ch)
        port.children.clear()


def _flatten_ports_side(side: List[LNode]) -> List[LNode]:
    new_side = []
    for i in side:
        for new_p in flatten_port(i):
            new_side.append(new_p)
    return new_side


def flatten_ports(la: Layout):
    """
    Flatten ports to simplify layout generation

    :attention: children property is destroyed, parent property stays same
    """
    for u in la.nodes:
        u.west = _flatten_ports_side(u.west)
        u.east = _flatten_ports_side(u.east)
        u.north = _flatten_ports_side(u.north)
        u.south = _flatten_ports_side(u.south)


def resolve_shared_connections(la: Layout):
    """
    Walk all ports on all nodes and group subinterface connections to only parent interface
    connection if it is possible
    """
    edges_to_remove = set()
    for u in la.nodes:
        for p in u.iterPorts():
            port_try_reduce(la, p, edges_to_remove)

    for e in edges_to_remove:
        la.edges.remove(e)


def add_stm_as_unit(la: Layout, stm: HdlStatement) -> LNode:
    u = la.add_node(originObj=stm, name=stm.__class__.__name__)
    u.addPort("out", PortType.OUTPUT, PortSide.WEST)
    u.addPort("in",  PortType.INPUT,  PortSide.EAST)
    return u


def LNode_addPortFromHdl(node, origin: Union[Interface, PortItem],
                         direction: PortType,
                         name: str):
    if direction == PortType.OUTPUT:
        side = PortSide.WEST
    elif direction == PortType.INPUT:
        side = PortSide.EAST
    else:
        raise ValueError(direction)

    p = node.addPort(name, direction, side)
    p.originObj = origin
    node.graph._node2lnode[origin] = p
    return p


def Unit_to_Layout(u: Unit) -> Layout:
    """
    Build Layout instance from Unit instance

    :attention: unit has to be synthesized
    """

    la = Layout()
    toL = la._node2lnode
    # create subunits
    for su in u._units:
        n = la.add_node(name=su._name, originObj=su)
        for intf in su._interfaces:
            add_port_to_unit(n, intf)

    # create subunits from statements
    for stm in u._ctx.statements:
        n = add_stm_as_unit(la, stm)

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
                src = la_stm.west[0]

            for stm in s.endpoints:
                la_stm = toL[stm]
                if isinstance(stm, PortItem):
                    dst = la_stm
                else:
                    dst = la_stm.east[0]
                la.add_edge(src, dst, name=s.name, originObj=s)

    reduce_useless_assignments(la)
    resolve_shared_connections(la)
    flatten_ports(la)

    for n in la.nodes:
        n.initDim()

    return la
