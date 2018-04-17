from typing import Callable

from elkContainer.constants import PortType, PortSide
from elkContainer.lNode import LNode
from fromHwtToElk.utils import removeEdge


def searchRootOfTree(reducibleChildren, nodeFromTree):
    while True:
        nextNode = nodeFromTree.east[0].outgoingEdges[0].dstNode
        if nextNode in reducibleChildren:
            nodeFromTree = nextNode
        else:
            return nodeFromTree


def flattenTrees(root, nodeSelector: Callable[[LNode], bool]):
    """
    Walk all nodes and discover trees of nodes (usually operators) and reduce them
    to single node with multiple outputs

    :attention: node has to have single output
    """
    reducibleChildren = set()
    for ch in root.children:
        if nodeSelector(ch):
            reducibleChildren.add(ch)

    while reducibleChildren:
        _treeRoot = reducibleChildren.pop()
        reducibleChildren.add(_treeRoot)
        # wee need to keep order of inputs, use preorder
        treeRoot = searchRootOfTree(reducibleChildren, _treeRoot)

        inputEdges = []
        reducedNodes = []
        # An iterative process to print preorder traveral of tree
        nodeStack = []
        nodeStack.append((treeRoot, None))

        while nodeStack:
            # Pop the top item from stack and print it
            node, e = nodeStack.pop()
            if node in reducibleChildren:
                reducedNodes.append(node)
                # walk inputs and add child nodes to stack
                for p in node.west:
                    for e in p.iterEdges():
                        nodeStack.append((e.srcNode, e))
            else:
                inputEdges.append(e)

        if len(reducedNodes) > 1:
            outputedge = treeRoot.east[0].outgoingEdges[0]
            assert outputedge is not None

            newName = reducedNodes[0].name
            newNode = root.addNode(newName)

            o = newNode.addPort("", PortType.OUTPUT, PortSide.EAST)
            dst = outputedge.dst
            removeEdge(outputedge)
            root.addEdge(o, dst)

            for ie in inputEdges:
                inp = newNode.addPort("", PortType.INPUT, PortSide.WEST)
                src = ie.src
                removeEdge(ie)
                root.addEdge(src, inp)

            for n in reducedNodes:
                root.children.remove(n)
                reducibleChildren.remove(n)
        else:
            reducibleChildren.remove(reducedNodes[0])
