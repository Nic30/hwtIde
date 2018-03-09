from layout.containers import LayoutExternalPort, LayoutNode
from hwt.hdl.constants import INTF_DIRECTION


class GreedyCycleBreaker():
    def initDegrees(self):
        add_unresolved = self.unresolved.add
        add_sink = self.sinks.add
        add_source = self.sources.add
        for n in self.nodes:
            n.initPortDegrees()
            if isinstance(n, LayoutExternalPort):
                if n.indeg:
                    add_sink(n)
                else:
                    add_source(n)
            else:
                add_unresolved(n)

    def process(self, graph):
        # list of sink nodes.
        sinks = self.sinks = set()
        # list of source nodes
        sources = self.sources = set()
        unresolved = self.unresolved = set()
        # mark for the nodes, inducing an ordering of the nodes.
        nodes = self.nodes = graph.getLayerlessNodes()

        self.initDegrees()

        # next rank values used for sinks and sources (from right and from
        # left)
        nextRight = -1
        nextLeft = 1

        # assign marks to all nodes
        while sinks or sources or unresolved:
            # sinks are put to the right --> assign negative rank, which is
            # later shifted to positive
            while sinks:
                sink = sinks.pop()
                sink.mark = nextRight
                nextRight -= 1
                self.updateNeighbors(sink)

            # sources are put to the left --> assign positive rank
            while sources:
                source = sources.pop()
                source.mark = nextLeft
                nextLeft += 1
                self.updateNeighbors(source)

            # while there are unprocessed nodes left that are neither sinks nor
            # sources...
            if not sinks and not sources and unresolved:
                # find the set of unprocessed node (=> mark == 0), with the largest out flow
                # randomly select a node from the ones with maximal outflow and
                # put it left
                maxNode = max(
                    unresolved, key=lambda node: node.outdeg - node.indeg)
                maxNode.mark = nextLeft
                unresolved.remove(maxNode)
                nextLeft += 1
                self.updateNeighbors(maxNode)

        # shift negative ranks to positive; this applies to sinks of the graph
        shiftBase = len(nodes) + 1
        for n in nodes:
            if n.mark < 0:
                n.mark += shiftBase

        # reverse edges that point left
        for node in nodes:
            # look at the node's outgoing edges
            for port in node.iterPorts():
                if port.direction == INTF_DIRECTION.MASTER:
                    for edge in port.connectedEdges:
                        if node.mark > edge.dstNode.mark:
                            edge.reverse()

    def updateNeighbors(self, node: LayoutNode):
        """
        Updates indegree and outdegree values of the neighbors of the given node,
        simulating its removal from the graph. the sources and sinks lists are
        also updated.

        :param node: node for which neighbors are updated
        """
        for p in node.iterPorts():
            isOutput = p.direction == INTF_DIRECTION.MASTER
            for e in p.connectedEdges:
                if isOutput:
                    other = e.dstNode
                else:
                    other = e.srcNode

                if not e.isSelfLoop() and other.mark == 0:
                    if isOutput:
                        other.outdeg -= 1
                        if other.outdeg <= 0 and other.indeg > 0:
                            self.unresolved.discard(other)
                            self.sources.add(other)
                    else:
                        other.indeg -= 1
                        if other.indeg <= 0 and other.outdeg > 0:
                            self.unresolved.discard(other)
                            self.sinks.add(other)
