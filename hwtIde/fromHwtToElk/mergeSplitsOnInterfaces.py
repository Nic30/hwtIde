from typing import Union, List, Tuple

from elkContainer.constants import PortType, PortSide
from elkContainer.lEdge import LEdge
from elkContainer.lNode import LNode
from elkContainer.lPort import LPort
from fromHwtToElk.utils import removeEdge
from hwt.pyUtils.arrayQuery import single, DuplicitValueExc


def getRootIntfPort(port: LPort):
    """
    :return: most top port which contains this port
    """
    while True:
        if isinstance(port.parent, LNode):
            return port
        else:
            port = port.parent


def portCnt(port):
    """
    recursively count number of ports without children
    """
    if port.children:
        return sum(map(lambda p: portCnt(p), port.children))
    else:
        return 1


def _copyPort(port: LPort, targetParent: Union[LPort], reverseDirection):
    """
    add port to LPort for interface
    """
    d = port.direction
    side = port.side
    if reverseDirection:
        d = PortType.opposite(d)
        side = PortSide.opposite(side)

    newP = LPort(targetParent.getNode(), d, side, name=port.name)
    if isinstance(targetParent, LPort):
        targetParent.children.append(newP)
        newP.parent = targetParent
    else:
        targetParent.getPortSideView(side).append(newP)

    for ch in port.children:
        _copyPort(ch, newP, reverseDirection)

    return newP


def copyPort(port, targetLNode, reverseDir, topPortName=None):
    """
    Create identical port on targetNode
    """
    newP = _copyPort(port, targetLNode, reverseDir)

    if topPortName is not None:
        newP.name = topPortName

    return newP


def walkSignalPorts(rootPort: LPort):
    """
    recursively walk ports without any children
    """
    if rootPort.children:
        for ch in rootPort.children:
            yield from walkSignalPorts(ch)
    else:
        yield rootPort


def reconnectPorts(root: LNode, srcPort: LPort,
                   oldSplits: List[Tuple[LNode, LEdge]],
                   newSplitNode: LNode):
    """
    :ivar root: top LNode instance in which are nodes and links stored
    :ivar srcPort: for SLICE it is port which is connected to input of SLICE node
        for CONCAT it is port which is connected to output of CONCAT
    :ivar oldSplits: list of tuples (node, edge) which should be disconnected from graph
    :ivar newSplitNode: new node which should be connected to graph
    """
    # sort oldSplit nodes because they are not in same order as signals on
    # ports
    srcPortSignals = list(walkSignalPorts(srcPort))
    portOrder = {p: i for i, p in enumerate(srcPortSignals)}

    def portSortKey(x):
        n, e = x
        if e.dstNode is n:
            return portOrder[e.src]
        elif e.srcNode is n:
            return portOrder[e.dst]
        else:
            raise ValueError("Edge not connected to split node", e, n)

    oldSplits.sort(key=portSortKey)
    newSplitPorts = [walkSignalPorts(p) for p in newSplitNode.east]

    for preSplitPort, splitInp, (oldSplitNode, e) in zip(
            srcPortSignals,
            walkSignalPorts(newSplitNode.west[0]),
            oldSplits):

        # reconnect edge from src port to split node
        assert (e.src is preSplitPort and e.dstNode is oldSplitNode)\
            or (e.dst is preSplitPort and e.srcNode is oldSplitNode), e
        ouputPort = e.src is preSplitPort
        removeEdge(e)
        if ouputPort:
            root.addEdge(preSplitPort, splitInp, originObj=e.originObj)
        else:
            root.addEdge(splitInp, preSplitPort, originObj=e.originObj)

        _newSplitPorts = [next(p) for p in newSplitPorts]
        # reconnect part from split node to other target nodes
        if oldSplitNode.name == "CONCAT":
            for oldP, newP in zip(oldSplitNode.west, _newSplitPorts):
                for e in list(oldP.incomingEdges):
                    root.addEdge(e.src, newP, originObj=e.originObj)
                    removeEdge(e)

        elif oldSplitNode.name == "SLICE":
            for oldP, newP in zip(oldSplitNode.east, reversed(_newSplitPorts)):
                for e in list(oldP.outgoingEdges):
                    root.addEdge(newP, e.dst, originObj=e.originObj)
                    removeEdge(e)
        else:
            raise ValueError(oldSplitNode)

        root.children.remove(oldSplitNode)


def mergeSplitsOnInterfaces(root: LNode):
    """
    collect all split/concatenation nodes and group them by target interface
    """
    srcPort2splits = {}
    for ch in root.children:
        srcPort = None
        try:
            if ch.name == "CONCAT":
                p = single(ch.east, lambda x: True)
                e = single(p.outgoingEdges, lambda x: True)
                srcPort = e.dst
            elif ch.name == "SLICE":
                p = single(ch.west, lambda x: True)
                e = single(p.incomingEdges, lambda x: True)
                srcPort = e.src
        except DuplicitValueExc:
            continue

        if srcPort is not None and isinstance(srcPort.parent, LPort):
            # only for non primitive ports
            rootPort = getRootIntfPort(srcPort)
            records = srcPort2splits.get(rootPort, [])
            records.append((ch, e))
            srcPort2splits[rootPort] = records

    # join them if it is possible
    for srcPort, splits in srcPort2splits.items():
        if len(splits) == portCnt(srcPort):
            newSplitNode = root.addNode("SPLIT")
            copyPort(srcPort, newSplitNode, True, "")
            n = splits[0][0]
            for i in range(max(len(n.west),
                               len(n.east))):
                copyPort(
                    srcPort, newSplitNode, False, "[%d]" % i)
            reconnectPorts(root, srcPort, splits, newSplitNode)
