from elkContainer.lNode import LNode
from hwt.pyUtils.arrayQuery import single


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


def mergeSplitsOnInterfaces(root: LNode):
    # collect all split/concatenation nodes
    # and group them by target interface
    srcPort2splits = {}
    for ch in root.children:
        srcPort = None

        if ch.name == "CONCAT":
            p = single(ch.east, lambda x: True)
            e = single(p.outgoingEdges, lambda x: True)
            srcPort = e.dst
        elif ch.name == "SLICE":
            p = single(ch.west, lambda x: True)
            e = single(p.incomingEdges, lambda x: True)
            srcPort = e.src

        if srcPort is not None:
            rootPort = getRootIntfPort(srcPort)
            records = srcPort2splits.get(rootPort, [])
            records.append((ch, e))
            srcPort2splits[rootPort] = records

    # join them if it is possible
    for srcPort, splits in srcPort2splits.items():
        if len(splits) == portCnt(srcPort):
            raise NotImplementedError("reduce splits and concatenations to single node to simplify structure")