from typing import Optional

from elkContainer.constants import PortType, PortSide, PortConstraints
from elkContainer.lNode import LNode
from fromHwtToElk.extractSplits import extractSplits
from fromHwtToElk.flattenPorts import flattenPorts
from fromHwtToElk.flattenTrees import flattenTrees
from fromHwtToElk.mergeSplitsOnInterfaces import mergeSplitsOnInterfaces
from fromHwtToElk.resolveSharedConnections import resolveSharedConnections
from fromHwtToElk.statementRenderer import StatementRenderer, Signal2stmPortCtx
from fromHwtToElk.utils import addOperatorAsLNode, addPortToLNode,\
    addStmAsLNode, addPort, ternaryAsSimpleAssignment,\
    isUselessTernary
from hwt.hdl.operator import Operator
from hwt.hdl.portItem import PortItem
from hwt.synthesizer.unit import Unit
from fromHwtToElk.reduceUselessAssignments import reduceUselessAssignments


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


def connectSignalToStatements(s, toL, stmPorts, root):
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
        node = toL[stm]
        if isinstance(stm, PortItem):
            src = node
        elif isinstance(stm, Operator):
            continue
        else:
            src = stmPorts[node].register(s, PortType.OUTPUT)
        try:
            assert src.getNode().parent == root, (s, node)
        except AssertionError as e:
            raise
        driverPorts.add(src)

    for stm in s.endpoints:
        if isinstance(stm, Operator):
            for ep in walkSignalEndpointsToStatements(stm.result):
                addEndpoint(ep)
        else:
            addEndpoint(stm)

    if not (driverPorts and endpointPorts):
        print("Warning signal endpoints/drivers not discovered", s)
    for src in driverPorts:
        for dst in endpointPorts:
            e = root.addEdge(src, dst, name=s.name, originObj=s)
            print(e)


def sortStatementPorts(root):
    pass


def checkConsystency(node):
    for ch in node.children:
        for e in node.iterEdges():
            try:
                e.consystencyCheck()
            except AssertionError as ex:
                raise
        checkConsystency(ch)


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
        UnitToLNode(su, n, toL)
        for intf in su._interfaces:
            addPortToLNode(n, intf)

    # create subunits from statements
    for stm in u._ctx.statements:
        n = addStmAsLNode(root, stm)
        stmPorts[n] = Signal2stmPortCtx(n)

    # create ports
    for intf in u._interfaces:
        addPort(root, intf)

    # connect nets
    for s in u._ctx.signals:
        if not s.hidden:
            connectSignalToStatements(s, toL, stmPorts, root)

    for stm in u._ctx.statements:
        n = toL[stm]
        r = StatementRenderer(n, toL, stmPorts[n])
        r.renderContent()

    # optimizations
    reduceUselessAssignments(root)
    extractSplits(root, u._ctx.signals, toL)
    flattenTrees(root, lambda node: node.name == "CONCAT")
    mergeSplitsOnInterfaces(root)
    resolveSharedConnections(root)

    sortStatementPorts(root)
    # required for to json conversion
    flattenPorts(root)

    checkConsystency(root)

    return root
