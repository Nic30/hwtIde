from elkContainer.lNode import LNode
from hwt.pyUtils.arrayQuery import single, DuplicitValueExc
from elkContainer.constants import PortType, PortSide
from elkContainer.lPort import LPort
from typing import Union
from fromHwtToElk.utils import removeEdge


def getRootIntfPort(port):
    while True:
        if isinstance(port.parent, LNode):
            return port
        else:
            port = port.parent


def portCnt(port):
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
    newP = _copyPort(port, targetLNode, reverseDir)

    if topPortName is not None:
        newP.name = topPortName

    return newP


def walkSignalPorts(rootPort: LPort):
    if rootPort.children:
        for ch in rootPort.children:
            yield from walkSignalPorts(ch)
    else:
        yield rootPort


def reconnectPorts(root, srcPort, oldSplits, newSplitNode):
    newSplitPorts = [walkSignalPorts(p) for p in newSplitNode.east]

    for preSplitPort, splitInp, (oldSplitNode, e) in zip(
            walkSignalPorts(srcPort),
            walkSignalPorts(newSplitNode.west[0]),
            oldSplits):

        try:
            # reconnect edge from src port to split node
            assert (e.src is preSplitPort and e.dstNode is oldSplitNode)\
                or (e.dst is preSplitPort and e.srcNode is oldSplitNode), e
        except AssertionError:
            raise
        removeEdge(e)
        root.addEdge(preSplitPort, splitInp)
        print("reconnecting", preSplitPort, splitInp)

        _newSplitPorts = [next(p) for p in newSplitPorts]
        # reconnect part from split node to other target nodes
        if oldSplitNode.name == "CONCAT":
            for oldP, newP in zip(oldSplitNode.west, _newSplitPorts):
                for e in list(oldP.incomingEdges):
                    print(">reconnecting", e.src, newP)
                    root.addEdge(e.src, newP)
                    removeEdge(e)

        elif oldSplitNode.name == "SLICE":
            for oldP, newP in zip(oldSplitNode.east, _newSplitPorts):
                for e in list(oldP.outgoingEdges):
                    print(">reconnecting", newP, e.dst)
                    root.addEdge(newP, e.dst)
                    removeEdge(e)
        else:
            raise ValueError(oldSplitNode)


def mergeSplitsOnInterfaces(root: LNode):
    # collect all split/concatenation nodes
    # and group them by target interface
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
