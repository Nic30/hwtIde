from layout.containers import NodeType, PortSide, Layout, LNode
from layout.crossing.crossingCounter import CrossingsCounter
from layout.crossing.hyperedgeCrossingsCounter import HyperedgeCrossingsCounter
from typing import List


class AllCrossingsCounter():
    """
    :note: Ported from ELK.

    Counts all crossings in a graph.
    """

    def __init__(self, graph: Layout):
        inLayerEdgeCounts = self.inLayerEdgeCounts = [0 for _ in graph.layers]
        hasNorthSouthPorts = self.hasNorthSouthPorts = [
            False for _ in graph.layers]
        hasHyperEdgesEastOfIndex = self.hasHyperEdgesEastOfIndex = hasNorthSouthPorts[:]
        self.nPorts = 0

        for l, layer in enumerate(graph.layers):
            for node in layer:
                hasNorthSouthPorts[l] |= node.type == NodeType.NORTH_SOUTH_PORT
                for port in node.iterPorts():
                    if (len(port.connectedEdges) > 1):
                        if port.side == PortSide.EAST:
                            hasHyperEdgesEastOfIndex[l] = True
                        elif (port.side == PortSide.WEST and l > 0):
                            hasHyperEdgesEastOfIndex[l - 1] = True

        for edge in graph.edges:
            if (edge.srcNode.layerIndex == edge.dstNode.layerIndex):
                inLayerEdgeCounts[l] += 1

        portPos = {}
        for n in graph.nodes:
            for p in n.iterPorts():
                portPos[p] = 0

        self.hyperedgeCrossingsCounter = HyperedgeCrossingsCounter(
            inLayerEdgeCounts,
            hasNorthSouthPorts,
            portPos)
        self.crossingCounter = CrossingsCounter(portPos)

    def countAllCrossings(self, currentOrder: List[List[LNode]]):
        """
        Count all crossings.

        :param currentOrder: the current node order
        :return: the number of crossings in the graph
        """
        if not currentOrder:
            return 0

        crossings = self.crossingCounter.countInLayerCrossingsOnSide(
            currentOrder[0], PortSide.WEST)
        crossings += self.crossingCounter.countInLayerCrossingsOnSide(
            currentOrder[len(currentOrder) - 1], PortSide.EAST)

        countCrossingsAt = self.countCrossingsAt
        for layerIndex in range(len(currentOrder)):
            crossings += countCrossingsAt(layerIndex, currentOrder)

        return crossings

    def countCrossingsAt(self, layerIndex: int, currentOrder: List[List[LNode]]):
        totalCrossings = 0
        leftLayer = currentOrder[layerIndex]
        if layerIndex < len(currentOrder) - 1:
            rightLayer = currentOrder[layerIndex + 1]
            if self.hasHyperEdgesEastOfIndex[layerIndex]:
                totalCrossings = self.hyperedgeCrossingsCounter.countCrossings(
                    leftLayer, rightLayer)
                totalCrossings += self.crossingCounter.countInLayerCrossingsOnSide(
                    leftLayer, PortSide.EAST)
                totalCrossings += self.crossingCounter.countInLayerCrossingsOnSide(
                    rightLayer, PortSide.WEST)
            else:
                totalCrossings = self.crossingCounter.countCrossingsBetweenLayers(
                    leftLayer, rightLayer)

        if self.hasNorthSouthPorts[layerIndex]:
            totalCrossings += self.crossingCounter.countNorthSouthPortCrossingsInLayer(
                leftLayer)

        return totalCrossings
