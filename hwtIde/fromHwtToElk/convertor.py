from typing import Optional

from elkContainer.lNode import LNode
from fromHwtToElk.connectSignalToStatements import connectSignalToStatements
from fromHwtToElk.extractSplits import extractSplits
from fromHwtToElk.flattenPorts import flattenPorts
from fromHwtToElk.flattenTrees import flattenTrees
from fromHwtToElk.mergeSplitsOnInterfaces import mergeSplitsOnInterfaces
from fromHwtToElk.reduceUselessAssignments import reduceUselessAssignments
from fromHwtToElk.resolveSharedConnections import resolveSharedConnections
from fromHwtToElk.statementRenderer import StatementRenderer
from fromHwtToElk.utils import addPortToLNode, addPort, NetCtxs
from hwt.synthesizer.unit import Unit
from fromHwtToElk.statementRendererUtils import addStmAsLNode, VirtualLNode
from hwt.hdl.portItem import PortItem


def sortStatementPorts(root):
    # [TODO]
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

    # {RtlSignal: NetCtx}
    netCtx = NetCtxs()

    # create subunits
    for su in u._units:
        n = root.addNode(name=su._name, originObj=su)
        UnitToLNode(su, n, toL)
        for intf in su._interfaces:
            addPortToLNode(n, intf)

    # create subunits from statements
    for stm in u._ctx.statements:
        n = addStmAsLNode(root, stm, stmPorts, netCtx)

    # create ports for this unit
    for intf in u._interfaces:
        addPort(root, intf)

    # render content of statements
    for stm in u._ctx.statements:
        n = toL.get(stm, None)
        if n is not None:
            if isinstance(n, VirtualLNode):
                # statement is not in wrap and does not need any port context
                p = None
            else:
                # statement is in wrap and needs a port context
                # to resolve port connections to wrap
                p = stmPorts[n]

            r = StatementRenderer(n, toL, p, netCtx)
            r.renderContent()

    # connect nets inside this unit
    for s in u._ctx.signals:
        if not s.hidden:
            net = netCtx.getDefault(s)
            for e in s.endpoints:
                if isinstance(e, PortItem):
                    net.addEndpoint(toL[e])

            for d in s.drivers:
                if isinstance(d, PortItem):
                    net.addDriver(toL[d])
            # connectSignalToStatements(
            #    s, toL, stmPorts, root, reducedStatements)

    # [TODO] uniq values per key
    for net in set(netCtx.values()):
        for src in net.drivers:
            for dst in net.endpoints:
                root.addEdge(src, dst)

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
