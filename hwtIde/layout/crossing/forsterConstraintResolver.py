from math import inf
from typing import List, Dict

from hwtIde.layout.crossing.barycenterState import BarycenterState
from layout.containers.lNode import LNode
from layout.containers.lGraph import LNodeLayer
from layout.containers.constants import NodeType


class ConstraintGroup():
    """
    :note: ported from ELK

    A node group contains one or more nodes. Node groups are used to model sets of nodes that are
    placed next to each other. A node group contains methods to calculate its barycenter value, to
    merge with another vertex and to generally do cool stuff.

    :ivar summedWeight: The sum of the node weights. Each node weight is the sum of the weights of the ports the
        node's ports are connected to
    :ivar degree: The number of ports relevant to the barycenter calculation.
    :ivar nodes:  List of nodes this vertex consists of.
    :ivar outgoingConstraints: List of outgoing constraints.
    :ivar incomingConstraints: List of incoming constraints.
    :ivar incomingConstraintsCount: The number of incoming constraints.
    """

    def __init__(self, states: Dict[LNode, BarycenterState]):
        """
        :param node: the node the vertex should contain
        """
        self.nodes = []
        self.summedWeight = 0.0
        self.degree = 0
        self.incomingConstraints = None
        self.outgoingConstraints = None
        self.states = states

    @classmethod
    def from_node(cls, states: Dict[LNode, BarycenterState], node: LNode):
        """
        :return: new instance of ConstraintGroup
        """
        self = cls(states)
        self.nodes.append(node)
        return self

    @classmethod
    def from_merge(cls, nodeGroup1: "ConstraintGroup", nodeGroup2: "ConstraintGroup") -> "ConstraintGroup":
        """
        Constructs a new vertex that is the concatenation of the given two vertices. The incoming
        constraints count is set to zero, while the list of successors are merged, updating the
        successors' incoming count appropriately if both vertices are predecessors. The new
        barycenter is derived from the barycenters of the given node groups.

        :param nodeGroup1: the first vertex
        :param nodeGroup2: the second vertex
        :return: new instance of ConstraintGroup
        """
        self = cls(nodeGroup1.states)
        # create a combined nodes array
        self.nodes.extend(nodeGroup1.nodes)
        self.nodes.extend(nodeGroup2.nodes)

        # Add constraints, taking care not to add any constraints to vertex1 or vertex2
        # and to decrement the incoming constraints count of those that are
        # successors to both
        if nodeGroup1.hasOutgoingConstraints():
            self.outgoingConstraints = list(nodeGroup1.outgoingConstraints)
            self.outgoingConstraints.remove(nodeGroup2)
            if nodeGroup2.hasOutgoingConstraints():
                for candidate in nodeGroup2.outgoingConstraints:
                    if candidate == nodeGroup1:
                        continue
                    elif candidate in self.outgoingConstraints:
                        # The candidate was in both vertices' successor list
                        candidate.incomingConstraintsCount -= 1
                    else:
                        self.outgoingConstraints.append(candidate)
        elif nodeGroup2.hasOutgoingConstraints():
            self.outgoingConstraints = list(nodeGroup2.outgoingConstraints)
            self.outgoingConstraints.remove(nodeGroup1)

        self.summedWeight = nodeGroup1.summedWeight + nodeGroup2.summedWeight
        self.degree = nodeGroup1.degree + nodeGroup2.degree

        if self.degree > 0:
            self.setBarycenter(self.summedWeight / self.degree)
        else:
            b1 = nodeGroup1.getBarycenter()
            b2 = nodeGroup2.getBarycenter()
            if b1 is not None and b2 is not None:
                self.setBarycenter((b1 + b2) / 2)
            elif b1 is not None:
                self.setBarycenter(b1)
            elif b2 is not None:
                self.setBarycenter(b2)
        return self

    def __repr__(self):
        sb = []
        for n in self.nodes:
            sb.append(repr(n))
            bc = self.getBarycenter(node=n)
            if bc is not None:
                sb.append("<")
                # [TODO] probably wrong, should be barycenter of selected node (now it is only of first)
                sb.append(repr(bc))
                sb.append(">")
        return '[%s]' % (", ".join(sb))

    def setBarycenter(self, barycenter: float) -> None:
        states = self.states
        for node in self.nodes:
            states[node].barycenter = barycenter

    def getBarycenter(self, node=None):
        """
        :return: barycenter of current constraint group.
        """
        if node is None:
            node = self.nodes[0]

        return self.states[node].barycenter

    def getOutgoingConstraints(self) -> List["ConstraintGroup"]:
        """
        Returns the list of outgoing constraints, creating it if not yet done before.

        :return: the outgoing constraints list of the node group
        """
        if self.outgoingConstraints is None:
            self.outgoingConstraints = []

        return self.outgoingConstraints

    def resetOutgoingConstraints(self) -> None:
        """
        Reset the list of outgoing constraints to None.
        """
        self.outgoingConstraints = None

    def hasOutgoingConstraints(self) -> bool:
        """
        Determine whether there are any outgoing constraints.

        :return: True if there are outgoing constraints
        """
        return self.outgoingConstraints is not None and len(self.outgoingConstraints) > 0

    def getIncomingConstraints(self):
        """
        Returns the list of incoming constraints, creating it if not yet done before.

        :return: the incoming constraints list of the node group
        """
        if self.incomingConstraints is None:
            self.incomingConstraints = []

        return self.incomingConstraints

    def resetIncomingConstraints(self):
        """
        Reset the list of incoming constraints to {@code null}.
        """
        self.incomingConstraints = None

    def hasIncomingConstraints(self):
        """
        Determine whether there are any incoming constraints.

        :return: True if there are incoming constraints
        """
        return self.incomingConstraints is not None and len(self.incomingConstraints) > 0

    def getNode(self) -> LNode:
        """
        Returns the contained node. This may only be used for node groups with exactly one node.

        :return: the contained node
        """
        assert len(self.nodes) == 1, self.nodes
        return self.nodes[0]


class ForsterConstraintResolver():
    """
    :note: ported from ELK

    Determines the node order of a given free layer. Uses heuristic methods to find
    an ordering that minimizes edge crossings between the given free layer and a neighboring layer
    with fixed node order. The barycenter heuristic is used here.

    :cvar BARYCENTER_EQUALITY_DELTA: Delta that two barycenters can differ by to still
        be considered equal.
    :ivar states: dict {LNode: BarycenterState}
    """
    BARYCENTER_EQUALITY_DELTA = 0.0001

    def __init__(self, layers: List[LNodeLayer]):
        states = self.states = {}
        cGroups = self.constraintGroups = {}
        units = self.layoutUnits = {}
        for layer in layers:
            for n in layer:
                states[n] = BarycenterState(n)
                cGroups[n] = ConstraintGroup.from_node(states, n)
                units[n] = [n, ]

    def processConstraints(self, nodes: List[LNode]):
        """
        :attention: nodes can be modified
        """
        groups = []
        for node in nodes:
            groups.append(self.constraintGroups[node])

        # Build the constraints graph
        self.buildConstraintsGraph(groups)

        # Find violated vertices
        while True:
            violatedConstraint = self.findViolatedConstraint(groups)
            if violatedConstraint is None:
                break

            self.handleViolatedConstraint(*violatedConstraint,
                                          groups)

        # Apply the determined order
        nodes.clear()
        states = self.states
        for group in groups:
            for node in group.nodes:
                nodes.append(node)
                states[node].barycenter = group.getBarycenter()

    def buildConstraintsGraph(self, groups):
        """
        Build the constraint graph for the given vertices. The constraint graph is created from
        the predefined <em>in-layer successor constraints</em> and the <em>layout units</em>.

        :param groups: the array of single-node vertices sorted by their barycenter values.
        """

        # Reset the constraint fields
        for group in groups:
            group.resetOutgoingConstraints()
            group.incomingConstraintsCount = 0

        # Iterate through the vertices, adding the necessary constraints
        lastNonDummyNode = None
        cgroups = self.constraintGroups
        layoutUnits = self.layoutUnits

        for group in groups:
            # at this stage all groups should consist of a single node
            node = group.getNode()
            # Add the constraints given by the vertex's node
            for successor in node.inLayerSuccessorConstraint:
                g = cgroups[successor]
                group.getOutgoingConstraints().append(g)
                g.incomingConstraintsCount += 1

            # Check if we're processing a a normal, none-dummy node
            if node.type == NodeType.NORMAL:
                # If we already processed another normal, non-dummy node, we need to add
                # constraints from all of that other node's layout unit's vertices to this
                # node's layout unit's vertices
                if lastNonDummyNode is not None:
                    for lastUnitNode in layoutUnits[lastNonDummyNode]:
                        for currentUnitNode in layoutUnits[node]:
                            g = cgroups[currentUnitNode]
                            cgroups[lastUnitNode].getOutgoingConstraints().append(g)
                            g.incomingConstraintsCount += 1

                lastNonDummyNode = node

    def findViolatedConstraint(self, groups):
        activeGroups = None

        # Iterate through the constrained vertices
        lastValue = -inf
        for group in groups:
            assert group.getBarycenter() is not None and group.getBarycenter() >= lastValue
            lastValue = group.getBarycenter()
            group.resetIncomingConstraints()

            # Find sources of the constraint graph to start the constraints
            # check
            if (group.hasOutgoingConstraints() and group.incomingConstraintsCount == 0):
                if activeGroups is None:
                    activeGroups = []
                activeGroups.append(group)

        # Iterate through the active node groups to find one with violated
        # constraints
        if activeGroups is not None:
            while activeGroups:
                group = activeGroups.pop(0)

                # See if we can find a violated constraint
                if group.hasIncomingConstraints():
                    for predecessor in group.getIncomingConstraints():
                        if (predecessor.getBarycenter() == group.getBarycenter()):
                            if groups.index(predecessor) > groups.index(group):
                                # The predecessor has equal barycenter, but
                                # higher index
                                return predecessor, group
                        elif predecessor.getBarycenter() > group.getBarycenter():
                            # The predecessor has greater barycenter and thus
                            # also higher index
                            return predecessor, group
                # No violated constraints add outgoing constraints to the
                # respective incoming list
                for successor in group.getOutgoingConstraints():
                    successorIncomingList = successor.getIncomingConstraints()
                    successorIncomingList.insert(0, group)

                    if successor.incomingConstraintsCount == len(successorIncomingList):
                        activeGroups.append(successor)
        # No violated constraints found
        return None

    def handleViolatedConstraint(self, firstNodeGroup: ConstraintGroup,
            secondNodeGroup: ConstraintGroup, nodeGroups: List[ConstraintGroup]):
        """
        Handles the case of a violated constraint. The node groups must be sorted by their
        barycenter values. After this method has finished, the list of node groups is smaller
        by one element, since two node groups have been unified, but the list is still correctly
        sorted by barycenter values.

        @param firstNodeGroup
                   the node group with violated outgoing constraint
        @param secondNodeGroup
                   the node group with violated incoming constraint
        @param nodeGroups
                   the list of vertices
        """

        # Create a new vertex from the two constrain-violating vertices this also
        # automatically calculates the new vertex's barycenter value
        newNodeGroup = ConstraintGroup.from_merge(firstNodeGroup, secondNodeGroup)
        assert (newNodeGroup.getBarycenter() + self.BARYCENTER_EQUALITY_DELTA 
                    >= secondNodeGroup.getBarycenter())
        assert (newNodeGroup.getBarycenter() - self.BARYCENTER_EQUALITY_DELTA 
                    <= firstNodeGroup.getBarycenter())

        # Iterate through the vertices. Remove the old vertices. Insert the new one
        # according to the barycenter value, thereby keeping the list sorted. Along
        # the way, constraint relationships will be updated
        nodeGroupIterator = iter(nodeGroups)
        alreadyInserted = False
        while True:
            nodeGroup = next(nodeGroupIterator)

            if (nodeGroup == firstNodeGroup or nodeGroup == secondNodeGroup):
                # Remove the two node groups with violated constraint from the list
                nodeGroupIterator.remove()
            elif (not alreadyInserted
                  and nodeGroup.getBarycenter() > newNodeGroup.getBarycenter()):
                # If we haven't inserted the new node group into the list already, do that now.
                # Note: we're not calling next() again. This means that during the next iteration,
                # we will again be looking at the current node group. But then, alreadyInserted will
                # be true and we can look at that node group's outgoing constraints.
                nodeGroupIterator.previous()
                nodeGroupIterator.add(newNodeGroup)

                alreadyInserted = True
            elif nodeGroup.hasOutgoingConstraints():
                # Check if the vertex has any constraints with the former two vertices
                firstNodeGroupConstraint = nodeGroup.getOutgoingConstraints()\
                        .remove(firstNodeGroup)
                secondNodeGroupConstraint = nodeGroup.getOutgoingConstraints()\
                        .remove(secondNodeGroup)

                if firstNodeGroupConstraint or secondNodeGroupConstraint:
                    nodeGroup.getOutgoingConstraints().add(newNodeGroup)
                    newNodeGroup.incomingConstraintsCount += 1

        # If we haven't inserted the new node group already, add it to the end
        if not alreadyInserted:
            nodeGroups.add(newNodeGroup)

