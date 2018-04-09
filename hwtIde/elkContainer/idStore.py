from elkContainer.lNode import LNode
from elkContainer.lPort import LPort


class ElkIdStore(dict):
    """
    :attention: First register nodes then register ports
        otherwise id will not be generated correctly
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.reverseDict = {v: k for k, v in self.items()}
        self.nodeCnt = 0
        self.portCnt = 0

    def registerNode(self, node: LNode):
        k = self.nodeCnt
        self[node] = k
        assert k not in self.reverseDict, (node, k)
        self.reverseDict[k] = node
        self.nodeCnt += 1

    def registerPort(self, port: LPort):
        k = self.nodeCnt + self.portCnt
        self[port] = k
        assert k not in self.reverseDict, (port, k)
        self.reverseDict[k] = port
        self.portCnt += 1
