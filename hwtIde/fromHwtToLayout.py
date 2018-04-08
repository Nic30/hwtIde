from typing import Set, List, Union

from hwt.hdl.assignment import Assignment
from hwt.hdl.portItem import PortItem
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.unit import Unit
from elkContainer.lNode import LayoutExternalPort, LNode
from elkContainer.lPort import LPort
from elkContainer.lEdge import LEdge
from elkContainer.constants import PortType, PortSide
from hwt.hdl.constants import INTF_DIRECTION
from hwt.hdl.statements import HdlStatement
from hwt.hdl.operator import Operator, isConst
from hwt.hdl.operatorDefs import AllOps
from hwt.hdl.value import Value


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

    new_lp = LPort(lp, d, lp.side, name=intf._name)
    new_lp.originObj = origin
    if intf._interfaces:
        for child_intf in intf._interfaces:
            _add_port(lep, new_lp, child_intf,
                      reverseDirection=reverseDirection)

    lp.children.append(new_lp)
    new_lp.parent = lp
    if lep._node2lnode is not None:
        lep._node2lnode[origin] = new_lp

    return new_lp


def add_port_to_unit(ln: LNode, intf: Interface, reverseDirection=False):
    origin = origin_obj_of_port(intf)

    d = intf._direction
    d = PortType_from_dir(d)
    if reverseDirection:
        d = PortType.opposite(d)

    p = LNode_add_portFromHdl(ln, origin,
                              d,
                              intf._name)
    for _intf in intf._interfaces:
        _add_port(ln, p, _intf, reverseDirection=reverseDirection)


def add_port(n: LNode, intf: Interface):
    """
    Add LayoutExternalPort for interface
    """
    d = PortType_from_dir(intf._direction)
    ext_p = LayoutExternalPort(
        n, intf._name, d, node2lnode=n._node2lnode)
    ext_p.originObj = origin_obj_of_port(intf)
    n.children.append(ext_p)
    add_port_to_unit(ext_p, intf, reverseDirection=True)

    return ext_p


def get_single_port(ports: List[LPort]) -> LEdge:
    assert len(ports) == 1, ports
    return ports[0]


def remove_edge(edge: LEdge):
    edge.dst.incomingEdges.remove(edge)
    edge.src.outgoingEdges.remove(edge)
    edge.dst = edge.dstNode = edge.src = edge.srcNode = None


def reduce_useless_assignments(root: LNode):
    do_update = False
    for n in root.children:
        if isinstance(n.originObj, Assignment) and not n.originObj.indexes and len(n.originObj._inputs) == 1:
            if not do_update:
                nodes = set(root.children)
                do_update = True
            nodes.remove(n)

            srcPorts = []
            dstPorts = []

            inP = get_single_port(n.west)
            outP = get_single_port(n.east)
            assert not inP.outgoingEdges, inP
            for e in inP.incomingEdges:
                sPort = e.src
                assert sPort is not outP
                srcPorts.append(sPort)
                remove_edge(e)

            assert not outP.incomingEdges, inP
            for e in outP.outgoingEdges:
                dPort = e.dst
                assert dPort is not inP
                dstPorts.append(dPort)
                remove_edge(e)

            for srcPort in srcPorts:
                for dstPort in dstPorts:
                    root.add_edge(srcPort, dstPort)
    if do_update:
        root.children = list(nodes)


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


def port_try_reduce(root: LNode, port: LPort):
    """
    Check if majority of children is connected to same port
    if it is the case reduce children and connect this port instead children
    """
    if not port.children:
        return

    for p in port.children:
        port_try_reduce(root, p)

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
        root.add_edge(port, new_target)
    elif port.direction == PortType.INPUT:
        root.add_edge(new_target, port)
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


def flatten_ports(root: LNode):
    """
    Flatten ports to simplify layout generation

    :attention: children property is destroyed, parent property stays same
    """
    for u in root.children:
        u.west = _flatten_ports_side(u.west)
        u.east = _flatten_ports_side(u.east)
        u.north = _flatten_ports_side(u.north)
        u.south = _flatten_ports_side(u.south)


def resolve_shared_connections(root: LNode):
    """
    Walk all ports on all nodes and group subinterface connections to only parent interface
    connection if it is possible
    """
    for u in root.children:
        for p in u.iterPorts():
            port_try_reduce(root, p)


def add_stm_as_unit(root: LNode, stm: HdlStatement) -> LNode:
    u = root.add_node(originObj=stm, name=stm.__class__.__name__)
    for i, _ in enumerate(stm._inputs):
        u.add_port("i%d" % i,  PortType.INPUT,  PortSide.WEST)
    for i, _ in enumerate(stm._outputs):
        u.add_port("o%d" % i, PortType.OUTPUT, PortSide.EAST)
    return u


def add_index_as_node(root: LNode, op: Operator) -> LNode:
    u = root.add_node(originObj=op, name="Index")
    u.add_port("out", PortType.OUTPUT, PortSide.EAST)
    u.add_port("in",  PortType.INPUT,  PortSide.WEST)
    u.add_port("index",  PortType.INPUT,  PortSide.WEST)
    return u


def add_operator_as_node(root: LNode, op: Operator):
    if op.operator == AllOps.INDEX:
        return add_index_as_node(root, op)
    else:
        u = root.add_node(originObj=op, name=op.operator.id)
        u.add_port("out", PortType.OUTPUT, PortSide.EAST)
        for i in range(len(op.operands)):
            u.add_port("in%d" % i,  PortType.INPUT,  PortSide.WEST)
        return u


def LNode_add_portFromHdl(node, origin: Union[Interface, PortItem],
                          direction: PortType,
                          name: str):
    if direction == PortType.OUTPUT:
        side = PortSide.EAST
    elif direction == PortType.INPUT:
        side = PortSide.WEST
    else:
        raise ValueError(direction)

    p = node.add_port(name, direction, side)
    p.originObj = origin
    if node._node2lnode is not None:
        node._node2lnode[origin] = p
    return p


def Value_as_LNode(root: LNode, val: Value):
    u = root.add_node(originObj=val, name=repr(val))
    u.add_port("out", PortType.OUTPUT, PortSide.EAST)
    return u


def Unit_to_LNode(u: Unit) -> LNode:
    """
    Build LNode instance from Unit instance

    :attention: unit has to be synthesized
    """

    toL = {}
    root = LNode(name=u._name, originObj=u, node2lnode=toL)
    # create subunits
    for su in u._units:
        n = root.add_node(name=su._name, originObj=su)
        for intf in su._interfaces:
            add_port_to_unit(n, intf)

    # create subunits from statements
    for stm in u._ctx.statements:
        n = add_stm_as_unit(root, stm)

    # create ports
    for intf in u._interfaces:
        add_port(root, intf)

    # pending and seen set because we do not want to draw
    # hidden signals in statements
    # we need to create connections for signals only outside of statements
    def connect_signal(s):
        driverPorts = set()
        endpointPorts = set()

        # connect all drivers of this signal with all endpoints
        for stm in s.drivers:
            try:
                node = toL[stm]
            except KeyError:
                if isinstance(stm, Operator):
                    toL[stm] = node = add_operator_as_node(root, stm)
                else:
                    raise

            if isinstance(stm, PortItem):
                src = node
            elif isinstance(stm, Operator):
                src = node.east[0]
                for i, (op, opPort) in enumerate(zip(stm.operands, node.west)):
                    if isConst(op):
                        n = Value_as_LNode(root, op)
                        root.add_edge(n.east[0], opPort)
            else:
                src = node.east[stm._outputs.index(s)]

            driverPorts.add(src)

        for stm in s.endpoints:
            if isinstance(stm, Operator):
                try:
                    node = toL[stm]
                except KeyError:
                    toL[stm] = node = add_operator_as_node(root, stm)

                for i, op in enumerate(stm.operands):
                    if op is s:
                        src = node.west[i]
                        endpointPorts.add(src)

            elif isinstance(stm, PortItem):
                dst = toL[stm]
                endpointPorts.add(dst)
            else:
                # [TODO] pretty statements
                laStm = toL[stm]
                dst = laStm.west[stm._inputs.index(s)]
                endpointPorts.add(dst)

        for src in driverPorts:
            for dst in endpointPorts:
                root.add_edge(src, dst, name=s.name, originObj=s)

    # connect nets
    for s in u._ctx.signals:
        # if not s.hidden:
        connect_signal(s)

    # while pending_signals:
    #    s = pending_signals.pop()
    #    connect_signal(s)

    reduce_useless_assignments(root)
    resolve_shared_connections(root)
    flatten_ports(root)

    return root
