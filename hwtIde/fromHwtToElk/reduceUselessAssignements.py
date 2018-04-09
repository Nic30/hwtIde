from elkContainer.lNode import LNode
from hwt.hdl.assignment import Assignment
from fromHwtToElk.utils import get_single_port, remove_edge


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

            inP = get_single_port(n.west)
            outP = get_single_port(n.east)
            for e in inP.incomingEdges:
                sPort = e.src
                srcPorts.append(sPort)
                edgesToRemove.append(e)

            for e in outP.outgoingEdges:
                dPort = e.dst
                dstPorts.append(dPort)
                edgesToRemove.append(e)

            for e in edgesToRemove:
                remove_edge(e)

            for srcPort in srcPorts:
                for dstPort in dstPorts:
                    root.add_edge(srcPort, dstPort)

    for n in nodes:
        for p in n.iterPorts():
            for e in p.iterEdges():
                try:
                    assert e.dstNode in nodes, (e, n, e.dstNode)
                    assert e.srcNode in nodes, (e, n, e.srcNode)
                except AssertionError:
                    raise
    if do_update:
        root.children = list(nodes)
