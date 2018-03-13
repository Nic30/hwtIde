from itertools import islice
from random import Random
from typing import List

from hwtIde.layout.containers import LNode, PortType, NodeType
from hwtIde.layout.crossing.forsterConstraintResolver import ForsterConstraintResolver


def changeIndex(dir_: bool):
    return 1 if dir_ else -1


def portTypeFor(direction: bool):
    return PortType.OUTPUT if direction else PortType.INPUT


def isExternalPortDummy(firstNode: LNode):
    return firstNode.type == NodeType.EXTERNAL_PORT


def startIndex(dir_: bool, size: int) -> int:
    if dir_:
        return 0
    else:
        return max(0, size - 1)


def isFirstLayer(nodeOrder: List[List[LNode]], currentIndex: int,
                 forwardSweep: bool) -> bool:
    return currentIndex == startIndex(forwardSweep, len(nodeOrder))


class BarycenterHeuristic():
    RANDOM_AMOUNT = 0.07
    """
    :note: Ported from ELK.
    :ivar states: dict {LNode: BarycenterState}
    """

    def __init__(self, constraintResolver: ForsterConstraintResolver, random: Random, portDistributor):
        """
        Barycenter heuristic for crossing minimization.

        :param constraintResolver: the constraint resolver
        :param random: the random number generator
        :param portDistributor: calculates the port ranks for the barycenter heuristic.
        :param graph: current node order
        """
        self.random = random
        # the constraint resolver for ordering constraints.
        self.constraintResolver = constraintResolver
        # The Barycenter PortDistributor is used to ask for the port ranks.*/
        self.portDistributor = portDistributor
        self.states = constraintResolver.states

    # the barycenter values of every node in the graph, indexed by layer.id
    # and node.id.
    def minimizeCrossingsInLayer(self, layer: List[LNode], preOrdered: bool,
                                 randomize: bool, forward: bool):
        if randomize:
            # Randomize barycenters (we don't need to update the edge count in this case
            # there are no edges of interest since we're only concerned with
            # one layer)
            self.randomizeBarycenters(layer)
        else:
            # Calculate barycenters and assign barycenters to barycenterless
            # node groups
            self.calculateBarycenters(layer, forward)
            self.fillInUnknownBarycenters(layer, preOrdered)

        if layer:
            # Sort the vertices according to their barycenters
            states = self.states
            layer.sort(key=lambda n: states[n])

            # Resolve ordering constraints
            self.constraintResolver.processConstraints(layer)

    def minimizeCrossings(self, order: List[List[LNode]], freeLayerIndex: int,
                          forwardSweep: bool, isFirstSweep: bool) -> bool:
        if (not isFirstLayer(order, freeLayerIndex, forwardSweep)):
            fixedLayer = order[freeLayerIndex - changeIndex(forwardSweep)]
            self.portDistributor.calculatePortRanks(
                fixedLayer, portTypeFor(forwardSweep))

        firstNodeInLayer = order[freeLayerIndex][0]
        preOrdered = not isFirstSweep or isExternalPortDummy(firstNodeInLayer)

        layer = list(order[freeLayerIndex])
        self.minimizeCrossingsInLayer(layer, preOrdered, False, forwardSweep)
        # apply the new ordering
        order[freeLayerIndex] = layer

        return False  # Does not always improve.

    def randomizeBarycenters(self, nodes):
        """
        Randomize the order of nodes for the given layer.

        :param nodes: a layer
        """
        states = self.states
        random = self.random.random
        for node in nodes:
            # Set barycenters only for nodeGroups containing a single node.
            st = states[node]
            st.summedWeight = st.barycenter = random()
            st.degree = 1

    def setFirstLayerOrder(self, order: List[List[LNode]], isForwardSweep: bool):
        _startIndex = startIndex(isForwardSweep, len(order))
        nodes = list(order[_startIndex])
        self.minimizeCrossingsInLayer(nodes, False, True, isForwardSweep)
        order[_startIndex] = nodes

        return False  # Does not always improve

    def fillInUnknownBarycenters(self, nodes, preOrdered):
        """
        Try to find appropriate barycenter values for node groups whose barycenter is undefined.

        :param nodes: the nodeGroups to fill in barycenters for.
        :param preOrdered: whether the nodeGroups have been ordered in a previous run.
        """
        # Determine placements for nodes with undefined barycenter value
        states = self.states
        if preOrdered:
            lastValue = -1

            for i, node in enumerate(node):
                st = states[node]
                value = st.barycenter

                if value is None:
                    # The barycenter is undefined - take the center of the previous value
                    # and the next defined value in the list
                    nextValue = lastValue + 1

                    for node2 in islice(node, i + 1, None):
                        x = states[node2].barycenter
                        if x is not None:
                            nextValue = x
                            break

                    value = (lastValue + nextValue) / 2
                    st.barycenter = value
                    st.summedWeight = value
                    st.degree = 1

                lastValue = value
        else:
            # No previous ordering - determine random placement for new nodes
            maxBary = 0.0
            for node in nodes:
                if states[node].barycenter is not None:
                    maxBary = max(maxBary, states[node].barycenter)

            maxBary += 2
            random = self.random.random
            for node in nodes:
                st = states[node]
                if st.barycenter is None:
                    value = random() * maxBary - 1
                    st.barycenter = value
                    st.summedWeight = value
                    st.degree = 1

    def calculateBarycenters(self, nodes: List[LNode], forward: bool):
        """
        Calculate the barycenters of the given node groups.

        :param nodes: the nodes
        :param forward: True if the current sweep moves forward
        """
        # Set all visited flags to false
        states = self.states
        calculateBarycenter = self.calculateBarycenter

        for node in nodes:
            states[node].visited = False

        for node in nodes:
            # Calculate the node groups's new barycenter (may be null)
            calculateBarycenter(node, forward)

    def calculateBarycenter(self, node, forward: bool):
        """
        Calculate the barycenter of the given single-node node group. This method is able to handle
        in-layer edges, but it may give incorrect results if the in-layer edges form a cycle.
        However, such cases do not occur in the present implementation.

        :param node: a node group consisting of a single node
        :param forward: True if the current sweep moves forward
        :param portPos: position array
        :return: a pair containing the summed port positions of the connected ports as the first,
                and the number of connected edges as the second entry.
        """

        # Check if the node group's barycenter was already computed
        st = self.states[node]
        if st.visited:
            return
        else:
            st.visited = True

        st.degree = 0
        st.summedWeight = 0.0
        st.barycenter = None
        states = self.states
        calculateBarycenter = self.calculateBarycenter

        for freePort in node.iterPorts():
            if forward:
                portIterable = freePort.getPredecessorPorts()
            else:
                portIterable = freePort.getSuccessorPorts()

            for fixedPort in portIterable:
                # If the node the fixed port belongs to is part of the free layer (thus, if
                # we have an in-layer edge), use that node's barycenter
                # calculation instead
                fixedNode = fixedPort.getNode()

                if fixedNode.layerIndex == node.layerIndex:
                    # Self-loops are ignored
                    if fixedNode is not node:
                        # Find the fixed node's node group and calculate its
                        # barycenter
                        calculateBarycenter(fixedNode, forward)

                        # Update this node group's values
                        fst = states[fixedNode]
                        st.degree += fst.degree
                        st.summedWeight += fst.summedWeight
                else:
                    st.summedWeight += fixedPort.rank
                    st.degree += 1

        # Iterate over the node's barycenter associates
        barycenterAssociates = node.barycenterAssociates
        if barycenterAssociates is not None:
            for associate in barycenterAssociates:
                # Make sure the associate is in the same layer as this node
                if node.layerIndex == associate.layerIndex:
                    # Find the associate's node group and calculate its
                    # barycenter
                    calculateBarycenter(associate, forward)

                    # Update this vertex's values
                    ast = states[associate]
                    st.degree += ast.degree
                    st.summedWeight += ast.summedWeight

        if st.degree > 0:
            # add a small random perturbation in order to increase diversity of
            # solutions
            st.summedWeight += (self.random.random() * self.RANDOM_AMOUNT
                                - self.RANDOM_AMOUNT / 2)
            st.barycenter = st.summedWeight / st.degree
