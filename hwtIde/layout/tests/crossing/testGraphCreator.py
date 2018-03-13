from layout.containers import Layout, PortSide
from _random import Random

class MockRandom(Random):
        def __init__
        current = 0
        changeBy = 0.0001
        nextBoolean = True

        
        public boolean nextBoolean(self):
            return nextBoolean
        

        
        public float nextFloat(self):
            current += changeBy
            return current
        

        
        public double nextDouble(self):
            return nextFloat()
        

        def setNextBoolean(final boolean nextBoolean):
            this.nextBoolean = nextBoolean
        

        def setChangeBy(final double changeBy):
            this.changeBy = changeBy
        

        def setCurrent(final float current):
            this.current = current


class TestGraphCreator():
    """
    Use to create test graphs. 
    :attention: Layout algorithm assumes the ports to be
        ordered in a clockwise manner. You must think about this yourself when
        constructing a test graph. This means that the methods for creating edges
        cannot be used in every case.
    TODO consider moving all downward into base
    """
    def __init__(self):
        self.portId = 0
        self.nodeId = 0
        self.edgeId = 0
        self.random = MockRandom()
        graph = Layout()
        self.setUpGraph(graph)

    def getGraph(self, graph):
        self.setUpGraph(graph)
        return graph

    def setUpGraph(self, g: Layout):
        g.setProperty(LayeredOptions.EDGE_ROUTING,
                      EdgeRouting.ORTHOGONAL)
        g.setProperty(InternalProperties.RANDOM,
                      self.random)
        return g

    def getEmptyGraph(self) -> Layout:
        """
        Creates empty graph.

        :return: empty graph
        """
        graph = Layout()
        self.setUpGraph(graph)
        return graph

    def getTwoNodesNoConnectionGraph(self) -> Layout: 
        """
        Creates two nodes with no connection between them.

        :return: graph with two nodes with no connection between them.
        """
        layer = self.makeLayer(self.graph)
        self.addNodeToLayer(layer)
        self.addNodeToLayer(layer)
        return self.graph

    def getCrossFormedGraph(self):
        """
        <pre>
        *  *
         \/
         /\
        *  *
        .
        </pre>

        :return: Graph of the form above.
        """

        leftLayer = self.makeLayer(self.graph)
        rightLayer = self.makeLayer(self.graph)

        topLeft = self.addNodeToLayer(leftLayer)
        bottomLeft = self.addNodeToLayer(leftLayer)
        topRight = self.addNodeToLayer(rightLayer)
        bottomRight = self.addNodeToLayer(rightLayer)

        self.eastWestEdgeFromTo(topLeft, bottomRight)
        self.eastWestEdgeFromTo(bottomLeft, topRight)
        return self.graph

    def multipleEdgesAndSingleEdge(self) -> Layout:
        """
        <pre>
        *
         \\
          \\
        *---*
        .
        </pre>

        :return: Graph of the form above.
        """
        makeLayer = self.makeLayer
        addNodeToLayer = self.addNodeToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        graph = self.graph

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        topLeft = addNodeToLayer(leftLayer)
        bottomLeft = addNodeToLayer(leftLayer)
        bottomRight = addNodeToLayer(rightLayer)

        eastWestEdgeFromTo(topLeft, bottomRight)
        eastWestEdgeFromTo(topLeft, bottomRight)
        eastWestEdgeFromTo(bottomLeft, bottomRight)
        return graph

    def getCrossFormedGraphWithConstraintsInSecondLayer(self):
        """
        <pre>
        *  *  <- this node must be ...
         \/
         /\
        *  *  <- before this node.
        .
        </pre>

        @return Graph of the form above.
        """
        self.getCrossFormedGraph()
        layerOne = self.graph.layers[1]
        topNode = layerOne[0]
        secondNode = layerOne[1]
        self.setInLayerOrderConstraint(topNode, secondNode)

        return self.graph

    def getCrossFormedGraphConstraintsPreventAnySwitch(self):
        """
        <pre>
        this node must be.. -> *  *  <- and this node must be ...
                                \/
                                /\
           before this node -> *  *  <- before this node.
        .
        </pre>

        @return Graph of the form above.
        """
        makeLayer = self.makeLayer
        addNodeToLayer = self.addNodeToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        graph = self.graph
        setInLayerOrderConstraint = self.setInLayerOrderConstraint

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        topLeft = addNodeToLayer(leftLayer)
        bottomLeft = addNodeToLayer(leftLayer)
        topRight = addNodeToLayer(rightLayer)
        bottomRight = addNodeToLayer(rightLayer)

        eastWestEdgeFromTo(topLeft, bottomRight)
        eastWestEdgeFromTo(bottomLeft, topRight)
        setInLayerOrderConstraint(topRight, bottomRight)
        setInLayerOrderConstraint(topLeft, bottomLeft)

        return graph

    def getOneNodeGraph(self):
        """
        Creates graph with only one node.

        @return graph with only one node.
        """
        layer = self.makeLayer(self.graph)
        self.addNodeToLayer(layer)

        return self.graph

    def getInLayerEdgesGraph(self):
        """
        <pre>
          --*
          |
        *-+-*-*
          |
          --*
        .
        </pre>

        @return graph of the form above
        """
        graph = self.graph
        makeLayer = self.makeLayer
        addNodeToLayer = self.addNodeToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        leftLayer = makeLayer(graph)
        middleLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        leftNode = addNodeToLayer(leftLayer)
        middleNodes = self.addNodesToLayer(3, middleLayer)
        rightNode = addNodeToLayer(rightLayer)

        # add east side ports first to get expected port ordering
        eastWestEdgeFromTo(middleNodes[1], rightNode)
        eastWestEdgeFromTo(leftNode, middleNodes[1])
        self.addInLayerEdge(middleNodes[0], middleNodes[2], PortSide.WEST)

        return graph

    def getInLayerEdgesGraphWhichResultsInCrossingsWhenSwitched(self):
        """
        <pre>
          --*
          |
          --*

         *--*
        .
        </pre>

        @return graph of the form above
        """
        graph = self.graph
        makeLayer = self.makeLayer
        addNodeToLayer = self.addNodeToLayer
        addNodesToLayer = self.addNodesToLayer

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        leftNode = addNodeToLayer(leftLayer)
        rightNodes = addNodesToLayer(3, rightLayer)

        self.addInLayerEdge(rightNodes[0], rightNodes[1], PortSide.WEST)
        self.eastWestEdgeFromTo(leftNode, rightNodes[2])

        return graph

    def getMultipleEdgesBetweenSameNodesGraph(self):
        """
        Constructs a cross formed graph with two edges between the corners

        <pre>
        *    *
         \\//
         //\\
        *    *
        .
        </pre>

        @return Graph of the form above.
        """
        graph = self.graph
        makeLayer = self.makeLayer
        addNodeToLayer = self.addNodeToLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        topLeft = addNodeToLayer(leftLayer)
        bottomLeft = addNodeToLayer(leftLayer)
        topRight = addNodeToLayer(rightLayer)
        bottomRight = addNodeToLayer(rightLayer)

        eastWestEdgeFromTo(topLeft, bottomRight)
        eastWestEdgeFromTo(topLeft, bottomRight)
        eastWestEdgeFromTo(bottomLeft, topRight)
        eastWestEdgeFromTo(bottomLeft, topRight)

        return graph

    def getCrossWithExtraEdgeInBetweenGraph(self):
        """
        <pre>
        *   *
         \ /
        *-+-*
         / \
        *   *
        .
        </pre>

        @return graph of the form above
        """
        graph = self.graph
        makeLayer = self.makeLayer
        eastWestEdgeFromTo = self.eastWestEdgeFromTo
        addNodesToLayer = self.addNodesToLayer

        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        leftNodes = addNodesToLayer(3, leftLayer)
        rightNodes = addNodesToLayer(3, rightLayer)

        eastWestEdgeFromTo(leftNodes[0], rightNodes[2])
        eastWestEdgeFromTo(leftNodes[1], rightNodes[1])
        eastWestEdgeFromTo(leftNodes[2], rightNodes[0])

        return graph

    def getCrossWithManySelfLoopsGraph(self):
        """
        Cross formed graph, but each node has three extra self loop edges.

        <pre>
        *  *
         \/
         /\
        *  *
        .
        </pre>

        @return Graph of the form above.
        """
        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        topLeft = addNodeToLayer(leftLayer)
        bottomLeft = addNodeToLayer(leftLayer)
        topRight = addNodeToLayer(rightLayer)
        bottomRight = addNodeToLayer(rightLayer)

        topLeftPort = addPortOnSide(topLeft, PortSide.EAST)
        bottomLeftPort = addPortOnSide(bottomLeft, PortSide.EAST)

        selfLoopCrossGraph = graph
        for layer in selfLoopCrossGraph:
            for node in layer:
                selfLoopOn(node, PortSide.EAST)
                selfLoopOn(node, PortSide.EAST)
                selfLoopOn(node, PortSide.EAST)
                selfLoopOn(node, PortSide.WEST)
                selfLoopOn(node, PortSide.WEST)
                selfLoopOn(node, PortSide.WEST)

        topRightPort = addPortOnSide(topRight, PortSide.WEST)
        bottomRightPort = addPortOnSide(bottomRight, PortSide.WEST)

        addEdgeBetweenPorts(topLeftPort, bottomRightPort)
        addEdgeBetweenPorts(bottomLeftPort, topRightPort)
        return selfLoopCrossGraph

    def selfLoopOn(node: LNode, side: PortSide) -> None:
        """
        Test for self loop.
        """
        addEdgeBetweenPorts(addPortOnSide(node, side), addPortOnSide(node, side))

    def getMoreComplexThreeLayerGraph(self):
        """
        <pre>
        *\  --*
          \/ /
        *-*===*
         + /
        * * --*
        .
        </pre>
        
        @return Graph of the form above.
        """
        leftLayer = makeLayer(graph)
        middleLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        leftNodes = addNodesToLayer(3, leftLayer)
        middleNodes = addNodesToLayer(2, middleLayer)
        rightNodes = addNodesToLayer(3, rightLayer)

        leftMiddleNodePort = addPortOnSide(leftNodes[1], PortSide.EAST)
        middleLowerNodePortEast = addPortOnSide(middleNodes[1], PortSide.EAST)
        middleUpperNodePortEast = addPortOnSide(middleNodes[0], PortSide.EAST)
        rightUpperNodePort = addPortOnSide(rightNodes[0], PortSide.WEST)
        rightMiddleNodePort = addPortOnSide(rightNodes[1], PortSide.WEST)

        addEdgeBetweenPorts(middleUpperNodePortEast, rightUpperNodePort)
        addEdgeBetweenPorts(middleUpperNodePortEast, rightMiddleNodePort)
        addEdgeBetweenPorts(middleUpperNodePortEast, rightMiddleNodePort)
        eastWestEdgeFromTo(middleLowerNodePortEast, rightNodes[2])
        eastWestEdgeFromTo(leftMiddleNodePort, middleNodes[0])
        eastWestEdgeFromTo(middleNodes[1], rightUpperNodePort)
        eastWestEdgeFromTo(leftMiddleNodePort, middleNodes[1])
        eastWestEdgeFromTo(leftNodes[2], middleNodes[0])
        eastWestEdgeFromTo(leftNodes[0], middleNodes[0])

        return graph

    def getFixedPortOrderGraph(self):
        """
        <pre>
        ____  *
        |  |\/
        |__|/\
              *
        .
        </pre>
        
        Port order fixed.
        
        @return Graph of the form above.
        """
        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        leftNode = addNodeToLayer(leftLayer)
        leftNode.setProperty(LayeredOptions.PORT_CONSTRAINTS, PortConstraints.FIXED_ORDER)

        rightTopNode = addNodeToLayer(rightLayer)
        rightBottomNode = addNodeToLayer(rightLayer)

        eastWestEdgeFromTo(leftNode, rightBottomNode)
        eastWestEdgeFromTo(leftNode, rightTopNode)

        return graph

    def getGraphNoCrossingsDueToPortOrderNotFixed(self):
        """
        <pre>
        ____  *
        |  |\/
        |__|/\
              *
        .
        </pre>

        Port order not fixed

        @return Graph of the form above.
        """
        leftLayer = makeLayer(graph)
        rightLayer = makeLayer(graph)

        leftNode = addNodeToLayer(leftLayer)

        rightTopNode = addNodeToLayer(rightLayer)
        rightBottomNode = addNodeToLayer(rightLayer)

        eastWestEdgeFromTo(leftNode, rightBottomNode)
        eastWestEdgeFromTo(leftNode, rightTopNode)

        return graph

    def getSwitchOnlyOneSided(self):
        """
        <pre>
        *  *---*
         \/
         /\
        *  *---*
        .
        </pre>

        @return Graph of the form above.
        """
        layers = makeLayers(3)

        leftNodes = addNodesToLayer(2, layers[0])
        middleNodes = addNodesToLayer(2, layers[1])
        rightNodes = addNodesToLayer(2, layers[2])

        eastWestEdgeFromTo(middleNodes[0], rightNodes[0])
        eastWestEdgeFromTo(middleNodes[1], rightNodes[1])
        eastWestEdgeFromTo(leftNodes[0], middleNodes[1])
        eastWestEdgeFromTo(leftNodes[1], middleNodes[0])

        return graph

    def getSwitchOnlyEastOneSided(self):
        """
        <pre>
        *--*  *
            \/
            /\
        *--*  *
        .
        </pre>

        @return Graph of the form above.
        """
        layers = makeLayers(3)

        leftNodes = addNodesToLayer(2, layers[0])
        middleNodes = addNodesToLayer(2, layers[1])
        rightNodes = addNodesToLayer(2, layers[2])

        eastWestEdgeFromTo(leftNodes[0], middleNodes[0])
        eastWestEdgeFromTo(leftNodes[1], middleNodes[1])
        eastWestEdgeFromTo(middleNodes[0], rightNodes[1])
        eastWestEdgeFromTo(middleNodes[1], rightNodes[0])

        return graph

    def getFixedPortOrderInLayerEdgesDontCrossEachOther(self):
        """
        <pre>
        ____
        |  |----
        |__|\  |
        ____ | |
        |  |/  |
        |__|---|
        .
        </pre>
        
        Port order fixed.
        
        @return Graph of the form above.
        """
        layer = makeLayer(graph)
        nodes = addNodesToLayer(2, layer)
        setFixedOrderConstraint(nodes[0])
        setFixedOrderConstraint(nodes[1])
        # must add ports and edges manually, due to clockwise port ordering
        upperPortUpperNode = addPortOnSide(nodes[0], PortSide.EAST)
        lowerPortUpperNode = addPortOnSide(nodes[0], PortSide.EAST)
        upperPortLowerNode = addPortOnSide(nodes[1], PortSide.EAST)
        lowerPortLowerNode = addPortOnSide(nodes[1], PortSide.EAST)
        addEdgeBetweenPorts(upperPortUpperNode, lowerPortLowerNode)
        addEdgeBetweenPorts(lowerPortUpperNode, upperPortLowerNode)
        
        return graph

    """
    <pre>
    ____
    |  |----
    |__|\  |
    ____ | |
    |  |-+--
    |__|-|
    .
    </pre>
    
    Port order fixed.
    
    @return Graph of the form above.
    """
    def getFixedPortOrderInLayerEdgesWithCrossings(self):
        Layer layer = makeLayer(graph)
        LNode[] nodes = addNodesToLayer(2, layer)
        setFixedOrderConstraint(nodes[0])
        setFixedOrderConstraint(nodes[1])
        addInLayerEdge(nodes[0], nodes[1], PortSide.EAST)
        addInLayerEdge(nodes[0], nodes[1], PortSide.EAST)

        
        return graph
    

    """
    <pre>
         ____
       / |  |
    *-+--|  |\
      | /|  |-+-*
    *-++-|__| |
      ||      |
      || ___  |
      | \| | /
    *-+--| |/
    *-+--|_|
       \
        \
         *
    .
    </pre>
    
    Port order fixed.
    
    @return Graph of the form above.
    """
    def getMoreComplexInLayerGraph(self):
        Layer[] layers = makeLayers(3)
        LNode[] leftNodes = addNodesToLayer(4, layers[0])
        LNode[] middleNodes = addNodesToLayer(3, layers[1])
        LNode rightNode = addNodeToLayer(layers[2])
        setFixedOrderConstraint(middleNodes[0])
        setFixedOrderConstraint(middleNodes[1])

        eastWestEdgeFromTo(leftNodes[1], middleNodes[0])

        eastWestEdgeFromTo(leftNodes[3], middleNodes[1])
        eastWestEdgeFromTo(leftNodes[2], middleNodes[1])
        addInLayerEdge(middleNodes[0], middleNodes[1], PortSide.WEST)
        eastWestEdgeFromTo(leftNodes[0], middleNodes[0])
        addInLayerEdge(middleNodes[0], middleNodes[2], PortSide.WEST)

        addInLayerEdge(middleNodes[0], middleNodes[1], PortSide.EAST)
        eastWestEdgeFromTo(middleNodes[0], rightNode)

        
        return graph

    """
     * <pre>
     * *==*  *
     *     \/
     *     /\
     * *==*  *
     * .
     * </pre>
     *
     * First Layer and last layer in fixed order.
     *
     * @return graph of the form above.
    """
    def getGraphWhichCouldBeWorsenedBySwitch(self):
        Layer[] layers = makeLayers(3)
        LNode[] leftNodes = addNodesToLayer(2, layers[0])
        LNode[] middleNodes = addNodesToLayer(2, layers[1])
        LNode[] rightNodes = addNodesToLayer(2, layers[2])

        setInLayerOrderConstraint(leftNodes[0], leftNodes[1])
        setInLayerOrderConstraint(rightNodes[0], rightNodes[1])

        eastWestEdgeFromTo(middleNodes[0], rightNodes[1])
        eastWestEdgeFromTo(middleNodes[1], rightNodes[0])
        eastWestEdgeFromTo(leftNodes[0], middleNodes[0])
        eastWestEdgeFromTo(leftNodes[0], middleNodes[0])
        eastWestEdgeFromTo(leftNodes[1], middleNodes[1])
        eastWestEdgeFromTo(leftNodes[1], middleNodes[1])

        
        return graph
    
    """
     * <pre>
     *     * <-- this ...
     *    /
     * *-+-* <-- cannot switch with this
     *  / _|__
     * *  |  |
     *    |__|
     *
     * .
     * </pre>
     *
     * @return graph of the form above.
     """
    def getNodesInDifferentLayoutUnitsPreventSwitch(self):
        Layer[] layers = makeLayers(2)
        LNode[] leftNodes = addNodesToLayer(2, layers[0])
        LNode[] rightNodes = addNodesToLayer(3, layers[1])

        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])

        addNorthSouthEdge(PortSide.EAST, rightNodes[2], rightNodes[1], leftNodes[0], True)

        rightNodes[1].setProperty(InternalProperties.IN_LAYER_LAYOUT_UNIT, rightNodes[2])
        rightNodes[2].setProperty(InternalProperties.IN_LAYER_LAYOUT_UNIT, rightNodes[2])

        
        return graph
    

    """
     * <pre>
     *  ---*
     *  |
     *  | ____
     * *+-|  |
     * *+-|  |
     *   \|__|
     * Port order not fixed.
     * .
     * </pre>
     *
     * @return Graph of the form above.
     """
    def multipleInBetweenLayerEdgesIntoNodeWithNoFixedPortOrder(self):
        Layer leftLayer = makeLayer(graph)
        LNode[] leftNodes = addNodesToLayer(2, leftLayer)
        Layer rightLayer = makeLayer(graph)
        LNode[] rightNodes = addNodesToLayer(2, rightLayer)

        addInLayerEdge(rightNodes[0], rightNodes[1], PortSide.WEST)
        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        
        return graph
    

    """
     * <pre>
     *  ---*
     *  |
     *  | ____
     * *+-|  |
     * *+-|  |
     *  | |__|
     *   \
     *    *
     * Port order not fixed.
     * .
     * </pre>
     *
     * @return Graph of the form above.
     """
    def multipleInBetweenLayerEdgesIntoNodeWithNoFixedPortOrderCauseCrossings(self):
        Layer leftLayer = makeLayer(graph)
        LNode[] leftNodes = addNodesToLayer(2, leftLayer)
        Layer rightLayer = makeLayer(graph)
        LNode[] rightNodes = addNodesToLayer(3, rightLayer)

        addInLayerEdge(rightNodes[0], rightNodes[2], PortSide.WEST)
        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        
        return graph
    

    """
     * <pre>
     * *----*
     *  \\
     *   \--*
     *    --*
     * *---/
     *  \---*
     * </pre>
     *
     * .
     *
     * @return Graph of the form above.
     """
    def getSwitchedProblemGraph(self):
        LNode[] leftNodes = addNodesToLayer(2, makeLayer(graph))
        LNode[] rightNodes = addNodesToLayer(4, makeLayer(graph))

        eastWestEdgeFromTo(leftNodes[1], rightNodes[2])
        eastWestEdgeFromTo(leftNodes[1], rightNodes[3])

        eastWestEdgeFromTo(leftNodes[0], rightNodes[0])
        eastWestEdgeFromTo(leftNodes[0], rightNodes[1])
        eastWestEdgeFromTo(leftNodes[0], rightNodes[2])

        
        return graph
    

    """
     * <pre>
     * *   *<- Into same port
     *  \//
     *  //\
     * *   *
     * </pre>
     *
     * .
     *
     * @return Graph of the form above.
     """
    def twoEdgesIntoSamePort(self):
        Layer leftLayer = makeLayer(graph)
        Layer rightLayer = makeLayer(graph)

        LNode topLeft = addNodeToLayer(leftLayer)
        LNode bottomLeft = addNodeToLayer(leftLayer)
        LNode topRight = addNodeToLayer(rightLayer)
        LNode bottomRight = addNodeToLayer(rightLayer)

        eastWestEdgeFromTo(topLeft, bottomRight)
        LPort bottomLeftFirstPort = addPortOnSide(bottomLeft, PortSide.EAST)
        LPort bottomLeftSecondPort = addPortOnSide(bottomLeft, PortSide.EAST)
        LPort topRightFirstPort = addPortOnSide(topRight, PortSide.WEST)
        LPort topRightSecondPort = addPortOnSide(topRight, PortSide.WEST)

        addEdgeBetweenPorts(bottomLeftFirstPort, topRightFirstPort)
        addEdgeBetweenPorts(bottomLeftSecondPort, topRightSecondPort)
        
        return graph
    

    """
     * <pre>
     * *---* <- Into same port
     *   /
     *  /
     * *---*
     * </pre>
     *
     * .
     *
     * @return Graph of the form above.
     """
    def twoEdgesIntoSamePortCrossesWhenSwitched(self):
        Layer leftLayer = makeLayer(graph)
        Layer rightLayer = makeLayer(graph)

        LNode topLeft = addNodeToLayer(leftLayer)
        LNode bottomLeft = addNodeToLayer(leftLayer)
        LNode topRight = addNodeToLayer(rightLayer)
        LNode bottomRight = addNodeToLayer(rightLayer)

        LPort topRightPort = addPortOnSide(topRight, PortSide.WEST)
        LPort bottomLeftPort = addPortOnSide(bottomLeft, PortSide.EAST)
        addEdgeBetweenPorts(bottomLeftPort, topRightPort)

        LPort topLeftPort = addPortOnSide(topLeft, PortSide.EAST)
        addEdgeBetweenPorts(topLeftPort, topRightPort)

        eastWestEdgeFromTo(bottomLeft, bottomRight)

        
        return graph
    

    """
     * <pre>
     * *  *
     *  \/
     *  /\
     * *--*<- Into same port
     * </pre>
     *
     * .
     *
     * @return Graph of the form above.
     """
    def twoEdgesIntoSamePortResolvesCrossingWhenSwitched(self):
        Layer leftLayer = makeLayer(graph)
        Layer rightLayer = makeLayer(graph)

        LNode topLeft = addNodeToLayer(leftLayer)
        LNode bottomLeft = addNodeToLayer(leftLayer)
        LNode topRight = addNodeToLayer(rightLayer)
        LNode bottomRight = addNodeToLayer(rightLayer)

        LPort topLeftPort = addPortOnSide(topLeft, PortSide.EAST)
        LPort bottomLeftPort = addPortOnSide(bottomLeft, PortSide.EAST)
        LPort bottomRightPort = addPortOnSide(bottomRight, PortSide.WEST)

        addEdgeBetweenPorts(topLeftPort, bottomRightPort)
        addEdgeBetweenPorts(bottomLeftPort, bottomRightPort)

        eastWestEdgeFromTo(bottomLeft, topRight)

        
        return graph
    

    """
     * <pre>
     * *---* <- into same port
     *   /
     *  /
     * *---*
     * ^
     * |
     * Two edges into same port.
     * </pre>
     *
     * @return Graph of the form above.
     """
    def twoEdgesIntoSamePortFromEastWithFixedPortOrder(self):
        Layer leftLayer = makeLayer(graph)
        Layer rightLayer = makeLayer(graph)

        LNode topLeft = addNodeToLayer(leftLayer)
        LNode bottomLeft = addNodeToLayer(leftLayer)
        LNode topRight = addNodeToLayer(rightLayer)
        LNode bottomRight = addNodeToLayer(rightLayer)

        setFixedOrderConstraint(bottomLeft)
        setFixedOrderConstraint(topRight)

        LPort topLeftPort = addPortOnSide(topLeft, PortSide.EAST)
        LPort bottomLeftPort = addPortOnSide(bottomLeft, PortSide.EAST)
        LPort topRightPort = addPortOnSide(topRight, PortSide.WEST)
        LPort bottomRightPort = addPortOnSide(bottomRight, PortSide.WEST)

        addEdgeBetweenPorts(bottomLeftPort, bottomRightPort)
        addEdgeBetweenPorts(bottomLeftPort, topRightPort)
        addEdgeBetweenPorts(topLeftPort, topRightPort)

        
        return graph
    

    """
     * Return nodes as 2d array.
     * @param g
     * @return
     """
    public LNode[][] getCurrentOrder(final LGraph g):
        LNode[][] nodeOrder = new LNode[g.getLayers().size()][]
        List<Layer> layers = g.getLayers()
        for (int i = 0 i < layers.size() i++):
            Layer layer = layers.get(i)
            List<LNode> nodes = layer.getNodes()
            nodeOrder[i] = new LNode[nodes.size()]
            for (int j = 0 j < nodes.size() j++):
                nodeOrder[i][j] = nodes.get(j)
            
        
        return nodeOrder
    

    // CHECKSTYLEOFF Javadoc

    def setAsNorthSouthNode(node: LNode):
        node.setType(NodeType.NORTH_SOUTH_PORT)
    

    def addNorthSouthEdge(final PortSide side, node: LNodeWithNSPorts, final LNode northSouthDummy,
            node: LNodeWithEastWestPorts, final boolean nodeWithEastWestPortsIsOrigin):
        boolean normalNodeEastOfNsPortNode = nodeWithEastWestPorts.getLayer().getIndex() < nodeWithNSPorts.getLayer()
                .getIndex()
        PortSide direction = normalNodeEastOfNsPortNode ? PortSide.WEST : PortSide.EAST

        PortSide targetNodePortSide = direction.opposed()
        LPort normalNodePort = addPortOnSide(nodeWithEastWestPorts, targetNodePortSide)

        LPort dummyNodePort = addPortOnSide(northSouthDummy, direction)

        if (nodeWithEastWestPortsIsOrigin):
            addEdgeBetweenPorts(normalNodePort, dummyNodePort)
         else {
            addEdgeBetweenPorts(dummyNodePort, normalNodePort)
        

        northSouthDummy.setProperty(InternalProperties.IN_LAYER_LAYOUT_UNIT, nodeWithNSPorts)
        northSouthDummy.setProperty(InternalProperties.ORIGIN, nodeWithNSPorts)

        setAsNorthSouthNode(northSouthDummy)

        LPort originPort = addPortOnSide(nodeWithNSPorts, side)
        dummyNodePort.setProperty(InternalProperties.ORIGIN, originPort)
        originPort.setProperty(InternalProperties.PORT_DUMMY, northSouthDummy)

        List<LNode> baryAssoc = Lists.newArrayList(northSouthDummy)

        List<LNode> otherBaryAssocs = nodeWithNSPorts.getProperty(InternalProperties.BARYCENTER_ASSOCIATES)
        if (otherBaryAssocs is None):
            nodeWithNSPorts.setProperty(InternalProperties.BARYCENTER_ASSOCIATES, baryAssoc)
         else {
            otherBaryAssocs.addAll(baryAssoc)
        

        if (side == PortSide.NORTH):
            northSouthDummy.getProperty(InternalProperties.IN_LAYER_SUCCESSOR_CONSTRAINTS).add(nodeWithNSPorts)
         else {
            nodeWithNSPorts.getProperty(InternalProperties.IN_LAYER_SUCCESSOR_CONSTRAINTS).add(northSouthDummy)
        
    

    def setInLayerOrderConstraint(final LNode thisNode, final LNode beforeThisNode):
        List<LNode> scndNodeAsList = Lists.newArrayList(beforeThisNode)
        thisNode.setProperty(InternalProperties.IN_LAYER_SUCCESSOR_CONSTRAINTS, scndNodeAsList)
    

    def setAsLongEdgeDummy(node: LNode):
        node.setType(NodeType.LONG_EDGE)
        node.setProperty(InternalProperties.IN_LAYER_LAYOUT_UNIT, null)
    

    def setPortOrderFixed(node: LNode):
        node.setProperty(LayeredOptions.PORT_CONSTRAINTS, PortConstraints.FIXED_ORDER)
        node.getGraph().getProperty(InternalProperties.GRAPH_PROPERTIES).add(GraphProperties.NON_FREE_PORTS)
    

    public Layer[] makeLayers(final int amount):
        return makeLayers(amount, graph)
    

    public Layer[] makeLayers(final int amount, final LGraph g):
        Layer[] layers = new Layer[amount]
        for (int i = 0 i < layers.length i++):
            layers[i] = makeLayer(g)
        
        return layers
    

    public MapPropertyHolder setFixedOrderConstraint(node: LNode):
        return node.setProperty(LayeredOptions.PORT_CONSTRAINTS, PortConstraints.FIXED_ORDER)
    

    def setFixedOrderConstraint(final LNode[] nodes):
        for (LNode n : nodes):
            setFixedOrderConstraint(n)
        
    

    def addInLayerEdge(node: LNodeOne, node: LNodeTwo, final PortSide portSide):
        LPort portOne = addPortOnSide(nodeOne, portSide)
        LPort portTwo = addPortOnSide(nodeTwo, portSide)
        addEdgeBetweenPorts(portOne, portTwo)
    

    def addInLayerEdge(node: LNodeOne, final LPort portTwo, final PortSide portSide):
        LPort portOne = addPortOnSide(nodeOne, portSide)
        addEdgeBetweenPorts(portOne, portTwo)
    

    def addInLayerEdge(final LPort portOne, node: LNodeTwo):
        PortSide portSide = portOne.getSide()
        LPort portTwo = addPortOnSide(nodeTwo, portSide)
        addEdgeBetweenPorts(portOne, portTwo)
    

    public LNode[] addNodesToLayer(final int amountOfNodes, final Layer leftLayer):
        LNode[] nodes = new LNode[amountOfNodes]
        for (int j = 0 j < amountOfNodes j++):
            nodes[j] = addNodeToLayer(leftLayer)
        
        return nodes
    

    protected Layer makeLayer(self):
        return makeLayer(graph)
    

    public Layer makeLayer(final LGraph g):
        List<Layer> layers = g.getLayers()
        Layer layer = new Layer(g)
        layers.add(layer)
        return layer
    

    public LNode addNodeToLayer(final Layer layer):
        LNode node = new LNode(layer.getGraph())
        node.setType(NodeType.NORMAL)
        node.setProperty(InternalProperties.IN_LAYER_LAYOUT_UNIT, node)
        node.setLayer(layer)
        node.id = nodeId++
        return node
    

    def eastWestEdgeFromTo(final LNode left, final LNode right):
        LPort leftPort = addPortOnSide(left, PortSide.EAST)
        LPort rightPort = addPortOnSide(right, PortSide.WEST)
        addEdgeBetweenPorts(leftPort, rightPort)
    

    def addEdgeBetweenPorts(final LPort from, final LPort to):
        LEdge edge = new LEdge()
        edge.setSource(from)
        edge.setTarget(to)
        edge.id = edgeId++
    

    """
     * Sets port constraints to fixed!
     *
     * @param node
     * @param portSide
     * @return
     """
    public LPort addPortOnSide(node: LNode, final PortSide portSide):
        LPort port = addPortTo(node)
        port.setSide(portSide)
        if (!node.getProperty(LayeredOptions.PORT_CONSTRAINTS).isSideFixed()):
            node.setProperty(LayeredOptions.PORT_CONSTRAINTS, PortConstraints.FIXED_SIDE)
        
        return port
    

    public LPort[] addPortsOnSide(final int n, node: LNode, final PortSide portSide):
        LPort[] ps = new LPort[n]
        for (int i = 0 i < ps.length i++):
            ps[i] = addPortOnSide(node, portSide)
        
        return ps
    

    private LPort addPortTo(node: LNode):
        LPort port = new LPort()
        port.setNode(node)
        port.id = portId++
        return port
    

    """
     * <pre>
     *     ____
     *     |  |
     * ----0  | <--- two edges into one port
     * | / |  |
     * | +-0  |
     * |/| |__|
     * ||\
     * ||  *
     * | \
     * ----*
     * </pre>
     *
     * Port order not fixed.
     *
     * @return Graph of the form above.
     """
    def multipleEdgesIntoOnePortAndFreePortOrder(self):
        LNode[] nodes = addNodesToLayer(3, makeLayer(graph))
        addInLayerEdge(nodes[0], nodes[2], PortSide.WEST)
        LPort portUpperNode = addPortOnSide(nodes[0], PortSide.WEST)
        addEdgeBetweenPorts(portUpperNode, addPortOnSide(nodes[2], PortSide.WEST))
        addEdgeBetweenPorts(portUpperNode, addPortOnSide(nodes[1], PortSide.WEST))
        
        return graph
    

    """
     * <pre>
     * ___
     * | |\    *
     * | |\\  /
     * |_|-++-+*
     *     || \
     *     ====*
     * </pre>
     *
     * left Node has fixed Port Order.
     *
     * @return Graph of the form above.
     """
    def getOnlyCorrectlyImprovedByBestOfForwardAndBackwardSweepsInSingleLayer(self):
        LNode leftNode = addNodeToLayer(makeLayer(graph))
        setFixedOrderConstraint(leftNode)
        LNode[] rightNodes = addNodesToLayer(3, makeLayer(graph))
        eastWestEdgeFromTo(leftNode, rightNodes[2])
        eastWestEdgeFromTo(leftNode, rightNodes[2])
        eastWestEdgeFromTo(leftNode, rightNodes[1])
        addInLayerEdge(rightNodes[0], rightNodes[2], PortSide.WEST)
        
        return graph
    

    protected <T> List<T> getListCopyInIndexOrder(final List<T> li, final int... is):
        List<T> list = new ArrayList<>()
        for (int i : is):
            list.add(li.get(i))
        
        return list
    

    protected <T> T[] getArrayInIndexOrder(final T[] arr, final int... is):
        T[] copy = Arrays.copyOf(arr, arr.length)
        int j = 0
        for (int i : is):
            copy[j++] = arr[i]
        
        return copy
    

    protected <T> List<T> copyOfListSwitchingOrder(final int i, final int j, final List<T> list):
        List<T> listCopy = new ArrayList<T>(list)
        T first = listCopy.get(i)
        T second = listCopy.get(j)
        listCopy.set(i, second)
        listCopy.set(j, first)
        return listCopy
    

    def switchOrderInArray(final int i, final int j, final T[] arr):
        T[] copy = Arrays.copyOf(arr, arr.length)
        T first = arr[i]
        T snd = arr[j]
        copy[j] = first
        copy[i] = snd
        return copy
    

    def addExternalPortDummyNodeToLayer(final Layer layer, final LPort port):
        LNode node = addNodeToLayer(layer)
        node.setProperty(InternalProperties.ORIGIN, port)
        node.setType(NodeType.EXTERNAL_PORT)
        node.setProperty(InternalProperties.EXT_PORT_SIDE, port.getSide())
        port.setProperty(InternalProperties.PORT_DUMMY, node)
        port.setProperty(InternalProperties.INSIDE_CONNECTIONS, True)
        Set<GraphProperties> ps = node.getGraph().getProperty(InternalProperties.GRAPH_PROPERTIES)
        ps.add(GraphProperties.EXTERNAL_PORTS)
        return node
    

    def addExternalPortDummiesToLayer(final Layer layer, final LPort[] ports):
        nodes = new LNode[ports.length]
        PortSide side = ports[0].getSide()
        for (int i = 0 i < ports.length i++):
            int portIndex = side == PortSide.EAST ? i : ports.length - 1 - i
            nodes[i] = addExternalPortDummyNodeToLayer(layer, ports[portIndex])
        
        return nodes
    

    def nestedGraph(node: LNode):
        node.setProperty(InternalProperties.COMPOUND_NODE, True)
        LGraph nestedGraph = node.getProperty(InternalProperties.NESTED_LGRAPH)
        if (nestedGraph is None):
            nestedGraph = new LGraph()
            setUpGraph(nestedGraph)
            node.setProperty(InternalProperties.NESTED_LGRAPH, nestedGraph)
            nestedGraph.setProperty(InternalProperties.PARENT_LNODE, node)
        
        return nestedGraph
    

    def switchOrderOfNodesInLayer(final int nodeOne, final int nodeTwo, final Layer layer):
        List<LNode> nodes = layer.getNodes()
        LNode firstNode = nodes.get(nodeOne)
        LNode secondNode = nodes.get(nodeTwo)
        List<LNode> switchedList = new ArrayList<LNode>(nodes)
        switchedList.set(nodeOne, secondNode)
        switchedList.set(nodeTwo, firstNode)
        return switchedList
    

    protected List<LNode> copyOfNodesInLayer(final int layerIndex):
        return new ArrayList<LNode>(graph.getLayers().get(layerIndex).getNodes())
    

    protected List<LNode> copyOfSwitchOrderOfNodesInLayer(final int nodeOne, final int nodeTwo, final int layerIndex):
        List<LNode> layer = copyOfNodesInLayer(layerIndex)
        return getCopyWithSwitchedOrder(nodeOne, nodeTwo, layer)
    

    protected List<LNode> getCopyWithSwitchedOrder(final int nodeOne, final int nodeTwo, final List<LNode> layer):
        LNode firstNode = layer.get(nodeOne)
        LNode secondNode = layer.get(nodeTwo)
        List<LNode> switchedList = new ArrayList<LNode>(layer)
        switchedList.set(nodeOne, secondNode)
        switchedList.set(nodeTwo, firstNode)
        return switchedList
    

    protected void eastWestEdgesFromTo(final int numberOfNodes, final LNode left, final LNode right):
        for (int i = 0 i < numberOfNodes i++):
            eastWestEdgeFromTo(left, right)
        
    

    protected void eastWestEdgeFromTo(final LPort leftPort, final LNode rightNode):
        addEdgeBetweenPorts(leftPort, addPortOnSide(rightNode, PortSide.WEST))
    

    def copyPortsInIndexOrder(node: LNode, *indices):
        res = Lists.newArrayList()
        for i in indices:
            res.add(node.getPorts().get(i))
        
        return res
    

    protected void eastWestEdgeFromTo(final LNode left, final LPort right):
        addEdgeBetweenPorts(addPortOnSide(left, PortSide.EAST), right)
    

    public MockRandom getRandom(self):
        return random
    

    def setRandom(final MockRandom random):
        this.random = random
    

    protected <T> void setOnAllGraphs(final IProperty<T> prop, final T val, final LGraph graph):
        graph.setProperty(prop, val)
        for (LNode node : Iterables.concat(graph)):
            LGraph nestedGraph = node.getProperty(InternalProperties.NESTED_LGRAPH)
            if (nestedGraph is not None):
                setOnAllGraphs(prop, val, nestedGraph)
            
        
    

    
    
    
    