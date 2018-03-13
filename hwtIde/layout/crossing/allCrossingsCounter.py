from typing import List
from layout.containers import LayoutNode, NodeType, PortSide, Layout
from layout.crossing.crossingCounter import CrossingsCounter


class AllCrossingsCounter():
    """
    :note: Ported from ELK.

    Counts all crossings in a graph.
    """

    def __init__(self, graph: Layout):
        inLayerEdgeCounts = self.inLayerEdgeCounts = []
        hasNorthSouthPorts = self.hasNorthSouthPorts = [False for _ in graph.layers]
        hasHyperEdgesEastOfIndex = self.hasHyperEdgesEastOfIndex = hasNorthSouthPorts[:]
        self.nPorts = 0

        for l, layer in enumerate(graph.layers):
            for node in layer:
                hasNorthSouthPorts[l] |= node.getType() == NodeType.NORTH_SOUTH_PORT
                for port in node.iterPorts():
                    if (len(port.connectedEdges) > 1):
                        if port.side == PortSide.EAST:
                            hasHyperEdgesEastOfIndex[l] = True
                        elif (port.side == PortSide.WEST and l > 0):
                            hasHyperEdgesEastOfIndex[l - 1] = True

        for edge in graph.edges:
            if (edge.srcNode.getLayer() == edge.dstNode.getLayer()):
                inLayerEdgeCounts[l] += 1

        portPos = {n: 0 for n in graph.nodes}
        self.hyperedgeCrossingsCounter = HyperedgeCrossingsCounter(inLayerEdgeCounts,
                                                                   hasNorthSouthPorts,
                                                                   portPos)
        self.crossingCounter = CrossingsCounter(portPos)

