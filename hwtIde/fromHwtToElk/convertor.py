from typing import Optional

from elkContainer.lNode import LNode
from fromHwtToElk.connectSignalToStatements import connectSignalToStatements
from fromHwtToElk.extractSplits import extractSplits
from fromHwtToElk.flattenPorts import flattenPorts
from fromHwtToElk.flattenTrees import flattenTrees
from fromHwtToElk.mergeSplitsOnInterfaces import mergeSplitsOnInterfaces
from fromHwtToElk.reduceUselessAssignments import reduceUselessAssignments
from fromHwtToElk.resolveSharedConnections import resolveSharedConnections
from fromHwtToElk.statementRenderer import StatementRenderer, Signal2stmPortCtx
from fromHwtToElk.utils import addOperatorAsLNode, addPortToLNode,\
    addStmAsLNode, addPort, ternaryAsSimpleAssignment,\
    isUselessTernary, ValueAsLNode
from hwt.hdl.operator import Operator
from hwt.synthesizer.unit import Unit


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

    # create subunits
    for su in u._units:
        n = root.addNode(name=su._name, originObj=su)
        UnitToLNode(su, n, toL)
        for intf in su._interfaces:
            addPortToLNode(n, intf)

    reducedStatements = set()
    # create subunits from statements
    for stm in u._ctx.statements:
        if StatementRenderer.isJustConstAssign(stm):
            # reduce assignment to just value node
            reducedStatements.add(stm)
            n = ValueAsLNode(root, stm.src)
            toL[stm] = n
        else:
            n = addStmAsLNode(root, stm)
            stmPorts[n] = Signal2stmPortCtx(n)

    # create ports for this unit
    for intf in u._interfaces:
        addPort(root, intf)

    # connect nets inside this unit
    for s in u._ctx.signals:
        if not s.hidden:
            connectSignalToStatements(
                s, toL, stmPorts, root, reducedStatements)

    # render content of statements
    for stm in u._ctx.statements:
        if stm not in reducedStatements:
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
