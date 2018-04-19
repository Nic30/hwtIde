from typing import List, Set, Callable

from elkContainer.lNode import LNode
from elkContainer.lPort import LPort
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


def UnitToLNode(u: Unit) -> LNode:
    """
    Build LNode instance from Unit instance

    :attention: unit has to be synthesized
    """

    toL = {}
    root = LNode(name=u._name, originObj=u, node2lnode=toL)
    # create subunits
    for su in u._units:
        n = root.addNode(name=su._name, originObj=su)
        for intf in su._interfaces:
            addPortToLNode(n, intf)

    # create subunits from statements
    for stm in u._ctx.statements:
        n = addStmAsLNode(root, stm)

    # create ports
    for intf in u._interfaces:
        addPort(root, intf)

    # pending and seen set because we do not want to draw
    # hidden signals in statements
    # we need to create connections for signals only outside of statements
    def connect_signal(s):
        driverPorts = set()
        endpointPorts = set()

        # connect all drivers of this signal with all endpoints
        for stm in s.drivers:
            node = lazyLoadNode(root, stm, toL)

            if isinstance(stm, PortItem):
                src = node
            elif isinstance(stm, Operator):
                src = node.east[0]
                for op, opPort in zip(stm.operands, node.west):
                    if isConst(op):
                        n = ValueAsLNode(root, op)
                        root.addEdge(n.east[0], opPort, originObj=op)
            else:
                src = node.east[stm._outputs.index(s)]

            driverPorts.add(src)

        for stm in s.endpoints:
            if isinstance(stm, Operator):
                node = lazyLoadNode(root, stm, toL)

                for op, src in zip(stm.operands, node.west):
                    if op is s:
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
                root.addEdge(src, dst, name=s.name, originObj=s)

    # connect nets
    for s in u._ctx.signals:
        connect_signal(s)

    reduceUselessAssignments(root)
    extractSplits(root, u._ctx.signals, toL)
    mergeSplitsOnInterfaces(root)
    flattenTrees(root, lambda node: node.name == "CONCAT")
    resolveSharedConnections(root)
    flattenPorts(root)

    return root
