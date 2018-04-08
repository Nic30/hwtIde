from typing import Union, List

from elkContainer.constants import PortType, PortSide
from elkContainer.lEdge import LEdge
from elkContainer.lNode import LayoutExternalPort, LNode
from elkContainer.lPort import LPort
from hwt.hdl.constants import INTF_DIRECTION
from hwt.hdl.operator import Operator
from hwt.hdl.operatorDefs import AllOps
from hwt.hdl.portItem import PortItem
from hwt.hdl.statements import HdlStatement
from hwt.hdl.value import Value
from hwt.synthesizer.interface import Interface


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
