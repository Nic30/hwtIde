from typing import List

from elkContainer.lNode import LNode
from elkContainer.lPort import LPort
from fromHwtToElk.reduceUselessAssignments import reduceUselessAssignments
from fromHwtToElk.resolveSharedConnections import resolveSharedConnections
from fromHwtToElk.utils import addOperatorAsLNode, addPortToLNode,\
    addStmAsLNode, addPort, ValueAsLNode
from hwt.hdl.operator import Operator, isConst
from hwt.hdl.portItem import PortItem
from hwt.synthesizer.unit import Unit


def flattenPort(port: LPort):
    yield port
    if port.children:
        for ch in port.children:
            yield from flattenPort(ch)
        port.children.clear()


def _flattenPortsSide(side: List[LNode]) -> List[LNode]:
    new_side = []
    for i in side:
        for new_p in flattenPort(i):
            new_side.append(new_p)
    return new_side


def flattenPorts(root: LNode):
    """
    Flatten ports to simplify layout generation

    :attention: children property is destroyed, parent property stays same
    """
    for u in root.children:
        u.west = _flattenPortsSide(u.west)
        u.east = _flattenPortsSide(u.east)
        u.north = _flattenPortsSide(u.north)
        u.south = _flattenPortsSide(u.south)


def UnitToLNode(u: Unit) -> LNode:
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
                        root.add_edge(n.east[0], opPort)
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
                root.add_edge(src, dst, name=s.name, originObj=s)

    # connect nets
    for s in u._ctx.signals:
        connect_signal(s)

    reduceUselessAssignments(root)
    #flattenConcatenations(root)
    resolveSharedConnections(root)
    flattenPorts(root)

    return root
