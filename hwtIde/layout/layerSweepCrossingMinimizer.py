from enum import Enum
from typing import List

from hwt.pyUtils.arrayQuery import arr_all
from hwtIde.layout.containers import Layout
from layout.containers import LayoutNode


class PortSide(Enum):
    EAST = 0
    WEST = 1
    SOUTH = 2
    NORTH = 3


def firstFree(isForwardSweep, length):
    return 1 if isForwardSweep else length - 2


def firstIndex(isForwardSweep: bool, length: int):
    return 0 if isForwardSweep else length - 1


def endIndex(isForwardSweep: bool, length: int):
    return length - 1 if isForwardSweep else 0


def isOnEndOfSweepSide(port, isForwardSweep: bool) -> bool:
    if isForwardSweep:
        return port.getSide() == PortSide.EAST
    else:
        return port.getSide() == PortSide.WEST


def sideOpposedSweepDirection(isForwardSweep):
    return PortSide.WEST if isForwardSweep else PortSide.EAST


def isNotEnd(length, freeLayerIndex, isForwardSweep):
    return freeLayerIndex < length if isForwardSweep else freeLayerIndex >= 0


class LayerSweepCrossingMinimizer():
    """
    This class minimizes crossings by sweeping through a graph,
    holding the order of nodes in one layer fixed and switching the nodes
    in the other layer. After each re-sorting step, the ports in the two
    current layers are sorted.

    By using a LayerSweepTypeDecider as called by the GraphInfoHolder
    initializing class, each graph can either be dealt with bottom-up
    or hierarchically.

    bottom-up: the nodes of a child graph are sorted, then the order
        of ports of hierarchy border traversing edges are fixed.
        Then the parent  graph is laid out, viewing the child graph
        as an atomic node.

    hierarchical: When reaching a node with a child graph marked
        as hierarchical: First the ports are sorted on the outside
        of the graph. Then the nodes on the inside are sorted
        by the order of the ports. Then the child graph is swept through.
        Then the ports of the parent node are sorted by the order of the nodes
        on the last layer of the child graph. Finally the sweep through
        the parent graph is continued.

    Therefore this is a hierarchical processor which must have access
    to the root graph.

    Reference for the original layer sweep:
    Kozo Sugiyama, Shojiro Tagawa, and Mitsuhiko Toda. Methods for visual
    understanding of hierarchical system structures. IEEE Transactions
    on Systems, Man and Cybernetics, 11(2):109–125, February 1981.

    Precondition:
    The graph has a proper layering, i.e. all long edges have been splitted;
    all nodes have at least fixed port sides.

    Postcondition:
    The order of nodes in each layer and the order of ports in each node
    are optimized to yield as few edge crossings as possible

    :note: port from ELK
    """

    def process(self, graph: Layout):
        """
        Short-circuit cases in which no crossings can be minimized.
        Note that in-layer edges may be subject to crossing minimization
        if |layers| = 1 and that hierarchical crossing minimization may dive
        into a graph with a single node. There can be graphs that consist
        only of empty layers, for example due to inside self-loops
        with unconnected ports
        """

        layers = graph.layers
        emptyGraph = not layers or arr_all(layers, lambda l: not l)
        singleNode = len(layers) == 1 and len(layers[0]) == 1

        # [TODO]
        hierarchicalLayout = False

        if emptyGraph or (singleNode and not hierarchicalLayout):
            return

        graphsToSweepOn = [graph, ]
        minimizingMethod = self.chooseMinimizingMethod(graphsToSweepOn)
        self.minimizeCrossings(graphsToSweepOn, minimizingMethod)
        self.transferNodeAndPortOrdersToGraph(graphInfoHolders)

    def chooseMinimizingMethod(self, graphsToSweepOn):
        parent = graphsToSweepOn[0]
        if not parent.crossMinDeterministic():
            return self.compareDifferentRandomizedLayouts
        elif parent.crossMinAlwaysImproves():
            return self.minimizeCrossingsNoCounter
        else:
            return self.minimizeCrossingsWithCounter

    def minimizeCrossings(self, graphsToSweepOn, minimizingMethod):
        for gData in graphsToSweepOn:
            if gData.currentNodeOrder:
                minimizingMethod.accept(gData)
                if gData.parent is not None:
                    self.setPortOrderOnParentGraph(gData)

    def setPortOrderOnParentGraph(self, gData):
        if (gData.hasExternalPorts()):
            bestSweep = gData.getBestSweep()
            # Sort ports on left and right side of the parent node
            self.sortPortsByDummyPositionsInLastLayer(
                bestSweep.nodes, gData.parent, True)
            self.sortPortsByDummyPositionsInLastLayer(
                bestSweep.nodes, gData.parent, False)
            #gData.parent().setProperty(LayeredOptions.PORT_CONSTRAINTS, PortConstraints.FIXED_ORDER);

    def sortPortsByDummyPositionsInLastLayer(self,
                                             nodeOrder: List[List[LayoutNode]],
                                             parent, onRightMostLayer: bool):
        _endIndex = endIndex(onRightMostLayer, nodeOrder.length)
        lastLayer = nodeOrder[_endIndex]
        if not lastLayer[0].isExternalPortDummy:
            return

        j = firstIndex(onRightMostLayer, lastLayer.length)
        ports = parent.getPorts()
        for i in range(i, len(ports)):
            port = ports[i]
            if (isOnEndOfSweepSide(port, onRightMostLayer)
                    and port.isHierarchical):
                ports[i] = lastLayer[j].origin
                j += next(onRightMostLayer)

    def transferNodeAndPortOrdersToGraph(self, graphInfoHolders):
        for gD in graphInfoHolders:
            bestSweep = gD.getBestSweep()
            if bestSweep is not None:
                bestSweep.transferNodeAndPortOrdersToGraph(gD.lGraph())

    # For use with any two-layer crossing minimizer which always improves
    # crossings (e.g. two-sided greedy switch).
    def minimizeCrossingsNoCounter(self, gData):
        isForwardSweep = True
        improved = True
        while improved:
            improved = False
            improved = gData.crossMinimizer().setFirstLayerOrder(
                gData.currentNodeOrder(), isForwardSweep)
            improved |= self.sweepReducingCrossings(
                gData, isForwardSweep, False)
            isForwardSweep = not isForwardSweep

        self.setCurrentlyBestNodeOrders()

    def setCurrentlyBestNodeOrders(self):
        for graph in self.graphsWhoseNodeOrderChanged:
            graph.setCurrentlyBestNodeAndPortOrder(
                SweepCopy(graph.currentNodeOrder()))

    def sweepReducingCrossings(self, graph, forward: bool, firstSweep: bool):
        nodes = graph.currentNodeOrder()
        length = len(nodes)

        improved = graph.portDistributor().distributePortsWhileSweeping(
            nodes,
            firstIndex(forward, length),
            forward)
        firstLayer = nodes[firstIndex(forward, length)]
        improved |= self.sweepInHierarchicalNodes(
            firstLayer, forward, firstSweep)
        i = firstFree(forward, length)
        while isNotEnd(length, i, forward):
            improved |= graph.crossMinimizer().minimizeCrossings(nodes, i, forward, firstSweep)
            improved |= graph.portDistributor().distributePortsWhileSweeping(nodes, i, forward)
            improved |= self.sweepInHierarchicalNodes(
                nodes[i], forward, firstSweep)
            i += next(forward)

        self.graphsWhoseNodeOrderChanged.add(graph)
        return improved

    def sweepInHierarchicalNodes(self, layer, isForwardSweep, isFirstSweep):
        improved = False
        for node in layer:
            if (node.nestedGraph is not None
                    and not self.graphInfoHolders[node.nestedGraph].dontSweepInto()):
                improved |= self.sweepInHierarchicalNode(
                    isForwardSweep,
                    node, isFirstSweep)

        return improved

    def sweepInHierarchicalNode(self, isForwardSweep, node, isFirstSweep):
        nestedLGraph = node.nestedGraph
        nestedGraph = self.graphInfoHolders[nestedLGraph]
        nestedGraphNodeOrder = nestedGraph.currentNodeOrder()
        startIndex = firstIndex(
            isForwardSweep, nestedGraphNodeOrder.length)
        firstNode = nestedGraphNodeOrder[startIndex][0]

        if firstNode.isExternalPortDummy:
            nestedGraphNodeOrder[startIndex] = self.sortPortDummiesByPortPositions(
                node,
                nestedGraphNodeOrder[startIndex],
                sideOpposedSweepDirection(isForwardSweep))
        else:
            nestedGraph.crossMinimizer().setFirstLayerOrder(
                nestedGraphNodeOrder, isForwardSweep)

        improved = self.sweepReducingCrossings(
            nestedGraph, isForwardSweep, isFirstSweep)
        self.sortPortsByDummyPositionsInLastLayer(
            nestedGraph.currentNodeOrder(),
            nestedGraph.parent(),
            isForwardSweep)

        return improved
