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
from hwt.serializer.hwt.serializer import HwtSerializer
from hwt.synthesizer.interface import Interface
from hwt.hdl.types.defs import BIT
from hwt.hdl.assignment import Assignment


def toStr(obj):
    """
    Convert hwt object to string
    """
    return HwtSerializer.asHdl(obj, HwtSerializer.getBaseContext())


def getParentUnit(intf):
    while isinstance(intf._parent, Interface):
        intf = intf._parent

    return intf._parent


def PortTypeFromDir(direction):
    if direction == INTF_DIRECTION.SLAVE:
        return PortType.INPUT
    elif direction == INTF_DIRECTION.MASTER:
        return PortType.OUTPUT
    else:
        raise ValueError(direction)


def originObjOfPort(intf):
    d = intf._direction
    d = PortTypeFromDir(d)

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


def _addPort(n: LNode, lp: LPort, intf: Interface,
             reverseDirection=False):
    """
    add port to LPort for interface
    """
    origin = originObjOfPort(intf)
    d = intf._direction
    d = PortTypeFromDir(d)

    if reverseDirection:
        d = PortType.opposite(d)

    new_lp = LPort(lp, d, lp.side, name=intf._name)
    new_lp.originObj = origin
    if intf._interfaces:
        for child_intf in intf._interfaces:
            _addPort(n, new_lp, child_intf,
                     reverseDirection=reverseDirection)

    lp.children.append(new_lp)
    new_lp.parent = lp
    if n._node2lnode is not None:
        n._node2lnode[origin] = new_lp

    return new_lp


def addPortToLNode(ln: LNode, intf: Interface, reverseDirection=False):
    origin = originObjOfPort(intf)

    d = intf._direction
    d = PortTypeFromDir(d)
    if reverseDirection:
        d = PortType.opposite(d)

    p = LNodeAddPortFromHdl(ln, origin,
                            d,
                            intf._name)
    for _intf in intf._interfaces:
        _addPort(ln, p, _intf, reverseDirection=reverseDirection)


def addPort(n: LNode, intf: Interface):
    """
    Add LayoutExternalPort for interface
    """
    d = PortTypeFromDir(intf._direction)
    ext_p = LayoutExternalPort(
        n, intf._name, d, node2lnode=n._node2lnode)
    ext_p.originObj = originObjOfPort(intf)
    n.children.append(ext_p)
    addPortToLNode(ext_p, intf, reverseDirection=True)

    return ext_p


def getSinglePort(ports: List[LPort]) -> LEdge:
    assert len(ports) == 1, ports
    return ports[0]


def removeEdge(edge: LEdge):
    edge.dst.incomingEdges.remove(edge)
    edge.src.outgoingEdges.remove(edge)
    edge.dst = edge.dstNode = edge.src = edge.srcNode = None


def addStmAsLNode(root: LNode, stm: HdlStatement) -> LNode:
    bodyText = toStr(stm)
    u = root.addNode(
        originObj=stm, bodyText=bodyText)
    # for _ in stm._inputs:
    #    u.addPort(None,  PortType.INPUT,  PortSide.WEST)
    # for _ in stm._outputs:
    #    u.addPort(None, PortType.OUTPUT, PortSide.EAST)
    return u


def addIndexAsLNode(root: LNode, op: Operator) -> LNode:
    bodyText = toStr(op)
    u = root.addNode(originObj=op, name="Index", bodyText=bodyText)
    u.addPort("out", PortType.OUTPUT, PortSide.EAST)
    u.addPort("in",  PortType.INPUT,  PortSide.WEST)
    u.addPort("index",  PortType.INPUT,  PortSide.WEST)
    return u


def isUselessTernary(op):
    if op.operator == AllOps.TERNARY:
        ifTrue = op.operands[1]
        ifFalse = op.operands[2]
        if ifTrue._dtype == BIT and ifFalse._dtype == BIT:
            try:
                return bool(ifTrue) and not bool(ifFalse)
            except Exception:
                pass
    return False


def ternaryAsSimpleAssignment(root, op):
    originObj = Assignment(op.operands[0], op.result, virtualOnly=True)
    u = root.addNode(originObj=originObj, name="Assignment")
    u.addPort("", PortType.OUTPUT, PortSide.EAST)
    u.addPort("",  PortType.INPUT,  PortSide.WEST)
    return u


def addOperatorAsLNode(root: LNode, op: Operator, operandSigCheck=None):
    if op.operator == AllOps.INDEX:
        return addIndexAsLNode(root, op)
    else:
        u = root.addNode(originObj=op, name=op.operator.id)
        u.addPort(None, PortType.OUTPUT, PortSide.EAST)
        for op in op.operands:
            p = u.addPort(None,  PortType.INPUT,  PortSide.WEST)

            if isinstance(op, Value):
                v = ValueAsLNode(root, op).east[0]
                root.addEdge(v, p)
            elif operandSigCheck is not None:
                operandSigCheck(op, p)

        return u


def LNodeAddPortFromHdl(node, origin: Union[Interface, PortItem],
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
    if node._node2lnode is not None:
        node._node2lnode[origin] = p
    return p


def ValueAsLNode(root: LNode, val: Value):
    u = root.addNode(originObj=val, bodyText=toStr(val))
    u.addPort(None, PortType.OUTPUT, PortSide.EAST)
    return u
