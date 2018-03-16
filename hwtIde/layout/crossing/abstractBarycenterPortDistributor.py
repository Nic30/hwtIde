
"""
Calculates port ranks and distributes ports.
The <em>rank</em> of a port is a floating point number that represents its position
inside the containing layer. This depends on the node order of that layer and on the
port constraints of the nodes. Port ranks are used by {@link ICrossingMinimizationHeuristics
for calculating barycenter or median values for nodes. Furthermore, they are used in this
class for distributing the ports of nodes where the order of ports is not fixed,
which has to be done as the last step of each crossing minimization processor.
There are different ways to determine port ranks, therefore that is done in concrete subclasses.

Must be initialized using {@link IInitializable#init(List, LNode[][]).
"""
from math import inf

from layout.containers import PortType, LNode, PortSide, LPort, LNodeLayer


def hasNestedGraph(node):
    return node.nestedLgraph is not None


def isNotFirstLayer(length: int, currentIndex: int, isForwardSweep: bool):
    return currentIndex != 0 if isForwardSweep else currentIndex != length - 1


def portTypeFor(isForwardSweep: bool):
    return PortType.OUTPUT if isForwardSweep else PortType.INPUT


class AbstractBarycenterPortDistributor():
    """ port ranks array in which the results of ranks calculation are stored."""
    """
     * Constructs a port distributor for the given array of port ranks. 
     * All ports are required to be assigned ids in the range of the given array.
     *
     * @param numLayers
     *            the number of layers in the graph.
    """

    def __init__(self, graph):
        r = self.portRanks = {}
        self.minBarycenter = inf
        self.maxBarycenter = 0.0
        np = self.nodePositions = {}
        for i, la in enumerate(graph.layers):
            for node in la:
                np[node] = i
                for p in node.iterPorts():
                    r[p] = 0

        self.portBarycenter = {}
        self.inLayerPorts = {}

    # ######################################/
    # Port Rank Assignment

    def distributePortsWhileSweeping(self, nodeOrder, currentIndex: int, isForwardSweep: bool):
        self.updateNodePositions(nodeOrder, currentIndex)
        freeLayer = nodeOrder[currentIndex]
        side = PortSide.WEST if isForwardSweep else PortSide.EAST
        distributePorts = self.distributePorts

        if isNotFirstLayer(len(nodeOrder), currentIndex, isForwardSweep):

            fixedLayer = currentIndex - \
                1 if isForwardSweep else nodeOrder[currentIndex + 1]
            self.calculatePortRanks(fixedLayer, portTypeFor(isForwardSweep))
            for node in freeLayer:
                distributePorts(node, side)

            self.calculatePortRanks(freeLayer, portTypeFor(not isForwardSweep))
            for node in fixedLayer:
                if not hasNestedGraph(node):
                    distributePorts(node, side.opposed())
        else:
            for node in freeLayer:
                distributePorts(node, side)

        # Barycenter port distributor can not be used with always improving crossing minimization heuristics
        # which do not need to count.
        return False

    def calculatePortRanks_many(self, layer: LNodeLayer, portType: PortType):
        """
         * Determine ranks for all ports of specific type in the given layer.
         * The ranks are written to the {@link #getPortRanks() array.
         *
         * @param layer
         *            a layer as node array
         * @param portType
         *            the port type to consider
        """
        calculatePortRanks = self.calculatePortRanks
        consumedRank = 0
        assert isinstance(layer, LNodeLayer), layer
        for node in layer:
            consumedRank += calculatePortRanks(node, consumedRank, portType)

    def calculatePortRanks(self, node: LNode, rankSum: float, type: PortType):
        """
         * Assign port ranks for the input or output ports of the given node. If the node's port
         * constraints imply a fixed order, the ports are assumed to be pre-ordered in the usual way,
         * i.e. in clockwise order north - east - south - west.
         * The ranks are written to the {@link #getPortRanks() array.
         *
         * @param node
         *            a node
         * @param rankSum
         *            the sum of ranks of preceding nodes in the same layer
         * @param type
         *            the port type to consider
         * @return the rank consumed by the given node the following node's ranks start at
         *         {@code rankSum + consumedRank
         * @see {@link org.eclipse.alg.layered.intermediate.PortListSorter 
        """
        raise NotImplementedError("Implement on child class")

    # ######################################/
    # Port Distribution

    def distributePorts_side(self, node: LNode, side: PortSide):
        if not node.portConstraints.isOrderFixed():
            # distribute ports in sweep direction and on north south side of
            # node.
            self.distributePorts(node, node.getPorts(side))
            self.distributePorts(node, node.getPorts(PortSide.SOUTH))
            self.distributePorts(node, node.getPorts(PortSide.NORTH))
            # sort the ports by considering the side, type, and barycenter
            # values
            self.sortPorts(node)

    def distributePorts(self, node, ports):
        """
         * Distribute the ports of the given node by their sides, connected ports, and input or output
         * type.
         *
         * @param node
         *            node whose ports shall be sorted
        """
        self.inLayerPorts.clear()
        self.iteratePortsAndCollectInLayerPorts(node, ports)

        if self.inLayerPorts:
            self.calculateInLayerPortsBarycenterValues(node)

    def iteratePortsAndCollectInLayerPorts(self, node, ports):
        minBarycenter = 0.0
        maxBarycenter = 0.0

        # a float value large enough to ensure that barycenters of south ports
        # work fine
        absurdlyLargeFloat = 2 * len(node.getLayer()) + 1
        # calculate barycenter values for the ports of the node
        dealWithNorthSouthPorts = self.dealWithNorthSouthPorts
        continueOnPortIteration = False
        inLayerPorts = self.inLayerPorts
        portRanks = self.portRanks
        portBarycenter = self.portBarycenter

        for port in ports:
            northSouthPort = port.side == PortSide.NORTH or port.side == PortSide.SOUTH
            sum_ = 0

            if northSouthPort:
                # Find the dummy node created for the port
                portDummy = port.portDummy
                if (portDummy is None):
                    continue

                sum_ += dealWithNorthSouthPorts(absurdlyLargeFloat,
                                                port, portDummy)

            else:
                # add up all ranks of connected ports
                for outgoingEdge in port.getOutgoingEdges():
                    connectedPort = outgoingEdge.getTarget()
                    if connectedPort.getNode().getLayer() == node.getLayer():
                        inLayerPorts.add(port)
                        continueOnPortIteration = True
                        break
                    else:
                        # outgoing edges go to the subsequent layer and are
                        # seen clockwise
                        sum_ += portRanks[connectedPort]

                if continueOnPortIteration:
                    continueOnPortIteration = False
                    continue

                for incomingEdge in port.getIncomingEdges():
                    connectedPort = incomingEdge.src
                    if connectedPort.getNode().getLayer() == node.getLayer():
                        inLayerPorts.add(port)
                        continueOnPortIteration = True
                        break
                    else:
                        # incoming edges go to the preceding layer and are seen
                        # counter-clockwise
                        sum_ -= portRanks[connectedPort]

                if continueOnPortIteration:
                    continueOnPortIteration = False
                    continue

            if port.getDegree() > 0:
                portBarycenter[port] = sum_ / port.getDegree()
                minBarycenter = min(minBarycenter, portBarycenter[port])
                maxBarycenter = max(maxBarycenter, portBarycenter[port])
            elif northSouthPort:
                # For northern and southern ports, the sum directly corresponds to the
                # barycenter value to be used.
                portBarycenter[port] = sum_

    def calculateInLayerPortsBarycenterValues(self, node):
        # go through the list of in-layer ports and calculate their barycenter
        # values
        nodePositions = self.nodePositions
        nodeIndexInLayer = nodePositions[node] + 1
        layerSize = len(node.getLayer()) + 1
        minBarycenter = self.minBarycenter
        maxBarycenter = self.maxBarycenter
        portBarycenter = self.portBarycenter

        for inLayerPort in self.inLayerPorts:
            # add the indices of all connected in-layer ports
            sum_ = 0
            inLayerConnections = 0

            for connectedPort in inLayerPort.getConnectedPorts():
                if connectedPort.getNode().getLayer() == node.getLayer():
                    sum_ += nodePositions[connectedPort.getNode()] + 1
                    inLayerConnections += 1

            # The port's barycenter value is the mean index of connected nodes. If that
            # value is lower than the node's index, most in-layer edges point upwards, so we want
            # the port to be placed at the top of the side. If the value is higher than the
            # nodes's index, most in-layer edges point downwards, so we want the port to be
            # placed at the bottom of the side.
            barycenter = sum_ / inLayerConnections

            portSide = inLayerPort.side
            if portSide == PortSide.EAST:
                if barycenter < nodeIndexInLayer:
                    # take a low value in order to have the port above
                    portBarycenter[inLayerPort] = minBarycenter - barycenter
                else:
                    # take a high value in order to have the port below
                    portBarycenter[inLayerPort] = maxBarycenter + \
                        (layerSize - barycenter)

            elif portSide == PortSide.WEST:
                if barycenter < nodeIndexInLayer:
                    # take a high value in order to have the port above
                    portBarycenter[inLayerPort] = maxBarycenter + barycenter
                else:
                    # take a low value in order to have the port below
                    portBarycenter[inLayerPort] = minBarycenter - \
                        (layerSize - barycenter)

    def dealWithNorthSouthPorts(self, absurdlyLargeFloat: float,
                                port: LPort, portDummy: LNode):
        # Find out if it's an input port, an output port, or both
        input_ = False
        output = False
        for portDummyPort in portDummy.getPorts():
            if portDummyPort.origin == port:
                if portDummyPort.getOutgoingEdges():
                    output = True
                elif portDummyPort.getIncomingEdges():
                    input_ = True

        sum_ = 0.0
        if input_ and input_ ^ output:
            # It's an input port the index of its dummy node is its inverted sortkey
            # (for southern input ports, the key must be larger than the ones
            # assigned to output ports or inputandoutput ports)
            if port.side == PortSide.NORTH:
                sum_ = -self.nodePositions[portDummy]
            else:
                sum_ = absurdlyLargeFloat - self.nodePositions[portDummy]
        elif output and input_ ^ output:
            # It's an output port the index of its dummy node is its sort key
            # (for northern output ports, the key must be larger than the ones assigned
            # to input ports or inputandoutput ports, which are negative and 0,
            # respectively)
            sum_ = self.nodePositions[portDummy] + 1.0
        elif input_ and output:
            # It's both, an input and an output port it must sit between input and
            # output ports
            # North: input ports < 0.0, output ports > 0.0
            # South: input ports > FLOAT_MAX / 2, output ports near zero
            if port.side == PortSide.NORTH:
                sum_ = 0.0
            else:
                sum_ = absurdlyLargeFloat / 2

        return sum_

    def updateNodePositions(self, nodeOrder, currentIndex: int):
        layer = nodeOrder[currentIndex]
        nodePositions = self.nodePositions
        for i, node in enumerate(layer):
            nodePositions[node] = i

    def sortPorts(self, node):
        """
        Sort the ports of a node using the given relative position values.
        These values are interpreted as a hint for the clockwise order of ports.
 
        @param node: a node
        """
        portBarycenter = self.portBarycenter
        for side in node.iterSides():
            side.sort(key=lambda p: portBarycenter[p])
