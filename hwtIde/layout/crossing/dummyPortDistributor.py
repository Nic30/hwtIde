from layout.containers.lGraph import LNodeLayer
from layout.containers.constants import PortType


class DummyPortDistributor():

    def __init__(self, layers: LNodeLayer):
        pr = self.portRanks = {}
        for la in layers:
            for n in la:
                for i, p in enumerate(n.iterPorts()):
                    pr[p] = i

    def distributePortsWhileSweeping(self, order: LNodeLayer,
                                     freeLayerIndex: int, isForwardSweep: bool):
        """
        Distribute ports in one layer. To be used in the context of layer sweep.

        :param order: the current order of the nodes
        :param freeLayerIndex: the index of the layer the node is in
        :param isForwardSweep: whether we are sweeping forward or not.
        """
        return False

    def calculatePortRanks(self, layer: LNodeLayer, portType: PortType):
        """
        Determine ranks for all ports of specific type in the given layer.
        The ranks are written to the {@link #getPortRanks()} array.

        :param layer: a layer as node array
        :param portType: the port type to consider
        """
        pass

    def calculatePortRanks_many(self, layer: LNodeLayer, portType: PortType):
        pass
