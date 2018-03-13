class BarycenterState():
    """
    :note: ported from ELK

    Represents the current barycenter state of a node.
    """

    def __init__(self, node):
        self.node = node
        # The sum of the node weights. Each node weight is the sum of the weights of the ports the
        # node's ports are connected to. */
        self.summedWeight = 0.0
        # The number of ports relevant to the barycenter calculation.
        self.degree = None
        # This vertex' barycenter value. (summedWeight / degree)
        self.barycenter = None
        # Whether the node group has been visited in some traversing algorithm.
        # */
        self.visited = False

    def __lt__(self, other):
        """
        Compare barycenter states
        """
        s1 = self
        s2 = other
        if s1.barycenter is not None and s2.barycenter is not None:
            return s1.barycenter < s2.barycenter
        elif s1.barycenter is not None:
            return True
        elif s2.barycenter is not None:
            return False
        return False

    def __repr__(self):
        return ("<BarycenterState [node:%r, summedWeight:%r, degree:%r, barycenter=%r, visited=%r]"
                % (self.node, self.summedWeight, self.degree, self.barycenter, self.visited))
