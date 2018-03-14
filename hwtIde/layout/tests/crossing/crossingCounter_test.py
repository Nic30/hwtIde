import unittest
from layout.crossing.crossingCounter import CrossingsCounter
from random import Random
from layout.containers import PortSide


class CrossingsCounterTC(unittest.TestCase):
    def setUp(self):
        self.gb = InLayerEdgeTestGraphCreator()
        self.counter = CrossingsCounter()

    def getInitPortOrder(self):
        # [TODO] has to be dict
        portOrder = [0 for _ in range(self.gb.getNumPorts(self.order()))]
        return portOrder
        
    def test_countCrossingsBetweenLayers_fixedPortOrderCrossingOnTwoNodes(self):
        """
         * <pre>
         * ___  ___
         * | |\/| |
         * |_|/\|_|
         * </pre>
        """
        gb = self.gb

        left = gb.addNodeToLayer(gb.makeLayer(gb.graph))
        right = gb.addNodeToLayer(gb.makeLayer(gb.graph))
        gb.eastWestEdgeFromTo(left, right)
        gb.eastWestEdgeFromTo(left, right)
        
        counter = CrossingsCounter(self.getInitPortOrder())

        order = self.order
        self.assertEqual(counter.countCrossingsBetweenLayers(order()[0], order()[1]), 1)
    

    def test_longInLayerCrossings(self):
        """
         * <pre>
         * *
         *  \
         *  /
         * *
         *  \
         * *+--
         *  | |
         * * /
         * *
         * </pre>
         * 
         * @throws Exception
        """
        gb = self.gb
        order = self.order

        nodes = gb.addNodesToLayer(5, gb.makeLayer())
        gb.addInLayerEdge(nodes[0], nodes[1], PortSide.EAST)
        gb.addInLayerEdge(nodes[1], nodes[3], PortSide.EAST)
        gb.addInLayerEdge(nodes[2], nodes[4], PortSide.EAST)

        counter = CrossingsCounter(self.getInitPortOrder())

        self.assertEqual(counter.countInLayerCrossingsOnSide(order()[0], PortSide.EAST), 1)
    
    def test_countCrossingsBetweenLayers_crossFormed(self):
        gb = self.gb
        gb.getCrossFormedGraph()

        counter = CrossingsCounter(self.getInitPortOrder())

        order = self.order
        self.assertEqual(counter.countCrossingsBetweenLayers(order()[0], order()[1]), 1)
    
    def order(self):
        return self.gb.graph.layers

    def test_countCrossingsBetweenLayers_crossFormedMultipleEdgesBetweenSameNodes(self):
        """
         * Constructs a cross formed graph with two edges between the corners
         *
         * <pre>
         * *    *
         *  \\//
         *  //\\
         * *    *
         * .
         * </pre>
        """
        gb = self.gb
        order = self.order

        leftLayer = gb.makeLayer(gb.graph)
        rightLayer = gb.makeLayer(gb.graph)

        topLeft = gb.addNodeToLayer(leftLayer)
        bottomLeft = gb.addNodeToLayer(leftLayer)
        topRight = gb.addNodeToLayer(rightLayer)
        bottomRight = gb.addNodeToLayer(rightLayer)

        topLeftTopPort = gb.addPortOnSide(topLeft, PortSide.EAST)
        topLeftBottomPort = gb.addPortOnSide(topLeft, PortSide.EAST)
        bottomRightBottomPort = gb.addPortOnSide(bottomRight, PortSide.WEST)
        bottomRightTopPort = gb.addPortOnSide(bottomRight, PortSide.WEST)
        gb.addEdgeBetweenPorts(topLeftTopPort, bottomRightTopPort)
        gb.addEdgeBetweenPorts(topLeftBottomPort, bottomRightBottomPort)

        bottomLeftTopPort = gb.addPortOnSide(bottomLeft, PortSide.EAST)
        bottomLeftBottomPort = gb.addPortOnSide(bottomLeft, PortSide.EAST)
        topRightBottomPort = gb.addPortOnSide(topRight, PortSide.WEST)
        topRightTopPort = gb.addPortOnSide(topRight, PortSide.WEST)
        gb.addEdgeBetweenPorts(bottomLeftTopPort, topRightTopPort)
        gb.addEdgeBetweenPorts(bottomLeftBottomPort, topRightBottomPort)

        gd = GraphInfoHolder(gb.graph, CrossMinType.BARYCENTER, None)
        gd.portDistributor().distributePortsWhileSweeping(order(), 1, True)
        counter = CrossingsCounter(self.getInitPortOrder())

        self.assertEqual(counter.countCrossingsBetweenLayers(order()[0], order()[1]), 4)
    
    def test_countCrossingsBetweenLayers_crossWithExtraEdgeInBetween(self):
        gb = self.gb
        gb.getCrossWithExtraEdgeInBetweenGraph()
        counter = CrossingsCounter(self.getInitPortOrder())
        order = self.order
        self.assertEqual(counter.countCrossingsBetweenLayers(order()[0], order()[1]), 3)

    def test_countCrossingsBetweenLayers_ignoreSelfLoops(self):
        gb = self.gb
        order = self.order

        gb.getCrossWithManySelfLoopsGraph()
        counter = CrossingsCounter(self.getInitPortOrder())
        self.assertEqual(counter.countCrossingsBetweenLayers(order()[0], order()[1]), 1)
    
    def test_countCrossingsBetweenLayers_moreComplexThreeLayerGraph(self):
        gb = self.gb
        order = self.order

        gb.getMoreComplexThreeLayerGraph()
        gd = GraphInfoHolder(gb.graph, CrossMinType.BARYCENTER, None)
        gd.portDistributor().distributePortsWhileSweeping(order(), 1, True)
        counter = CrossingsCounter(self.getInitPortOrder())
        self.assertEqual(counter.countCrossingsBetweenLayers(order()[0], order()[1]), 1)
    
    def test_countCrossingsBetweenLayers_fixedPortOrder(self):
        order = self.order
        
        self.gb.getFixedPortOrderGraph()
        counter = CrossingsCounter(self.getInitPortOrder())
        self.assertEqual(counter.countCrossingsBetweenLayers(order()[0], order()[1]), 1)
    

    def test_countCrossingsBetweenLayers_intoSamePort(self):
        """
         * <pre>
         * *   *<- Into same port
         *  \//
         *  //\
         * *   *
         * </pre>
        """
        gb = self.gb
        order = self.order

        leftLayer = gb.makeLayer(gb.graph)
        rightLayer = gb.makeLayer(gb.graph)
        
        topLeft = gb.addNodeToLayer(leftLayer)
        bottomLeft = gb.addNodeToLayer(leftLayer)
        topRight = gb.addNodeToLayer(rightLayer)
        bottomRight = gb.addNodeToLayer(rightLayer)
        
        gb.eastWestEdgeFromTo(topLeft, bottomRight)
        bottomLeftFirstPort = gb.addPortOnSide(bottomLeft, PortSide.EAST)
        bottomLeftSecondPort = gb.addEdgeBetweenPorts(bottomLeft, PortSide.EAST)
        topRightFirstPort = gb.addPortOnSide(topRight, PortSide.WEST)
        
        gb.addEdgeBetweenPorts(bottomLeftFirstPort, topRightFirstPort)
        gb.addEdgeBetweenPorts(bottomLeftSecondPort, topRightFirstPort)
        
        counter = CrossingsCounter(self.getInitPortOrder())

        self.assertEqual(counter.countCrossingsBetweenLayers(order()[0], order()[1]), 2)
    

    def test_countCrossingsBetweenPorts_givenWesternCrossings_OnlyCountsForGivenPorts(self):
        """
         * <pre>
         * *   /*
         * |  /
         * \ /____
         *  x/|  |
         * |/\|  |
         * *  |__|
         * </pre>
        """
        gb = self.gb
        leftNodes = gb.addNodesToLayer(2, gb.makeLayer(gb.graph))
        rightNodes = gb.addNodesToLayer(2, gb.makeLayer(gb.graph))
        gb.eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        gb.eastWestEdgeFromTo(leftNodes[1], rightNodes[1])
        gb.eastWestEdgeFromTo(leftNodes[1], rightNodes[0])

        counter = CrossingsCounter(self.getInitPortOrder())
        counter.initForCountingBetween(leftNodes, rightNodes)
        self.assertEqual(counter.countCrossingsBetweenPortsInBothOrders(rightNodes[1].getPorts().get(1),
                rightNodes[1].getPorts().get(0)).getFirst(), 1)
    
    def test_countCrossingsBetweenPorts_GivenCrossingsOnEasternSide_(self):
        """
         * <pre>
         * ___
         * | |\/*
         * |_|/\*
         * </pre>
        """
        gb = self.gb
        leftNodes = gb.addNodesToLayer(1, gb.makeLayer())
        rightNodes = gb.addNodesToLayer(2, gb.makeLayer())
        gb.eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        gb.eastWestEdgeFromTo(leftNodes[0], rightNodes[0])

        counter = CrossingsCounter(self.getInitPortOrder())
        counter.initForCountingBetween(leftNodes, rightNodes)
        self.assertEqual(counter
                .countCrossingsBetweenPortsInBothOrders(leftNodes[0].getPorts().get(0), leftNodes[0].getPorts().get(1))
                .getFirst(), 1)
    

    def test_countingTwoDifferentGraphs_DoesNotInterfereWithEachOther(self):
        """
         * <pre>
         * *---         *---
         * ___ \       ___  \
         * | |\/* and: | |--* 
         * | |/\*      | |--*
         * |_|         |_|
         * </pre>
        """
        gb = self.gb
        leftNodes = gb.addNodesToLayer(3, gb.makeLayer())
        rightNodes = gb.addNodesToLayer(3, gb.makeLayer())
        leftNode = leftNodes[1]
        leftPorts = gb.addPortsOnSide(2, leftNode, PortSide.EAST)
        gb.eastWestEdgeFromTo(leftNodes[2], rightNodes[1])
        gb.eastWestEdgeFromTo(leftPorts[0], rightNodes[1])
        gb.eastWestEdgeFromTo(leftPorts[1], rightNodes[0])
        gb.eastWestEdgeFromTo(leftNodes[0], rightNodes[0])

        counter = CrossingsCounter(self.getInitPortOrder())
        counter.initForCountingBetween(leftNodes, rightNodes)
        self.assertEqual(counter
                .countCrossingsBetweenPortsInBothOrders(leftNode.getPorts().get(0), leftNode.getPorts().get(1))
                .getFirst(), 1)

        counter.switchPorts(leftPorts[0], leftPorts[1])
        leftNode.getPorts().set(0, leftPorts[1])
        leftNode.getPorts().set(1, leftPorts[0])
        self.assertEqual(counter
                .countCrossingsBetweenPortsInBothOrders(leftNode.getPorts().get(0), leftNode.getPorts().get(1))
                .getFirst(), 0)

    def test_countCrossingsBetweenPorts_twoEdgesIntoSamePort(self):
        """
         * <pre>
         * *   *
         *  \//
         *  //\
         * *   *
         * ^Into same port
         * </pre>
        """
        gb = self.gb
        order = self.order

        leftLayer = gb.makeLayer()
        rightLayer = gb.makeLayer()
        
        topLeft = gb.addNodeToLayer(leftLayer)
        bottomLeft = gb.addNodeToLayer(leftLayer)
        topRight = gb.addNodeToLayer(rightLayer)
        bottomRight = gb.addNodeToLayer(rightLayer)
        
        gb.eastWestEdgeFromTo(topLeft, bottomRight)
        bottomLeftPort = gb.addPortOnSide(bottomLeft, PortSide.EAST)
        topRightPort = gb.addPortOnSide(topRight, PortSide.WEST)
        
        gb.addEdgeBetweenPorts(bottomLeftPort, topRightPort)
        gb.addEdgeBetweenPorts(bottomLeftPort, topRightPort)
        
        
        counter = CrossingsCounter(self.getInitPortOrder())
        counter.initForCountingBetween(order()[0], order()[1])
        
        self.assertEqual(counter.countCrossingsBetweenPortsInBothOrders(bottomLeftPort, topLeft.getPorts().get(0)).getFirst(),
                2)
    

    #@Ignore
    #def benchmark():
    #    makeTwoLayerRandomGraphWithNodesPerLayer(6000, 6)
    #
    #    counter = CrossingsCounter(self.getInitPortOrder())
    #    System.out.println("Starting")
    #    length = 400
    #    times = new long[length]
    #    for (int i = 0 i < length i++):
    #        long tick = new Date().getTime()
    #        counter.countCrossingsBetweenLayers(order()[0], order()[1])
    #        times[i] = new Date().getTime() - tick
    #    
    #    System.out.println(Arrays.stream(times).min())
    #

    def makeTwoLayerRandomGraphWithNodesPerLayer(self, numNodes: int, edgesPerNode: int):
        gb = self.gb
        leftNodes = gb.addNodesToLayer(numNodes, gb.makeLayer())
        rightNodes = gb.addNodesToLayer(numNodes, gb.makeLayer())
        random = Random(0)
        for i in range(edgesPerNode * numNodes):
            if random.randbits(1):
                left = leftNodes[random.nextInt(numNodes)]
                right = rightNodes[random.nextInt(numNodes)]
                gb.eastWestEdgeFromTo(left, right)
            else:
                gb.addInLayerEdge(leftNodes[random.nextInt(numNodes)],
                                  leftNodes[random.nextInt(numNodes)],
                                  PortSide.EAST)

        for node in rightNodes:
            node.cachePortSides()
        
        for node in leftNodes:
            node.cachePortSides()
        
    @staticmethod
    def getNumPorts(currentOrder):
        numPorts = 0
        for lNodes in currentOrder:
            for node in lNodes:
                numPorts += len(node.getPorts())
        return numPorts

