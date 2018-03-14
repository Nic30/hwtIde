import unittest

from layout.containers import PortType, PortSide
from layout.crossing.barycenterHeuristic import BarycenterHeuristic
from layout.crossing.forsterConstraintResolver import ForsterConstraintResolver
from layout.tests.crossing.testGraphCreator import TestGraphCreator
from layout.crossing.nodeRelativePortDistributor import NodeRelativePortDistributor


class BarycenterHeuristicTest(unittest.TestCase):
    def setUp(self):
        self.gb = TestGraphCreator()
        self.random = self.gb.random

    def test_minimizeCrossings_removesCrossingInSimpleCross(self):
        """
        *  *
         \/
         /\
        *  *
        .

        @return Graph of the form above.
        """
        gb = self.gb
        leftNodes = gb.addNodesToLayer(2, gb.makeLayer())
        rightNodes = gb.addNodesToLayer(2, gb.makeLayer())
        gb.eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        gb.eastWestEdgeFromTo(leftNodes[1], rightNodes[0])
        nodes = gb.graph.layers

        portDist = NodeRelativePortDistributor(gb.graph)
        constraintResolver = ForsterConstraintResolver(nodes)

        portDist.calculatePortRanks(nodes[0], PortType.OUTPUT)
        crossMin = BarycenterHeuristic(
            constraintResolver, self.random, portDist, nodes)

        expectedOrder = gb.switchOrderInArray(0, 1, nodes[1])
        gb.minimizeCrossings(crossMin, nodes[1], False, False, True)

        self.assertSequenceEqual(expectedOrder, nodes[1])

    def test_mockRandomizeFirstLayer(self):
        """
         *
         * *  *
         *  \/
         *  /\
         * *  *
         * .
         *
         * @return Graph of the form above.
        """
        gb = self.gb

        leftNodes = gb.addNodesToLayer(2, gb.makeLayer())
        rightNodes = gb.addNodesToLayer(2, gb.makeLayer())
        gb.eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        gb.eastWestEdgeFromTo(leftNodes[1], rightNodes[0])

        nodes = gb.graph.layers
        portDist = NodeRelativePortDistributor(gb.graph)
        constraintResolver = ForsterConstraintResolver(nodes)
        portDist.calculatePortRanks(nodes[0], PortType.OUTPUT)
        crossMin = BarycenterHeuristic(
            constraintResolver, self.random, portDist, nodes)

        expectedOrder = nodes[0][:]
        expectedSwitchedOrder = gb.switchOrderInArray(0, 1, nodes[0])

        gb.minimizeCrossings(crossMin, nodes[0], False, True, True)
        self.assertSequenceEqual(expectedOrder, nodes[0])

        self.random.setChangeBy(-0.01)
        gb.minimizeCrossings(crossMin, nodes[0], False, True, True)

        self.assertSequenceEqual(nodes[0], expectedSwitchedOrder)

    def test_fillingInUnknownBarycenters(self):
        """
         * <pre>
         *   *  *
         *    \/
         *    /\
         * *-*  *
         * .
         * </pre>
         *
         * @return Graph of the form above.
        """
        gb = self.gb
        leftNode = gb.addNodeToLayer(gb.makeLayer())
        middleNodes = gb.addNodesToLayer(2, gb.makeLayer())
        rightNodes = gb.addNodesToLayer(2, gb.makeLayer())
        gb.eastWestEdgeFromTo(middleNodes[0], rightNodes[1])
        gb.eastWestEdgeFromTo(middleNodes[1], rightNodes[0])
        gb.eastWestEdgeFromTo(leftNode, middleNodes[1])

        nodes = gb.graph.layers
        expectedSwitchedOrder = gb.switchOrderInArray(0, 1, nodes[2])
        expectedOrderSecondLayer = nodes[1][:]

        portDist = NodeRelativePortDistributor(gb.graph)
        constraintResolver = ForsterConstraintResolver(nodes)

        crossMin = BarycenterHeuristic(
            constraintResolver, self.random, portDist, nodes)
        portDist.calculatePortRanks(nodes[0], PortType.OUTPUT)
        gb.minimizeCrossings(crossMin, nodes[0], False, True, True)
        portDist.calculatePortRanks(nodes[1], PortType.OUTPUT)
        gb.minimizeCrossings(crossMin, nodes[1], False, False, True)
        self.assertSequenceEqual(nodes[1], expectedOrderSecondLayer)
        gb.minimizeCrossings(crossMin, nodes[2], False, False, True)
        self.assertSequenceEqual(nodes[2], expectedSwitchedOrder)

    def test_assumingFixedPortOrder_givenSimplePortOrderCross_removesCrossingIndependentOfRandom(self):
        """
         * <pre>
         * ____  *
         * |  |\/
         * |__|/\
         *       *
         * .
         * </pre>
         *
         * @return Graph of the form above.
        """
        gb = self.gb
        leftLayer = gb.makeLayer()
        rightLayer = gb.makeLayer()

        leftNode = gb.addNodeToLayer(leftLayer)

        rightTopNode = gb.addNodeToLayer(rightLayer)
        rightBottomNode = gb.addNodeToLayer(rightLayer)

        gb.eastWestEdgeFromTo(leftNode, rightBottomNode)
        gb.eastWestEdgeFromTo(leftNode, rightTopNode)

        gb.setFixedOrderConstraint(leftNode)

        nodes = gb.graph.toNodeArray()

        portDist = NodeRelativePortDistributor(gb.graph)
        constraintResolver = ForsterConstraintResolver(nodes)

        portDist.calculatePortRanks(nodes[0], PortType.OUTPUT)
        crossMin = BarycenterHeuristic(
            constraintResolver, self.random, portDist, nodes)

        expectedOrder = gb.switchOrderInArray(0, 1, nodes[1])

        gb.minimizeCrossings(crossMin, nodes[1], False, False, True)
        self.assertSequenceEqual(nodes[1], expectedOrder)

        self.random.setChangeBy(-0.1)
        self.random.setNextBoolean(False)
        gb.minimizeCrossings(crossMin, nodes[1], False, False, True)

        self.assertIs(nodes[1], expectedOrder)

    def test_assumingFixedPortOrder_givenSimplePortOrderCross_removesCrossingBackwards(self):
        """
         * <pre>
         *
         * *  ___
         *  \/| |
         *  /\|_|
         * *
         * </pre>
         *
        """
        gb = self.gb
        leftNodes = gb.addNodesToLayer(2, gb.makeLayer())
        rightNode = gb.addNodeToLayer(gb.makeLayer())
        gb.eastWestEdgeFromTo(leftNodes[0], rightNode)
        gb.eastWestEdgeFromTo(leftNodes[1], rightNode)
        gb.setFixedOrderConstraint(rightNode)

        nodes = gb.graph.layers

        portDist = NodeRelativePortDistributor(gb.graph)
        constraintResolver = ForsterConstraintResolver(nodes)

        portDist.calculatePortRanks(nodes[1], PortType.INPUT)
        crossMin = BarycenterHeuristic(
            constraintResolver, self.random, portDist, nodes)
        expectedOrder = gb.switchOrderInArray(0, 1, nodes[0])
        gb.minimizeCrossings(crossMin, nodes[0], False, False, False)
        self.assertSequenceEqual(expectedOrder, nodes[0])

    def test_inLayerEdges(self):
        """
         * <pre>
         *       ___
         *    ---| |
         *    |  | |  <- switch this
         * ---+--|_|
         * |  |
         * *--|--*  <- with this
         *    |
         *    ---*
         * .
         * </pre>
         *
         * With fixed Port PortOrder.
         *
         * @return Graph of the form above.
        """
        gb = self.gb
        leftNode = gb.addNodeToLayer(gb.makeLayer())
        rightNodes = gb.addNodesToLayer(3, gb.makeLayer())
        gb.setFixedOrderConstraint(rightNodes[0])
        gb.eastWestEdgeFromTo(leftNode, rightNodes[0])
        gb.addInLayerEdge(rightNodes[0], rightNodes[2], PortSide.WEST)
        gb.eastWestEdgeFromTo(leftNode, rightNodes[1])
        nodes = gb.graph.nodes.toNodeArray()

        portDist = NodeRelativePortDistributor(gb.graph)
        constraintResolver = ForsterConstraintResolver(nodes)

        portDist.calculatePortRanks(nodes[0], PortType.INPUT)
        crossMin = BarycenterHeuristic(
            constraintResolver, self.random, portDist, nodes)

        expectedOrder = gb.getArrayInIndexOrder(nodes[1], 2, 0, 1)
        gb.minimizeCrossings(crossMin, nodes[1], False, False, True)
        self.assertSequenceEqual(nodes[1], expectedOrder)

    def test_northSouthEdges(self):
        """
         * <pre>
         *   ----*
         *   |---*
         *   ||
         * *-++--*
         *   ||
         *  ----
         *  |__|
         * </pre>
         * @return Graph of the form above.
        """
        gb = self.gb
        leftNodes = gb.addNodesToLayer(1, gb.makeLayer())
        middleNodes = gb.addNodesToLayer(4, gb.makeLayer())
        rightNodes = gb.addNodesToLayer(3, gb.makeLayer())
        gb.eastWestEdgeFromTo(leftNodes[0], middleNodes[2])
        gb.eastWestEdgeFromTo(middleNodes[2], rightNodes[2])
        gb.setAsLongEdgeDummy(middleNodes[2])
        gb.addNorthSouthEdge(
            PortSide.NORTH, middleNodes[3], middleNodes[0], rightNodes[0], False)
        gb.addNorthSouthEdge(
            PortSide.NORTH, middleNodes[3], middleNodes[1], rightNodes[1], False)

        layoutUnits = LinkedListMultimap.create()
        nodes = gb.graph.nodes
        for list_ in nodes:
            for node in list_:
                layoutUnit = node.inLayerLayoutUnit
                if layoutUnit is not None:
                    layoutUnits.put(layoutUnit, node)

        portDist = NodeRelativePortDistributor(gb.graph)
        constraintResolver = ForsterConstraintResolver(nodes)

        portDist.calculatePortRanks(nodes[0], PortType.INPUT)

        crossMin = BarycenterHeuristic(
            constraintResolver, self.random, portDist, nodes)
        expectedOrder = gb.getArrayInIndexOrder(nodes[1], 1, 0, 3, 2)

        self.random.setChangeBy(-0.01)
        gb.minimizeCrossings(crossMin, nodes[1], False, False, True)

        self.assertSequenceEqual(nodes[1], expectedOrder)

    def minimizeCrossings(self, crossMin: BarycenterHeuristic, nodes,
                          preOrdered: bool, randomized: bool, forward: bool):
        """
         * Helper method that wraps the nodes array in a list and applies the order back to the array.
        """
        nodeList = list(nodes)
        crossMin.minimizeCrossings(nodeList, preOrdered, randomized, forward)
        nodes.clear()
        nodes.extend(nodeList)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FrameTmplTC('test_sWithStartPadding'))
    suite.addTest(unittest.makeSuite(BarycenterHeuristicTest))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
