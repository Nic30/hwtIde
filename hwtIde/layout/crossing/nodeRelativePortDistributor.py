from layout.containers.constants import PortType, PortSide
from layout.containers.lNode import LNode
from layout.crossing.abstractBarycenterPortDistributor import AbstractBarycenterPortDistributor


class NodeRelativePortDistributor(AbstractBarycenterPortDistributor):

    def calculatePortRanks(self, node: LNode, rankSum: float, typ: PortType):
        portRanks = self.portRanks

        if typ == PortType.INPUT:
            # Count the number of input ports, and additionally the north-side input ports
            inputCount = 0
            northInputCount = 0
            for port in node.iterPorts():
                if port.incomingEdges:
                    inputCount += 1
                    if port.side == PortSide.NORTH:
                        northInputCount += 1

            # Assign port ranks in the order north - west - south - east
            incr = 1.0 / (inputCount + 1)
            northPos = rankSum + northInputCount * incr
            restPos = rankSum + 1 - incr
            for port in node.getPorts(PortType.INPUT):
                if port.side == PortSide.NORTH:
                    portRanks[port] = northPos
                    northPos -= incr
                else:
                    portRanks[port] = restPos
                    restPos -= incr

        elif typ == PortType.OUTPUT:
            # Count the number of output ports
            outputCount = 0
            for port in node.iterPorts():
                if port.outgoingEdges:
                    outputCount += 1

            # Iterate output ports in their natural order, that is north - east - south - west
            incr = 1.0 / (outputCount + 1)
            pos = rankSum + incr
            for port in node.getPorts(PortType.OUTPUT):
                portRanks[port] = pos
                pos += incr

        else:
            # this means illegal input to the method
            raise ValueError("Port type is undefined", typ)

        # the consumed rank is always 1
        return 1
