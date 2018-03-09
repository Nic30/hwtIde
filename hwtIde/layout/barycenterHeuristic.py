from random import Random
from typing import List
from layout.containers import LayoutNode

# 
# Represents the current barycenter state of a node.
# 
class BarycenterState():
    # The node this state holds data for.
    def __init__(self, node):
        self.node = node
        # The sum of the node weights. Each node weight is the sum of the weights of the ports the
        # node's ports are connected to. */
        self.summedWeight = 0.0
        # The number of ports relevant to the barycenter calculation.
        self.degree = None
        # This vertex' barycenter value. (summedWeight / degree) 
        self.barycenter = None
        # Whether the node group has been visited in some traversing algorithm. */
        self.visited = False

    def __repr__(self):
        return ("<BarycenterState [node:%r, summedWeight:%r, degree:%r, barycenter=%r, visited=%r]" % (
            self.node, self.summedWeight, self.degree, self.barycenter, self.visited))


def barycenterStateComparator(a, b):
    
    if a.barycenter is not None and :
        

class BarycenterHeuristic():
    def __init__(self, constraintResolver, random:Random, portDistributor):
    
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

    # the barycenter values of every node in the graph, indexed by layer.id and node.id.
    def minimizeCrossings(self, layer: List[LayoutNode], preOrdered: bool,
            randomize: bool, forward: bool):

        if randomize:
            # Randomize barycenters (we don't need to update the edge count in this case;
            # there are no edges of interest since we're only concerned with one layer)
            self.randomizeBarycenters(layer);
        else:
            # Calculate barycenters and assign barycenters to barycenterless node groups
            self.calculateBarycenters(layer, forward);
            self.fillInUnknownBarycenters(layer, preOrdered);

        if layer:
            # Sort the vertices according to their barycenters
            Collections.sort(layer, barycenterStateComparator);

            # Resolve ordering constraints
            constraintResolver.processConstraints(layer);
