from typing import Set, List, Union

from hwt.hdl.assignment import Assignment
from hwt.hdl.portItem import PortItem
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.unit import Unit
from layeredGraphLayouter.containers.lNode import LayoutExternalPort, LNode
from layeredGraphLayouter.containers.lPort import LPort
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.containers.lEdge import LEdge
from layeredGraphLayouter.containers.constants import PortType, PortSide,\
    PortConstraints
from hwt.hdl.constants import INTF_DIRECTION
from hwt.hdl.statements import HdlStatement
from hwt.hdl.operator import Operator
from hwt.hdl.operatorDefs import AllOps
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase


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
        for child_intf in intf._interfaces:
            _add_port(lep, new_lp, child_intf,
                      reverseDirection=reverseDirection)

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


def add_port(la: LGraph, intf: Interface):
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


def get_single_port(ports: List[LPort]) -> LEdge:
    assert len(ports) == 1
    return ports[0]


def remove_edge(allEdges, edge: LEdge):
    edge.dst.incomingEdges.remove(edge)
    edge.src.outgoingEdges.remove(edge)
    allEdges.remove(edge)


def reduce_useless_assignments(la: LGraph):
    do_update = False
    for n in la.nodes:
        if isinstance(n.originObj, Assignment) and not n.originObj.indexes:
            if not do_update:
                edges = set(la.edges)
                nodes = set(la.nodes)
                do_update = True

            nodes.remove(n)

            srcPorts = []
            dstPorts = []

            inP = get_single_port(n.west)
            assert not inP.outgoingEdges, inP
            for in_e in inP.incomingEdges:
                srcPorts.append(in_e.src)
                remove_edge(edges, in_e)

            outP = get_single_port(n.east)
            assert not outP.incomingEdges, inP
            for out_e in outP.outgoingEdges:
                dstPorts.append(out_e.dst)
                remove_edge(edges, out_e)

            for srcPort in srcPorts:
                for dstPort in dstPorts:
                    new_e = la.add_edge(srcPort, dstPort)
                    edges.add(new_e)

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
        if len(inEdges) + len(outEdges) != 1:
            return 0

        if inEdges:
            e = inEdges[0]
        else:
            e = outEdges[0]

        # if is connected to different port
        if e.src.name != e.dst.name:
            return 0

        if e.src is port:
            p = e.dst.parent
        else:
            assert e.dst is port
            p = e.src.parent

        # if is part of interface which can be reduced
        if not isinstance(p, LNode):
            connections = result.get(p, [])
            connections.append((port, e))
            result[p] = connections

        return 1


def port_try_reduce(la: LGraph, port: LPort,
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


def flatten_ports(la: LGraph):
    """
    Flatten ports to simplify layout generation

    :attention: children property is destroyed, parent property stays same
    """
    for u in la.nodes:
        u.west = _flatten_ports_side(u.west)
        u.east = _flatten_ports_side(u.east)
        u.north = _flatten_ports_side(u.north)
        u.south = _flatten_ports_side(u.south)


def resolve_shared_connections(la: LGraph):
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


def add_stm_as_unit(la: LGraph, stm: HdlStatement) -> LNode:
    u = la.add_node(originObj=stm, name=stm.__class__.__name__)
    u.addPort("out", PortType.OUTPUT, PortSide.EAST)
    u.addPort("in",  PortType.INPUT,  PortSide.WEST)
    return u


def add_index_as_node(la: LGraph, op: Operator) -> LNode:
    u = la.add_node(originObj=op, name="Index")
    u.addPort("out", PortType.OUTPUT, PortSide.EAST)
    u.addPort("in",  PortType.INPUT,  PortSide.WEST)
    u.addPort("index",  PortType.INPUT,  PortSide.WEST)
    return u


def add_operator_as_node(la: LGraph, op: Operator):
    if op.operator == AllOps.INDEX:
        return add_index_as_node(la, op)
    else:
        u = la.add_node(originObj=op, name=op.operator.id)
        u.addPort("out", PortType.OUTPUT, PortSide.EAST)
        for i in range(len(op.operands)):
            u.addPort("in%d" % i,  PortType.INPUT,  PortSide.WEST)
        return u


def LNode_addPortFromHdl(node, origin: Union[Interface, PortItem],
                         direction: PortType,
                         name: str):
    if direction == PortType.OUTPUT:
        side = PortSide.EAST
    elif direction == PortType.INPUT:
        side = PortSide.WEST
    else:
        raise ValueError(direction)

    p = node.addPort(name, direction, side)
    p.originObj = origin
    node.graph._node2lnode[origin] = p
    return p


def Unit_to_LGraph(u: Unit) -> LGraph:
    """
    Build LGraph instance from Unit instance

    :attention: unit has to be synthesized
    """

    la = LGraph()
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

    # pending and seen set because we do not want to draw
    # hidden signals in statements
    # we need to create connections for signals only outside of statements
    pending_signals = set()
    seen_signals = set()

    def connect_signal(s):
        seen_signals.add(s)

        driverPorts = set()
        endpointPorts = set()

        # connect all drivers of this signal with all endpoints
        for stm in s.drivers:
            try:
                la_stm = toL[stm]
            except KeyError:
                if isinstance(stm, Operator):
                    toL[stm] = la_stm = add_operator_as_node(la, stm)
                else:
                    raise

            if isinstance(stm, PortItem):
                src = la_stm
            else:
                src = la_stm.east[0]
            driverPorts.add(src)

            for stm in s.endpoints:
                if isinstance(stm, Operator):
                    try:
                        node = toL[stm]
                    except KeyError:
                        toL[stm] = node = add_operator_as_node(la, stm)

                    for dst, op in zip(node.west, stm.operands):
                        if op is s:
                            endpointPorts.add(dst)
                        elif isinstance(op, RtlSignalBase) and op not in seen_signals:
                            pending_signals.add(op)
                        else:
                            pass
                            # [TODO] create nodes for constants
                    if stm.result not in seen_signals:
                        pending_signals.add(stm.result)

                    continue
                elif isinstance(stm, PortItem):
                    dst = toL[stm]
                    endpointPorts.add(dst)
                else:
                    # [TODO] pretty statements
                    dst = toL[stm].west[0]
                    endpointPorts.add(dst)

        for src in driverPorts:
            for dst in endpointPorts:
                la.add_edge(src, dst, name=s.name, originObj=s)

    # connect nets
    for s in u._ctx.signals:
        if not s.hidden:
            connect_signal(s)

    while pending_signals:
        s = pending_signals.pop()
        connect_signal(s)

    reduce_useless_assignments(la)
    resolve_shared_connections(la)
    flatten_ports(la)

    for n in la.nodes:
        n.initDim()

    return la
