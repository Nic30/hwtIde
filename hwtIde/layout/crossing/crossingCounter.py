"""
In ELK Layered we distinguish three types of edge crossings that can occur:

Between-layer crossings (the ones everybody knows),
In-layer crossings (caused by out very own in-layer edges), and
North-south crossings (caused by implicit edges between {@link NodeType#NORTH_SOUTH_PORT} dummies and their
originating {@link NodeType#NORMAL} node).

All three types of crossings are counted by this class, by transferring each counting problem into 
counting in-layer edges as described below. 

In-layer crossings
First, let's explain how counting in-layer crossings works, since we transfer the other two types of crossings 
into this case. Before usage, each port must have a unique id and each node an id unique for it's layer.


For counting in-layer crossings with {@link #countInLayerCrossingsOnSide(LNode[], PortSide)}, we step through each
edge and add the position of the end of the edge to a sorted list. Each time we meet the same edge again, we delete
it from the list again. Each time we add an edge end position, the number of crossings is the index of the this
position in the sorted list. The implementation of this list guarantees that adding, deleting and finding indices is
log n.


          List
0--       [2]
1-+-|     [2,3]
  | |
2-- |     [3]
3----     []


Between-layer crossings
Between-layer crossings become in-layer crossings if we fold and rotate the right layer downward and pretend that we
are in a single layer. For example:


0  3
 \/
 /\
1  2
becomes:
0-┐
1-+-┐
  | |
2-┘ |
3---┘
Ta daaanot 


This is used in {@link #countCrossingsBetweenLayers(LNode[], LNode[])}.

North/south crossings
North/south crossings are counted per layer and just as for between-layer edges we index the ports and nodes of a
layer such that we can simply count in-layer edge crossings. This time the rotations are a bit more intricate, 
however. The nice things is that we can directly incorporate long edges.

An example:

           o----------- ne1
nw1 ---o   |       o--- ne2
nw2 ---+---+---o   |
     __|___|___|___|__
    | pn1 pn2 pn3 pn4 |
    |                 |
    |__ps1__ps2__ps3__|
        |    |    |
sw1 ----o    |    |
lw  ---------+----+----- le
sw2 ---------+----o
             o---------- se1

becomes:

nw1 --┐
nw2 --+-┐
pn1 --┘ |
pn2 --┐ |
pn3 --+-┘
pn4 -┐|
ne2 -┘|
ne1 --┘
ps3 ---┐
ps2 ---+-┐
ps1 -┐ | |
sw1 -┘ | |
lw  -┐ | |
sw2 -+-┘ |
se1 -+---┘
le --┘

Thus, the top-down in-layer index order is (nsl means north/south/long edge dummy):

northern nsl dummies with western edges north-to-south, 
northern ports west-to-east order
northern nsl dummies with eastern edges south-to-north
southern ports east-to-west order
southern nsl dummies with western edges north-to-south
southern nsl dummies with eastern edges south-to-north

"""
from collections import deque
from typing import List, Tuple, Dict, Deque
from layout.containers import LNode, LPort, PortSide, LEdge, NodeType
from layout.crossing.binaryIndexedTree import BinaryIndexedTree
from hwt.pyUtils.arrayQuery import where, arr_any
from itertools import islice


def reverseForTopDown(seq, topDown: bool):
    if topDown:
        return seq
    else:
        return reversed(seq)


def inNorthSouthEastWestOrder(node: LNode, side: PortSide):
    """
    Iterate over ports in north to south and east to west order.

    @param node: whose ports are being considered.
    @param side: of the node we are interested in
    @return Iterable for ports on given node and side in given order.
    """
    if side == PortSide.EAST or side == PortSide.NORTH:
            return node.getPortSideView(side)
    elif side == PortSide.SOUTH or side == PortSide.WEST:
            return reversed(node.getPortSideView(side))
    raise ValueError(side)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#                                  CONVENIENCE
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def getPorts(node: LNode, side: PortSide, topDown: bool):
    if side == PortSide.EAST:
        if topDown:
            return node.getPortSideView(side)
        else:
            return reversed(node.getPortSideView(side))
    elif topDown:
        return reversed(node.getPortSideView(side))
    else:
        return node.getPortSideView(side)


def getNorthSouthPortsWithIncidentEdges(node: LNode, side: PortSide):
    return where(node.getPortSideView(side), lambda p: p.portDummy)


def isInLayer(edge: LEdge) -> bool:
    sourceLayer = edge.srcNode.layerIndex
    targetLayer = edge.dstNode.layerIndex
    return sourceLayer == targetLayer


def otherEndOf(edge: LEdge, fromPort: LPort):
    return edge.dst if fromPort is edge.src else edge.src


def isPortSelfLoop(edge: LEdge) -> bool:
    return edge.src == edge.dst


def isLayoutUnitChanged(lastUnit: LNode, node: LNode) -> bool:
    if lastUnit is None or lastUnit == node or not node.inLayerLayoutUnit:
        return False

    return node.inLayerLayoutUnit is not lastUnit


class CrossingsCounter():
    """
    :note: ported from ELK
    """
    INDEXING_SIDE = PortSide.WEST
    STACK_SIDE = PortSide.EAST

    def __init__(self, portPositions: Dict[LPort, int]):
        """
        Create crossings counter.

        :param portPositions: port position array passed to prevent frequent
            large array construction.
        """
        self.portPositions = portPositions
        self.indexTree = None
        self.ends = deque()

        self.nodeCardinalities = {}

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                                  PUBLIC API
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def countCrossingsBetweenLayers(self, leftLayerNodes, rightLayerNodes):
        """
        Count in-layer and between-layer crossings between the two given layers.

        :param leftLayerNodes: left layer
        :param rightLayerNodes: right layer
        :return number of crossings.
        """
        ports = self.initPortPositionsCounterClockwise(
            leftLayerNodes, rightLayerNodes)
        self.indexTree = BinaryIndexedTree(len(ports))
        return self.countCrossingsOnPorts(ports)

    def countInLayerCrossingsOnSide(self, nodes, side):
        """
        Only count in-layer crossings on the given side.

        :param nodes: order of nodes in layer in question.
        :param side: the side
        :return number of crossings.
        """
        ports = self.initPortPositionsForInLayerCrossings(nodes, side)
        return self.countInLayerCrossingsOnPorts(ports)

    def countNorthSouthPortCrossingsInLayer(self, layer: List[LNode]):
        """
        Count crossings between edges connected to north/south ports
        of the passed layer's nodes. Also counts crossings of these edges
        with long edges spanning the passed layer.

        :param layer: a layer of the layering
        :return number of crossings.
        """
        ports = self.initPositionsForNorthSouthCounting(layer)
        self.indexTree = BinaryIndexedTree(len(ports))
        return self.countNorthSouthCrossingsOnPorts(ports)

    def countCrossingsBetweenPortsInBothOrders(self, upperPort, lowerPort
                                               ) -> Tuple[int, int]:
        """
        Count crossings caused between edges incident to upperPort
        and lowerPort and when the order of these two is switched. Initialize
        before use with {@link #initForCountingBetween(LNode[], LNode[])}
        when not on either end of a graph. If you do want to use this
        to the left of the leftmost or to the right of the rightmost layer, use
        {@link #initPortPositionsForInLayerCrossings(LNode[], PortSide)}.

        :param upperPort
                   the upper port
        :param lowerPort
                   the lower port
        :return {@link Pair} of integers where {@link Pair#getFirst()}
                returns the crossings in the unswitched and
                {@link Pair#getSecond()} in the switched order.
        """
        ports = self.connectedPortsSortedByPosition(upperPort, lowerPort)
        upperLowerCrossings = self.countCrossingsOnPorts(ports)
        # Since we might add endpositions of ports which are not in the ports list, we need to explicitly clear
        # the index tree.
        self.indexTree.clear()
        self.switchPorts(upperPort, lowerPort)

        possitions = self.portPositions
        ports.sort(key=lambda p: possitions[p])
        lowerUpperCrossings = self.countCrossingsOnPorts(ports)
        self.indexTree.clear()
        self.switchPorts(lowerPort, upperPort)
        return (upperLowerCrossings, lowerUpperCrossings)

    def countInLayerCrossingsBetweenNodesInBothOrders(self, upperNode, lowerNode, side):
        """
        Count crossings caused between edges incident to upperNode and lowerNode and when the order of these two is
        switched. Initialize before use with {@link #initPortPositionsForInLayerCrossings(LNode[], PortSide)}.

        :param upperNode
                   the upper node
        :param lowerNode
                   the lower node
        :param side
                   the side on which to count
        :return tuple of integers (the crossings in the unswitched,
                                   the crossings in the switched order)
        """
        ports = self.connectedInLayerPortsSortedByPosition(
            upperNode, lowerNode, side)
        upperLowerCrossings = self.countInLayerCrossingsOnPorts(ports)
        self.switchNodes(upperNode, lowerNode, side)
        # Since we might add endpositions of ports which are not in the ports list, we need to explicitly clear
        # the index tree.
        self.indexTree.clear()

        possitions = self.portPositions
        ports.sort(key=lambda p: possitions[p])
        lowerUpperCrossings = self.countInLayerCrossingsOnPorts(ports)
        self.switchNodes(lowerNode, upperNode, side)
        self.indexTree.clear()
        return (upperLowerCrossings, lowerUpperCrossings)

    def initForCountingBetween(self, leftLayerNodes, rightLayerNodes):
        """
        Initializes the counter for counting crosses on a specific
        side of two layers. Use this method if only if you do
        not need to count all crossings, such as with {@link #countCrossingsBetweenPortsInBothOrders(LPort, LPort)}.

        :param leftLayerNodes
                   Nodes in western layer.
        :param rightLayerNodes
                   Nodes in eastern layer.
        """
        ports = self.initPortPositionsCounterClockwise(
            leftLayerNodes, rightLayerNodes)
        self.indexTree = BinaryIndexedTree(len(ports))

    def initPortPositionsForInLayerCrossings(self, nodes: List[LNode], side: PortSide):
        """
        Initializes the counter for counting in-layer crossings on a specific
        side of a single layer. Use this method if only if you do not need
        to count all in layer crossings, such as with
        {@link #countCrossingsBetweenPortsInBothOrders(LPort, LPort)} on one end of a graph or
        {@link #countInLayerCrossingsBetweenNodesInBothOrders(LNode, LNode, PortSide)} in the middle.

        :param nodes: The order of the nodes in the layer
        :param side: The side to initialize
        :return the ports on which to count crossings on
        """
        ports = []
        self.initPositions(nodes, ports, side, True, True)
        self.indexTree = BinaryIndexedTree(len(ports))
        return ports

    def switchPorts(self, topPort: LPort, bottomPort: LPort):
        """
        Notify counter of port switch.

        :param topPort: The port previously further north.
        :param bottomPort: The port previously further south.
        """
        topPortPos = self.portPositions[topPort]
        self.portPositions[topPort] = self.portPositions[bottomPort.id]
        self.portPositions[bottomPort] = topPortPos

    def switchNodes(self, wasUpperNode: LNode, wasLowerNode: LNode, side: PortSide):
        """
        This method should be used as soon as neighboring nodes have been
        switched. Use the first parameter to pass which node was the upper
        node before a switch and the second to pass the former lower node.
        We assume a left-right layout.

        :param wasUpperNode: The node which was the upper node before switching.
        :param wasLowerNode: The node which was the lower node before switching.
        :param side: The side on which the crossings are currently being counted.
        """
        poss = self.portPositions
        nodeCardinalities = self.nodeCardinalities
        ports = inNorthSouthEastWestOrder(wasUpperNode, side)
        for port in ports:
            poss[port] = poss[port] + nodeCardinalities[wasLowerNode]

        ports = inNorthSouthEastWestOrder(wasLowerNode, side)
        for port in ports:
            poss[port] = poss[port] - nodeCardinalities[wasUpperNode]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                                  def API
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def connectedInLayerPortsSortedByPosition(self, upperNode: LPort,
                                              lowerNode: LNode,
                                              side: PortSide):
        # ports = new TreeSet<>((a, b) -> Integer.compare(positionOf(a),
        # positionOf(b)))
        ports = set()
        for node in (upperNode, lowerNode):
            for port in inNorthSouthEastWestOrder(node, side):
                for edge in port.getConnectedEdges():
                    if not edge.isSelfLoop():
                        ports.add(port)
                        if isInLayer(edge):
                            ports.add(otherEndOf(edge, port))
        return list(ports)

    def connectedPortsSortedByPosition(self, upperPort: LPort, lowerPort: LPort):
        # ports = new TreeSet<>((a, b) -> Integer.compare(positionOf(a),
        # positionOf(b)))
        ports = set()
        for port in (upperPort, lowerPort):
            ports.add(port)
            for edge in port.getConnectedEdges():
                if not isPortSelfLoop(edge):
                    ports.add(otherEndOf(edge, port))

        return list(ports)

    def countCrossingsOnPorts(self, ports) -> int:
        crossings = 0
        poss = self.portPositions
        indexTree = self.indexTree
        ends = self.ends

        for port in ports:
            indexTree.removeAll(poss[port])
            # First get crossings for all edges.
            for edge in port.connectedEdges:
                endPosition = poss[otherEndOf(edge, port)]
                if endPosition > poss[port]:
                    crossings += indexTree.rank(endPosition)
                    ends.append(endPosition)

            # Then add end points.
            while ends:
                indexTree.add(ends.pop())

        return crossings

    def countInLayerCrossingsOnPorts(self, ports) -> int:
        crossings = 0
        poss = self.portPositions
        indexTree = self.indexTree
        ends = self.ends

        for port in ports:
            indexTree.removeAll(poss[port])
            numBetweenLayerEdges = 0
            # First get crossings for all edges.
            for edge in port.getConnectedEdges():
                if isInLayer(edge):
                    endPosition = poss[otherEndOf(edge, port)]
                    if endPosition > poss(port):
                        crossings += indexTree.rank(endPosition)
                        ends.append(endPosition)
                else:
                    numBetweenLayerEdges += 1

            crossings += indexTree.size() * numBetweenLayerEdges
            # Then add end points.
            while ends:
                indexTree.add(ends.pop())

        return crossings

    def countNorthSouthCrossingsOnPorts(self, ports) -> int:
        crossings = 0
        targetsAndDegrees = []
        indexTree = self.indexTree
        poss = self.portPositions
        ends = self.ends

        for port in ports:
            indexTree.removeAll(poss[port])
            targetsAndDegrees.clear()

            # collect the edges that are incident to the port,
            # which is a bit tedious since north/south ports have no physical
            # edge within the graph at this point
            t = port.getNode().type
            if t == NodeType.NORMAL:
                dummy = port.portDummy
                # guarded in #initPositionsForNorthSouthCounting(...)
                assert dummy is not None
                for p in dummy.getPorts():
                    # western and eastern
                    targetsAndDegrees.add((p, p.getDegree()))

            elif t == NodeType.LONG_EDGE:
                for p in where(port.getNode().iterPorts(), lambda p: p is not port):
                    # add an edge to the dummy's other port
                    targetsAndDegrees.add((p, p.getDegree()))
                    break

            elif t == NodeType.NORTH_SOUTH_PORT:
                dummyPort = port.getProperty(InternalProperties.ORIGIN)
                targetsAndDegrees.add((dummyPort, port.getDegree()))

            # First get crossings for all edges.
            for targetAndDegree in targetsAndDegrees:
                endPosition = poss[targetAndDegree.getFirst()]
                if endPosition > poss[port]:
                    crossings += indexTree.rank(endPosition) * \
                        targetAndDegree.getSecond()
                    ends.append(endPosition)

            # Then add end points.
            while ends:
                indexTree.add(ends.pop())

        return crossings

    def initPositions(self, nodes: List[LNode], ports: List[LPort],
                      side: PortSide, topDown: bool, getCardinalities: bool
                      ) -> None:
        numPorts = len(ports)
        if getCardinalities:
            nodeCardinalities = self.nodeCardinalities = {n: 0 for n in nodes}
        poss = self.portPositions

        for node in reverseForTopDown(nodes, topDown):
            nodePorts = list(getPorts(node, side, topDown))
            if getCardinalities:
                nodeCardinalities[node] = sum(1 for _ in nodePorts)

            for port in nodePorts:
                poss[port] = numPorts
                numPorts += 1

            ports.extend(nodePorts)

    def initPortPositionsCounterClockwise(self, leftLayerNodes: List[LNode],
                                          rightLayerNodes: List[LNode]):
        ports = []
        self.initPositions(leftLayerNodes, ports, PortSide.EAST, True, False)
        self.initPositions(rightLayerNodes, ports, PortSide.WEST, False, False)
        return ports

    def initPositionsForNorthSouthCounting(self, nodes: List[LNode]):
        ports = []
        stack = deque()

        lastLayoutUnit = None
        index = 0
        emptyStack = self.emptyStack
        poss = self.portPositions

        for current in nodes:
            if isLayoutUnitChanged(lastLayoutUnit, current):
                # work the stack (filled with southern dummies)
                index = emptyStack(stack, ports, self.STACK_SIDE, index)

            if current.inLayerLayoutUnit:
                lastLayoutUnit = current.inLayerLayoutUnit

            t = current.type
            # what we consider normal
            if t == NodeType.NORMAL or t == NodeType.BIG_NODE:
                # index the northern ports west-to-east
                for p in getNorthSouthPortsWithIncidentEdges(current, PortSide.NORTH):
                    poss[p] = index
                    index += 1
                    ports.append(p)

                # work the stack (filled with northern dummies)
                index = emptyStack(stack, ports, self.STACK_SIDE, index)

                # index the southern ports in regular clock-wise order
                for p in getNorthSouthPortsWithIncidentEdges(current, PortSide.SOUTH):
                    poss[p] = index
                    index += 1
                    ports.append(p)

            elif t == NodeType.NORTH_SOUTH_PORT:
                if arr_any(current.getPortSideView(self.INDEXING_SIDE), lambda x: True):
                    # should be only one
                    p = current.getPortSideView(self.INDEXING_SIDE)[0]
                    poss[p] = index
                    index += 1
                    ports.append(p)

                if not current.getPortSideView(self.STACK_SIDE).isEmpty():
                    stack.append(current)

            elif t == NodeType.LONG_EDGE:
                for p in current.getPortSideView(PortSide.WEST):
                    poss[p] = index
                    index += 1
                    ports.append(p)

                for p in current.getPortSideView(PortSide.EAST):
                    stack.append(current)

            else:
                # nothing to do here
                pass

        # are there any southern dummy nodes left on the stack?
        emptyStack(stack, ports, self.STACK_SIDE, index)

        return ports

    def emptyStack(self, stack: Deque[LNode], ports: List[LPort],
                   side: PortSide, startIndex: int) -> int:
        index = startIndex
        poss = self.portPositions
        while stack:
            dummy = stack.pop()
            # dummy is either a north/south port dummy or a long edge dummy
            # both of which have only a single port on the west and/or east
            # side
            p = dummy.getPortSideView(side)[0]
            poss[p] = index
            index += 1
            ports.add(p)

        return index
