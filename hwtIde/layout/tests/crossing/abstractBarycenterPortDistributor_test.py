import unittest

from layout.tests.crossing.testGraphCreator import TestGraphCreator
from layout.containers.constants import PortSide


class AbstractBarycenterPortDistributorTC(unittest.TestCase):
    def setUp(self):
        self.gb = TestGraphCreator()

    def test_distributePortsOnSide_GivenCrossOnWesternSide_ShouldRemoveCrossing(self):
        """
        <pre>
        *  ___
         \/| |
         /\| |
        *  |_|
        </pre>
        """
        gb = self.gb
        leftNodes = gb.addNodesToLayer(2, gb.makeLayer())
        rightNode = gb.addNodeToLayer(gb.makeLayer())
        gb.eastWestEdgeFromTo(leftNodes[0], rightNode)
        gb.eastWestEdgeFromTo(leftNodes[1], rightNode)

        _nodes = list(rightNode.iterPorts())
        expectedPortOrderRightNode = [_nodes[1], _nodes[0]]

        self.distributePortsInCompleteGraph(4)

        self.assertSequenceEqual(rightNode, expectedPortOrderRightNode)

    def test_distributePortsOfGraph_GivenCrossOnBothSides_ShouldRemoveCrossin(self):
        """
         * <pre>
         * *  ___  *
         *  \/| |\/
         *  /\| |/\
         * *  |_|  *
         * </pre>
         *
        """
        gb = self.gb

        leftNodes = gb.addNodesToLayer(2, gb.makeLayer())
        middleNode = gb.addNodeToLayer(gb.makeLayer())
        rightNodes = gb.addNodesToLayer(2, gb.makeLayer())
        gb.eastWestEdgeFromTo(middleNode, rightNodes[1])
        gb.eastWestEdgeFromTo(middleNode, rightNodes[0])
        gb.eastWestEdgeFromTo(leftNodes[0], middleNode)
        gb.eastWestEdgeFromTo(leftNodes[1], middleNode)

        expectedPortOrderMiddleNode = gb.copyPortsInIndexOrder(middleNode, 1, 0, 3, 2)

        gb.distributePortsInCompleteGraph(8)

        self.assertSequenceEqual(middleNode.getPorts(), expectedPortOrderMiddleNode)

    def distributePortsInCompleteGraph(self, numberOfPorts: int):
        gb = self.gb
        gd = GraphInfoHolder(gb.graph, CrossMinType.BARYCENTER, None)
        nodes = gb.graph.leyers
        for i in range(len(nodes)):
            gd.portDistributor().distributePortsWhileSweeping(nodes, i, True)

        for i in range(0, len(nodes) - 1, -1):
            gd.portDistributor().distributePortsWhileSweeping(nodes, i, False)

    def test_distributePortsOfGraph_GivenCrossOnEasternSide_ShouldRemoveCrossing(self):
        """
         * <pre>
         * ___
         * | |\ /-*
         * | | x
         * |_|/ \-*
         * </pre>
        """
        leftNode = addNodeToLayer(makeLayer(getGraph()))
        rightNodes = addNodesToLayer(2, makeLayer(getGraph()))
        eastWestEdgeFromTo(leftNode, rightNodes[1])
        eastWestEdgeFromTo(leftNode, rightNodes[0])

        expectedPortOrderLeftNode = copyPortsInIndexOrder(leftNode, 1, 0)

        distributePortsInCompleteGraph(4)

        self.assertSequenceEqual(leftNode.iterPorts(), expectedPortOrderLeftNode)

    def test_distributePortsOfGraph_GivenInLayerEdgePortOrderCrossing_ShouldRemoveIt(self):
        """
         * <pre>
         *     *-----
         *     *-\  |
         *   ____ | |
         * * |  |-+--
         *   |__|-|
         * </pre>
        """
        addNodeToLayer(makeLayer())
        nodes = addNodesToLayer(3, makeLayer())
        addInLayerEdge(nodes[0], nodes[2], PortSide.EAST)
        addInLayerEdge(nodes[1], nodes[2], PortSide.EAST)

        expectedPortOrderLowerNode = copyPortsInIndexOrder(nodes[2], 1, 0)

        distributePortsInCompleteGraph(4)

        self.assertSequenceEqual(nodes[2].iterPorts(), expectedPortOrderLowerNode)

    def test_distributePortsOfGraph_GivenNorthSouthPortOrderCrossing_ShouldSwitchPortOrder(self):
        """
         * <pre>
         *     *-->*
         *     |
         *   *-+-->*
         *   | |
         *  _|_|_
         *  |   |
         *  |___|
         *  .
         * </pre>
        """
        leftNodes = addNodesToLayer(3, makeLayer())
        rightNodes = addNodesToLayer(2, makeLayer())

        addNorthSouthEdge(PortSide.NORTH, leftNodes[2], leftNodes[1], rightNodes[1], False)
        addNorthSouthEdge(PortSide.NORTH, leftNodes[2], leftNodes[0], rightNodes[0], False)

        expectedPortOrderLowerNode = Lists.newArrayList(leftNodes[2].getPorts().get(1), leftNodes[2].getPorts().get(0))

        distributePortsInCompleteGraph(6)

        self.assertSequenceEqual(leftNodes[2].iterPorts(), expectedPortOrderLowerNode)

    def test_distributePortsWhileSweeping_givenSimpleCross_ShouldRemoveCrossing(self):
        """
         * <pre>
         * ___  ____
         * | |\/|  |
         * |_|/\|  |
         *      |--|
         * </pre>
        """
        leftNode = addNodeToLayer(makeLayer())
        rightNode = addNodeToLayer(makeLayer())
        eastWestEdgeFromTo(leftNode, rightNode)
        eastWestEdgeFromTo(leftNode, rightNode)
        expectedPortRightNode = copyPortsInIndexOrder(rightNode, 1, 0)
        nodeArray = graph.toNodeArray()
        portDist = LayerTotalPortDistributor(len(nodeArray))
        IInitializable.init(Arrays.asList(portDist), nodeArray)
        portDist.distributePortsWhileSweeping(nodeArray, 1, True)

        assertThat(rightNode.getPorts(), is(expectedPortRightNode))

    # TODO this is a problem which currently cannot be solved by our algorithm :-(
    #def distributePortsOnSide_partlyCrossHierarchicalEdges_CrossHierarchyStaysOuterChanges(self):
    #   """
    #    * <pre>
    #    * ____
    #    * | *+--  *
    #    * |  |  \/
    #    * |  |\ /\
    #    * | *+-x  *
    #    * |__|  \
    #    *        -*
    #    * </pre>
    #   """
    #    leftOuterNode = addNodeToLayer(makeLayer())
    #    rightNodes = addNodesToLayer(3, makeLayer())
    #    LPort[] leftOuterPorts = addPortsOnSide(3, leftOuterNode, PortSide.EAST)
    #    LGraph leftInnerGraph = nestedGraph(leftOuterNode)
    #    leftInnerNodes = addNodesToLayer(2, makeLayer(leftInnerGraph))
    #    leftInnerDummyNodes = new LNode[2]
    #    Layer dummyLayer = makeLayer()
    #    leftInnerDummyNodes[0] = addExternalPortDummyNodeToLayer(dummyLayer, leftOuterPorts[0])
    #    leftInnerDummyNodes[1] = addExternalPortDummyNodeToLayer(dummyLayer, leftOuterPorts[2])
    #    eastWestEdgeFromTo(leftInnerNodes[0], leftInnerDummyNodes[0])
    #    eastWestEdgeFromTo(leftInnerNodes[1], leftInnerDummyNodes[1])
    #    eastWestEdgeFromTo(leftOuterPorts[0], rightNodes[1])
    #    eastWestEdgeFromTo(leftOuterPorts[1], rightNodes[2])
    #    eastWestEdgeFromTo(leftOuterPorts[2], rightNodes[0])
    #    # leftOuterNode.setProperty(InternalProperties.HAS_HIERARCHICAL_AND_NORMAL_PORTS, True)
    #    setPortOrderFixed(leftOuterNode)
    #
    #    expectedOrder = Lists.newArrayList(switchOrderInArray(1, 2, leftOuterPorts))
    #
    #    distributePortsInCompleteGraph(8)
    #
    #    assertThat(leftOuterNode.getPorts(), is(expectedOrder))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(AbstractBarycenterPortDistributorTC('test_distributePortsOnSide_GivenCrossOnWesternSide_ShouldRemoveCrossing'))
    # suite.addTest(unittest.makeSuite(AbstractBarycenterPortDistributorTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

