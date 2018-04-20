from elkContainer.lNode import LNode
from elkContainer.lPort import LPort
from elkContainer.lEdge import LEdge


class ElkIdStore(dict):
    """
    :attention: First register nodes then register ports
        otherwise id will not be generated correctly
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.reverseDict = {v: k for k, v in self.items()}

    def register(self, obj):
        k = len(self)
        self[obj] = k
        self.reverseDict[k] = obj

    def registerNode(self, node: LNode):
        self.register(node)

    def registerPort(self, port: LPort):
        self.register(port)

    def registerEdge(self, edge: LEdge):
        self.register(edge)
