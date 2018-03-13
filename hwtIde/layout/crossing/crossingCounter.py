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
Ta daaa!


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
from typing import List, Tuple
from layout.containers import LayoutNode


class CrossingsCounter():
    """
    :note: ported from ELK
    """

    def __init__(self, portPositions: List[int]):
        """
        Create crossings counter.

        @param portPositions
                   port position array passed to prevent frequent large array construction.
        """
        self.portPositions = portPositions
        self.indexTree = None
        self.ends = deque()

        self.nodeCardinalities = []

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #                                  PUBLIC API
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def countCrossingsBetweenLayers(self, leftLayerNodes, rightLayerNodes):
        """
        Count in-layer and between-layer crossings between the two given layers.

        @param leftLayerNodes
                   left layer
        @param rightLayerNodes
                   right layer
        @return number of crossings.
        """
        ports = self.initPortPositionsCounterClockwise(leftLayerNodes, rightLayerNodes)
        self.indexTree = BinaryIndexedTree(len(ports))
        return self.countCrossingsOnPorts(ports)

    def countInLayerCrossingsOnSide(self, nodes, side):
        """
        Only count in-layer crossings on the given side.

        @param nodes
                   order of nodes in layer in question.
        @param side
                   the side
        @return number of crossings.
        """
        ports = self.initPortPositionsForInLayerCrossings(nodes, side)
        return self.countInLayerCrossingsOnPorts(ports)

    def countNorthSouthPortCrossingsInLayer(self, layer: List[LayoutNode]):
        """
        Count crossings between edges connected to north/south ports of the passed layer's nodes.
        Also counts crossings of these edges with long edges spanning the passed layer.

        @param layer
                   a layer of the layering
        @return number of crossings.
        """
        ports = self.initPositionsForNorthSouthCounting(layer)
        self.indexTree = BinaryIndexedTree(len(ports))
        return self.countNorthSouthCrossingsOnPorts(ports)

    def countCrossingsBetweenPortsInBothOrders(self, upperPort, lowerPort) -> Tuple[int, int]:
        """
        Count crossings caused between edges incident to upperPort and lowerPort and when the order of these two is
        switched. Initialize before use with {@link #initForCountingBetween(LNode[], LNode[])} when not on either end of
        a graph. If you do want to use this to the left of the leftmost or to the right of the rightmost layer, use
        {@link #initPortPositionsForInLayerCrossings(LNode[], PortSide)}.

        @param upperPort
                   the upper port
        @param lowerPort
                   the lower port
        @return {@link Pair} of integers where {@link Pair#getFirst()} returns the crossings in the unswitched and
                {@link Pair#getSecond()} in the switched order.
        """
        ports = self.connectedPortsSortedByPosition(upperPort, lowerPort)
        upperLowerCrossings = self.countCrossingsOnPorts(ports)
        # Since we might add endpositions of ports which are not in the ports list, we need to explicitly clear
        # the index tree.
        self.indexTree.clear()
        self.switchPorts(upperPort, lowerPort)
        ports.sort(key=lambda p: positionOf[p])
        lowerUpperCrossings = countCrossingsOnPorts(ports)
        indexTree.clear()
        switchPorts(lowerPort, upperPort)
        return (upperLowerCrossings, lowerUpperCrossings)

    def countInLayerCrossingsBetweenNodesInBothOrders(self, upperNode, lowerNode, side):
        """
        Count crossings caused between edges incident to upperNode and lowerNode and when the order of these two is
        switched. Initialize before use with {@link #initPortPositionsForInLayerCrossings(LNode[], PortSide)}.

        @param upperNode
                   the upper node
        @param lowerNode
                   the lower node
        @param side
                   the side on which to count
        @return {@link Pair} of integers where {@link Pair#getFirst()} returns the crossings in the unswitched and
                {@link Pair#getSecond()} in the switched order.
        """
        ports = self.connectedInLayerPortsSortedByPosition(upperNode, lowerNode, side)
        upperLowerCrossings = self.countInLayerCrossingsOnPorts(ports)
        self.switchNodes(upperNode, lowerNode, side)
        # Since we might add endpositions of ports which are not in the ports list, we need to explicitly clear
        # the index tree.
        self.indexTree.clear()
        ports.sort(key=lambda p: positionOf[p])
        lowerUpperCrossings = countInLayerCrossingsOnPorts(ports)
        switchNodes(lowerNode, upperNode, side)
        indexTree.clear()
        return (upperLowerCrossings, lowerUpperCrossings)

    def initForCountingBetween(self, leftLayerNodes, rightLayerNodes):
        """
        Initializes the counter for counting crosses on a specific side of two layers. Use this method if only if you do
        not need to count all crossings, such as with {@link #countCrossingsBetweenPortsInBothOrders(LPort, LPort)}.

        @param leftLayerNodes
                   Nodes in western layer.
        @param rightLayerNodes
                   Nodes in eastern layer.
        """
        ports = self.initPortPositionsCounterClockwise(leftLayerNodes, rightLayerNodes)
        self.indexTree = BinaryIndexedTree(len(ports))

    def initPortPositionsForInLayerCrossings(self, nodes, side):
        """
        Initializes the counter for counting in-layer crossings on a specific side of a single layer. Use this method if
        only if you do not need to count all in layer crossings, such as with
        {@link #countCrossingsBetweenPortsInBothOrders(LPort, LPort)} on one end of a graph or
        {@link #countInLayerCrossingsBetweenNodesInBothOrders(LNode, LNode, PortSide)} in the middle.
        
        @param nodes
                   The order of the nodes in the layer
        @param side
                   The side to initialize
        @return the ports on which to count crossings on
        """
        ports = []
        self.initPositions(nodes, ports, side, True, True)
        indexTree = BinaryIndexedTree(ports.size())
        return ports

