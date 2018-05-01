
class LEdge():
    """
    Edge in layout graph

    :ivar name: name of this edge (label)
    :ivar originObj: optional object which was this edge generated for
    :ivar src: LPort instance where this edge starts
    :ivar srcNode: node of src (used as cache)
    :ivar dst: LPort instance where this edge ends
    :ivar dstNode: node of dst (used as cache)
    """

    def __init__(self, name: str=None, originObj=None):
        if name is not None:
            assert isinstance(name, str)
        self.name = name
        self.originObj = originObj
        self.src = None
        self.srcNode = None
        self.dst = None
        self.dstNode = None
        self.labels = []
        self.bendPoints = []

    def setSrcDst(self, src: "LPort", dst: "LPort"):
        self.setSource(src)
        self.setTarget(dst)

    def consystencyCheck(self):
        assert (self.srcNode.parent is self.dstNode.parent
                or self.srcNode is self.dstNode.parent
                or self.srcNode.parent is self.dstNode)
        #p = self.src
        #n = self.srcNode
        #assert p in n.west or p in n.east or p in n.south or p in n.north, self
        #p = self.dst
        #n = self.dstNode
        #assert p in n.west or p in n.east or p in n.south or p in n.north, self

    def setTarget(self, dst: "LPort"):
        if self.dst is not None:
            self.dst.incomingEdges.remove(self)
        self.dst = dst

        if dst is None:
            self.dstNode = None
            self.isSelfLoop = False
        else:
            self.dstNode = dst.getNode()
            dst.incomingEdges.append(self)
            self.isSelfLoop = self.srcNode is self.dstNode

            if self.src is not None:
                self.consystencyCheck()

    def setSource(self, src: "LPort"):
        if self.src is not None:
            self.src.outgoingEdges.remove(self)
        self.src = src

        if src is None:
            self.srcNode = None
            self.isSelfLoop = False
        else:
            self.srcNode = src.getNode()
            src.outgoingEdges.append(self)
            self.isSelfLoop = self.srcNode is self.dstNode

            if self.dst is not None:
                self.consystencyCheck()

    def toElkJson(self, idStore):
        return {
            "id": str(idStore[self]),
            "source": str(idStore[self.srcNode]),
            "sourcePort": str(idStore[self.src]),
            "target": str(idStore[self.dstNode]),
            "targetPort": str(idStore[self.dst]),
        }

    def __repr__(self):
        return "<%s, %r -> %r>" % (
            self.__class__.__name__, self.src, self.dst)
