from elkContainer.lNode import LNode
from elkContainer.constants import PortType, PortSide
from hwt.hdl.statements import HdlStatement
from hwt.hdl.assignment import Assignment
from hwt.hdl.operator import isConst
from fromHwtToElk.utils import ValueAsLNode, toStr, NetCtxs
from typing import Dict


def walkStatementsForSig(statments, s):
    for stm in statments:
        if s in stm._outputs:
            yield stm


class Signal2stmPortCtx(dict):
    def __init__(self, stmNode: LNode):
        self.stmNode = stmNode

    def getInside(self, k, portType):
        p = self.get(k, None)
        if not isinstance(self.stmNode, VirtualLNode):
            if p is None:
                return self.register(k, portType)
            else:
                return p

        n = p.getNode()
        if p.direction == PortType.INPUT:
            return n.east[0]
        elif p.direction == PortType.OUTPUT:
            return n.west[0]
        else:
            raise NotImplementedError()

    def getOutside(self, k):
        return self[k]

    def register(self, sig, portType: PortType):
        p = self.get(sig, None)
        if p is not None:
            return p

        if portType == PortType.INPUT:
            side = PortSide.WEST
        elif portType == portType.OUTPUT:
            side = PortSide.EAST
        else:
            raise ValueError(portType)

        p = self.stmNode.addPort(sig.name, portType, side)
        self[sig] = p
        return p


class VirtualLNode():
    def __init__(self, parent: LNode, stm: HdlStatement):
        self.originObj = stm
        self.parent = parent
        self.addNode = parent.addNode
        self.addEdge = parent.addEdge

    def __repr__(self):
        return "<VirtualLNode for %r>" % self.originObj


def addStmAsLNode(root: LNode, stm: HdlStatement,
                  stmPorts: Dict[LNode, Signal2stmPortCtx],
                  netCtx: NetCtxs) -> LNode:
    toL = root._node2lnode
    isOnlyAssig = isinstance(stm, Assignment)
    if isOnlyAssig and not stm.indexes and isConst(stm.src):
        # is only constant
        n = ValueAsLNode(root, stm.src)
        netCtx.getDefault(stm.dst).addDriver(n.east[0])
    elif isOnlyAssig:
        # inline operatos in assingment to parent node
        n = toL[stm] = VirtualLNode(root, stm)
    else:
        # render content of statement into container node
        bodyText = toStr(stm)
        n = root.addNode(
            originObj=stm, bodyText=bodyText)

        stmPorts[n] = Signal2stmPortCtx(n)
    return n