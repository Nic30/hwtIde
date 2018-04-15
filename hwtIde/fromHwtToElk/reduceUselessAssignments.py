from elkContainer.lNode import LNode
from fromHwtToElk.utils import getSinglePort, removeEdge
from hwt.hdl.assignment import Assignment


def reduceUselessAssignments(root: LNode):
    """
    Remove assingments if it is only a direct connection and can be replaced with direct link
    """
    do_update = False
    for n in root.children:
        if isinstance(n.originObj, Assignment)\
                and not n.originObj.indexes\
                and len(n.originObj._inputs) >= 1:

            if not do_update:
                nodes = set(root.children)
                do_update = True

            nodes.remove(n)

            srcPorts = []
            dstPorts = []
            edgesToRemove = []

            inP = getSinglePort(n.west)
            outP = getSinglePort(n.east)
            for e in inP.incomingEdges:
                sPort = e.src
                srcPorts.append(sPort)
                edgesToRemove.append(e)

            for e in outP.outgoingEdges:
                dPort = e.dst
                dstPorts.append(dPort)
                edgesToRemove.append(e)

            for e in edgesToRemove:
                removeEdge(e)

            for srcPort in srcPorts:
                for dstPort in dstPorts:
                    root.addEdge(srcPort, dstPort)

    if do_update:
        for n in nodes:
            for p in n.iterPorts():
                for e in p.iterEdges():
                    try:
                        assert e.dstNode in nodes, (e, n, e.dstNode)
                        assert e.srcNode in nodes, (e, n, e.srcNode)
                    except AssertionError:
                        raise
        root.children = list(nodes)
