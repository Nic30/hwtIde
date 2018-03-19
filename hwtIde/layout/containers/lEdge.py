from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


class LEdge():
    def __init__(self, signal: RtlSignal, name: str):
        self.name = name
        self.signal = signal
        self.src = None
        self.srcNode = None
        self.dst = None
        self.dstNode = None
        self.reversed = False

    def setSrcDst(self, src: "LPort", dst: "LPort"):
        self.src = src
        self.srcNode = src.getNode()
        self.dst = dst
        self.dstNode = dst.getNode()
        src.outgoingEdges.append(self)
        dst.incomingEdges.append(self)

    def reverse(self):
        self.src.outgoingEdges.remove(self)
        self.dst.incomingEdges.remove(self)
        self.src, self.dst = self.dst, self.src
        self.src.outgoingEdges.append(self)
        self.dst.incomingEdges.append(self)

        self.srcNode, self.dstNode = self.dstNode, self.srcNode
        self.reversed = not self.reversed

    def isSelfLoop(self):
        """
        :return: True if source is same node as destination
        """
        return self.srcNode is self.dstNode

    def __repr__(self):
        if self.reversed:
            return "<%sm reversed, %r -> %r>" % (self.__class__.__name__, self.dst, self.src)
        else:
            return "<%s, %r -> %r>" % (self.__class__.__name__, self.src, self.dst)
