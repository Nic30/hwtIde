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
                and len(n.originObj._inputs) == 1:
            if not do_update:
                nodes = set(root.children)
                do_update = True
            nodes.remove(n)

            srcPorts = []
            dstPorts = []

            inP = get_single_port(n.west)
            outP = get_single_port(n.east)
            assert not inP.outgoingEdges, inP
            for e in inP.incomingEdges:
                sPort = e.src
                assert sPort is not outP
                srcPorts.append(sPort)
                remove_edge(e)

            assert not outP.incomingEdges, inP
            for e in outP.outgoingEdges:
                dPort = e.dst
                assert dPort is not inP
                dstPorts.append(dPort)
                remove_edge(e)

            for srcPort in srcPorts:
                for dstPort in dstPorts:
                    root.add_edge(srcPort, dstPort)
    if do_update:
        root.children = list(nodes)
