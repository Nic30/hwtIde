from hwt.pyUtils.arrayQuery import flatten
from layout.containers import Layout, LNode, NodeType


class SweepCopy():
    """
    :note: Ported from ELK.

    Stores node and port order for a sweep.
    """

    def __init__(self, nodeOrderIn):
        # Saves a copy of the node order.
        self.nodeOrder = []
        # Saves a copy of the orders of the ports on each node, because they
        # are reordered in each sweep. */
        self.portOrders = {}

    @classmethod
    def from_order(cls, nodeOrderIn):
        # Copies on construction.
        self = cls()
        self.nodeOrder = [list(layer) for layer in nodeOrderIn]
        po = self.portOrders
        for node in flatten(nodeOrderIn, level=1):
            po[node] = list(node.iterPorts())

    def transferNodeAndPortOrdersToGraph(self, lGraph: Layout):
        """
        the 'NORTH_OR_SOUTH_PORT' option allows the crossing minimizer to decide
        the side a corresponding dummy node is placed on in order to reduce the number of crossings
        as a consequence the configured port side may not be valid anymore and has to be corrected
        """
        northSouthPortDummies = []
        #updatePortOrder = set()

        # iterate the layers
        layers = lGraph.layers
        for i, nodes in enumerate(layers):
            northSouthPortDummies.clear()

            # iterate and order the nodes within the layer
            for j, node, in enumerate(nodes):
                # use the id field to remember the order within the layer
                if node.getType() == NodeType.NORTH_SOUTH_PORT:
                    northSouthPortDummies.append(node)

                nodes[j] = node

                # order ports as computed
                # node.getPorts().clear()
                # node.getPorts().extend(portOrders.get(i).get(j))

        # assert that the port side is set properly
        # for dummy in northSouthPortDummies:
        #    origin = self.assertCorrectPortSides(dummy)
        #    updatePortOrder.add(origin)
        #    updatePortOrder.add(dummy)
        #
        # since the side of certain ports may have changed at this point,
        # the list of ports must be re-sorted (see PortListSorter)
        # and the port list views must be re-cached.
        # for node in updatePortOrder:
        #    Collections.sort(node.getPorts(), PortListSorter.DEFAULT_SORT_COMPARATOR)
        #    node.cachePortSides()

    # def assertCorrectPortSides(self, dummy: LNode) -> LNode:
    #    """
    #    Corrects the {@link PortSide} of dummy's origin.
    #
    #    :return: The {@link LNode} ('origin') whose port {@code dummy} represents.
    #    """
    #    assert dummy.getType() == NodeType.NORTH_SOUTH_PORT
    #
    #    origin = dummy.in_layer_layout_unit
    #
    #    # a north south port dummy has exactly one port
    #    dummyPorts = dummy.getPorts()
    #    dummyPort = dummyPorts[0]
    #
    #    # find the corresponding port on the regular node
    #    for port in origin.iterPorts():
    #        if (port.equals(dummyPort.getProperty(InternalProperties.ORIGIN))):
    #            # switch the port's side if necessary
    #            if ((port.getSide() == PortSide.NORTH) and (dummy.id > origin.id)):
    #                port.setSide(PortSide.SOUTH)
    #            elif ((port.getSide() == PortSide.SOUTH) and (origin.id > dummy.id)):
    #                port.setSide(PortSide.NORTH)
    #            break
    #    return origin
