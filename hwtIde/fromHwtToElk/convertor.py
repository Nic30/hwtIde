from typing import List, Set, Callable

from elkContainer.lNode import LNode
from elkContainer.lPort import LPort
from fromHwtToElk.reduceUselessAssignments import reduceUselessAssignments
from fromHwtToElk.resolveSharedConnections import resolveSharedConnections
from fromHwtToElk.utils import addOperatorAsLNode, addPortToLNode,\
    addStmAsLNode, addPort, ValueAsLNode
from hwt.hdl.operator import Operator, isConst
from hwt.hdl.portItem import PortItem
from hwt.synthesizer.unit import Unit
from fromHwtToElk.extractSplits import extractSplits
from hwt.hdl.operatorDefs import OpDefinition
from fromHwtToElk.flattenTrees import flattenTrees
from fromHwtToElk.flattenPorts import flattenPorts
from fromHwtToElk.mergeSplitsOnInterfaces import mergeSplitsOnInterfaces


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
            try:
                node = toL[stm]
            except KeyError:
                if isinstance(stm, Operator):
                    toL[stm] = node = addOperatorAsLNode(root, stm)
                else:
                    raise

            if isinstance(stm, PortItem):
                src = node
            elif isinstance(stm, Operator):
                src = node.east[0]
                for i, (op, opPort) in enumerate(zip(stm.operands, node.west)):
                    if isConst(op):
                        n = ValueAsLNode(root, op)
                        root.addEdge(n.east[0], opPort)
            else:
                src = node.east[stm._outputs.index(s)]

            driverPorts.add(src)

        for stm in s.endpoints:
            if isinstance(stm, Operator):
                try:
                    node = toL[stm]
                except KeyError:
                    toL[stm] = node = addOperatorAsLNode(root, stm)

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
