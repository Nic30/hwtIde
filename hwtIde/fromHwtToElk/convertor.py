from typing import Optional

from elkContainer.lNode import LNode
from fromHwtToElk.extractSplits import extractSplits
from fromHwtToElk.flattenPorts import flattenPorts
from fromHwtToElk.flattenTrees import flattenTrees
from fromHwtToElk.mergeSplitsOnInterfaces import mergeSplitsOnInterfaces
from fromHwtToElk.reduceUselessAssignments import reduceUselessAssignments
from fromHwtToElk.resolveSharedConnections import resolveSharedConnections
from fromHwtToElk.utils import addOperatorAsLNode, addPortToLNode,\
    addStmAsLNode, addPort, ValueAsLNode, ternaryAsSimpleAssignment,\
    isUselessTernary
from hwt.hdl.operator import Operator, isConst
from hwt.hdl.portItem import PortItem
from hwt.synthesizer.unit import Unit
from elkContainer.constants import PortType, PortSide
from hwt.hdl.assignment import Assignment


def lazyLoadNode(root, stm, toL):
    try:
        return toL[stm]
    except KeyError:
        if isinstance(stm, Operator):
            if isUselessTernary(stm):
                node = ternaryAsSimpleAssignment(root, stm)
            else:
                node = addOperatorAsLNode(root, stm)
            toL[stm] = node
            return node
        else:
            raise


def walkSignalEndpointsToStatements(sig):
    assert sig.hidden, sig
    for ep in sig.endpoints:
        if isinstance(ep, Operator):
            yield from walkSignalEndpointsToStatements(ep.result)
        else:
            yield ep


class Signal2stmPortCtx(dict):
    def __init__(self, stmNode: LNode):
        self.stmNode = stmNode

    def register(self, sig, portType: PortType):
        p = self.get(sig, None)
        if p is not None:
            return p

        if portType == PortType.INPUT:
            side = PortSide.WEST
        elif portType == portType.OUTPUT:
            side = PortSide.EAST
        else:
            raise ValueError(portType)

        p = self.stmNode.addPort(sig.name, portType, side)
        self[sig] = p
        return p


def sortStatementPorts(root):
    pass


def renderContentOfStatemtn(root, toL):
    stm = root.originObj
    FF = "FF"
    LATCH = "LATCH"
    MUX = "MUX"
    RAM = "RAM"
    CONNECTION = "CONNECTION"
    signalsToRedner = set()

    # walk statements and render muxs and memories
    if isinstance(stm, Assignment):
        n = root.addNode(name=CONNECTION, originObj=(CONNECTION, stm))
        toL[n.originObj] = n
        n.addPort("", PortType.INPUT, PortSide.WEST)
        if stm.indexes:
            n.addPort("", PortType.INPUT, PortSide.WEST)
        n.addPort("", PortType.OUTPUT, PortSide.EAST)
    else:
        raise NotImplementedError()


def UnitToLNode(u: Unit, node: Optional[LNode]=None, toL: Optional[dict]=None) -> LNode:
    """
    Build LNode instance from Unit instance

    :attention: unit has to be synthesized
    """
    if toL is None:
        toL = {}
    if node is None:
        root = LNode(name=u._name, originObj=u, node2lnode=toL)
    else:
        root = node

    stmPorts = {}

    # create subunits
    for su in u._units:
        n = root.addNode(name=su._name, originObj=su)
        #UnitToLNode(su, n, toL)
        for intf in su._interfaces:
            addPortToLNode(n, intf)

    # create subunits from statements
    for stm in u._ctx.statements:
        n = addStmAsLNode(root, stm)
        stmPorts[n] = Signal2stmPortCtx(n)
        renderContentOfStatemtn(n, toL)

    # create ports
    for intf in u._interfaces:
        addPort(root, intf)

    # pending and seen set because we do not want to draw
    # hidden signals in statements
    # we need to create connections for signals only outside of statements
    def connect_signal(s):
        driverPorts = set()
        endpointPorts = set()

        def addEndpoint(ep):
            if isinstance(ep, PortItem):
                dst = toL[ep]
                endpointPorts.add(dst)
            else:
                laStm = toL[ep]
                dst = stmPorts[laStm].register(s, PortType.INPUT)
                endpointPorts.add(dst)

        # connect all drivers of this signal with all endpoints
        for stm in s.drivers:
            node = lazyLoadNode(root, stm, toL)

            if isinstance(stm, PortItem):
                src = node
            elif isinstance(stm, Operator):
                continue
                src = node.east[0]
                for op, opPort in zip(stm.operands, node.west):
                    if isConst(op):
                        n = ValueAsLNode(root, op)
                        root.addEdge(n.east[0], opPort, originObj=op)
            else:
                src = stmPorts[node].register(s, PortType.OUTPUT)

            driverPorts.add(src)

        for stm in s.endpoints:
            if isinstance(stm, Operator):
                for ep in walkSignalEndpointsToStatements(stm.result):
                    addEndpoint(ep)
            else:
                addEndpoint(stm)

        for src in driverPorts:
            for dst in endpointPorts:
                root.addEdge(src, dst, name=s.name, originObj=s)

    # connect nets
    for s in u._ctx.signals:
        if not s.hidden:
            connect_signal(s)

    # optimizations
    reduceUselessAssignments(root)
    extractSplits(root, u._ctx.signals, toL)
    flattenTrees(root, lambda node: node.name == "CONCAT")
    mergeSplitsOnInterfaces(root)
    resolveSharedConnections(root)

    sortStatementPorts(root)
    # required for to json conversion
    flattenPorts(root)

    return root
