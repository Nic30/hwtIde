#                     __________
# if rising(clk): clk-|>       |
#     a(1)         1--|in   out|---a
#
#                              __________
# if rising(clk):  1-|-\   clk-|>       |
#     if b:          |  >------|in   out|---a
#        a(1)      2-|-/
#     else:           |
#        a(2)         b
#
from collections import defaultdict
from itertools import chain
from typing import Dict, Union, Tuple, List, Set, Optional

from elkContainer.constants import PortType, PortSide
from elkContainer.lNode import LNode
from elkContainer.lPort import LPort
from fromHwtToElk.utils import addOperatorAsLNode, ValueAsLNode
from hwt.hdl.assignment import Assignment
from hwt.hdl.ifContainter import IfContainer
from hwt.hdl.operator import Operator, isConst
from hwt.hdl.statements import HdlStatement
from hwt.hdl.switchContainer import SwitchContainer
from hwt.hdl.types.array import HArray
from hwt.hdl.value import Value
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.netlist import walk_assignments


FF = "FF"
LATCH = "LATCH"
MUX = "MUX"
RAM_WRITE = "RAM_WRITE"
RAM_READ = "RAM_READ"
CONNECTION = "CONNECTION"


def walkStatementsForSig(statments, s):
    for stm in statments:
        if s in stm._outputs:
            yield stm


class Signal2stmPortCtx(dict):
    def __init__(self, stmNode: LNode):
        self.stmNode = stmNode

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


class StatementRenderer():
    def __init__(self, node: LNode, toL, portCtx):
        self.node = node
        self.stm = node.originObj
        self.toL = toL
        self.portCtx = portCtx

        # sig: (extra src ports, extra dst ports)
        self.extraConn = defaultdict(lambda: ([], []))

    def addInputPort(self, node, name,
                     inpValue: Union[Value, RtlSignalBase],
                     side=PortSide.WEST):
        root = self.node
        port = node.addPort(name, PortType.INPUT, side)
        if isinstance(inpValue, Value):
            v = ValueAsLNode(root, inpValue).east[0]
            root.addEdge(v, port)
        else:
            if isinstance(inpValue, LPort):
                root.addEdge(inpValue, port)
            elif not inpValue.hidden:
                inpValue = self.portCtx[inpValue]
                root.addEdge(inpValue, port)
            else:
                self.extraConn[inpValue][1].append(port)

    def addOutputPort(self, node: LNode, name: str,
                      out: Optional[Union[Value, RtlSignalBase]],
                      side=PortSide.EAST):
        oPort = node.addPort(name, PortType.OUTPUT, side)
        if out is not None:
            if isinstance(out, LPort):
                self.node.addEdge(oPort, out)
            elif out.hidden:
                self.extraConn[out][0].append(oPort)
            else:
                out = self.portCtx[out]
                self.node.addEdge(oPort, out)

        return oPort

    def createRamWriteNode(self,
                           s: RtlSignalBase,
                           clk: Optional[RtlSignalBase],
                           addr: RtlSignalBase,
                           inp: RtlSignalBase,
                           connectOut):
        n = self.node.addNode(RAM_WRITE)
        if clk is not None:
            self.addInputPort(n, "clk", clk)

        self.addInputPort(n, "addr", addr)
        self.addInputPort(n, "in", inp)

        memPort = self.addOutputPort(n, "mem", s if connectOut else None)

        return n, memPort

    def createFFNode(self,
                     o: RtlSignalBase,
                     clk: RtlSignalBase,
                     i: RtlSignalBase,
                     connectOut):
        c = self.extraConn
        n = self.node.addNode(FF)
        self.addInputPort(n, "clk", clk)
        self.addInputPort(n, "i", i)

        oPort = self.addOutputPort(n, "o", o if connectOut else None)

        return n, oPort

    def createMux(self,
                  output: RtlSignalBase,
                  inputs: List[Union[RtlSignalBase, Value]],
                  control: Union[RtlSignalBase, List[RtlSignalBase]],
                  connectOut):
        con = self.extraConn
        root = self.node
        portCtx = self.portCtx
        addInputPort = self.addInputPort

        n = root.addNode(MUX)
        if isinstance(control, (RtlSignalBase, Value)):
            control = [control, ]

        for c in control:
            addInputPort(n, "", c, PortSide.SOUTH)

        for i in inputs:
            addInputPort(n, "", i)

        oPort = n.addPort("", PortType.OUTPUT, PortSide.EAST)
        if connectOut:
            if output.hidden:
                con[output][0].append(oPort)
            else:
                output = portCtx[output]
                root.addEdge(oPort, output)

        return n, oPort

    def renderContent(self):
        stm = self.stm
        node = self.node
        portCtx = self.portCtx
        # for each inputs and outputs render expression trees
        signalsAndOps = set()
        ops = findAllHiddenOperators(
            [sig for sig in chain(stm._inputs, stm._outputs) if sig.hidden],
            signalsAndOps)
        ops = list(ops)

        # walk statements and render muxs and memories
        for o in stm._outputs:
            self.renderForSignal(stm, o)

        def connectExternalInputs(operand, opPort):
            if not operand.hidden:
                src = portCtx[operand]
                node.addEdge(src, opPort)

        for op in ops:
            addOperatorAsLNode(node, op, operandSigCheck=connectExternalInputs)

        for s in signalsAndOps:
            if isinstance(s, RtlSignalBase):
                self.makeConnections(s)

    def makeConnections(self, s: RtlSignalBase):
        """
        :ivar s: signal to make connections from
        :ivar toL: dictionary for resolving layout node for hdl node
        :ivar root: node of parent statement
        """
        toL = self.toL
        root = self.node
        driverPorts = set()
        endpointPorts = set()
        extra = self.extraConn

        # connect all drivers of this signal with all endpoints
        for stm in s.drivers:
            if isinstance(stm, Operator):
                node = toL[stm]
                driverPorts.add(node.east[0])

        for stm in s.endpoints:
            if isinstance(stm, Operator):
                node = toL.get(stm, None)
                if node is not None and node.parent is root:
                    for op, port in zip(stm.operands, node.west):
                        if op is s:
                            endpointPorts.add(port)

        _extra = extra.get(s, None)
        if _extra:
            for src in _extra[0]:
                driverPorts.add(src)
            for dst in _extra[1]:
                endpointPorts.add(dst)

        for src in driverPorts:
            for dst in endpointPorts:
                root.addEdge(src, dst, name=s.name, originObj=s)

    @staticmethod
    def isJustConstAssign(stm):
        return isinstance(stm, Assignment) and not stm.indexes and isConst(stm.src)
        
    def renderForSignal(self, stm: Union[HdlStatement, List[HdlStatement]],
                        s: RtlSignalBase,
                        connectOut=True) -> Union[RtlSignalBase, LPort]:
        """
        Walk statement and render nodes which are representing
        hardware components (MUX, LATCH, FF, ...) for specified signal
        """
        # filter statements for this signal only if required
        if not isinstance(stm, HdlStatement):
            stm = list(walkStatementsForSig(stm, s))
            if len(stm) != 1:
                raise NotImplementedError("deduced MUX")
            else:
                stm = stm[0]

        # render assignment instances
        if isinstance(stm, Assignment):
            if stm.indexes:
                raise NotImplementedError()
            else:
                assert stm.dst is s, (stm.dst, s)
                if connectOut:
                    dst = self.portCtx[s]
                    self.extraConn[stm.src][1].append(dst)
                    return None, dst
                else:
                    return None, stm.src

        encl = stm._enclosed_for
        full_ev_dep = stm._is_completly_event_dependent
        now_ev_dep = stm._now_is_event_dependent
        ev_dep = full_ev_dep or now_ev_dep
        par = stm.parentStm
        parent_ev_dep = par is not None and par._now_is_event_dependent

        # render IfContainer instances
        if isinstance(stm, IfContainer):
            if isinstance(s._dtype, HArray):
                # ram output port
                # [TODO]
                clk = stm.cond
                for a in walk_assignments(stm, s):
                    assert len(a.indexes) == 1, "one address per RAM port"
                    addr = a.indexes[0]
                return self.createRamWriteNode(s, clk, addr,
                                               a.src, connectOut)

            elif full_ev_dep and not parent_ev_dep:
                # FF with optional MUX
                assert not stm.ifFalse, stm
                if stm.elIfs:
                    raise NotImplementedError(MUX)

                subStms = list(walkStatementsForSig(stm.ifTrue, s))
                assert len(subStms) == 1, subStms
                subStm = subStms[0]
                _, _out = self.renderForSignal(subStm, s, False)
                return self.createFFNode(s, stm.cond, _out, connectOut)

            elif par is None and not parent_ev_dep and s not in encl:
                # LATCH
                raise NotImplementedError(LATCH)
            else:
                # MUX
                controls = [stm.cond]
                inputs = [self.renderForSignal(stm.ifTrue, s, False)[1]]
                for c, stms in stm.elIfs:
                    controls.append(c)
                    inputs.append(self.renderForSignal(stms, s, False)[1])
                inputs.append(self.renderForSignal(stm.ifFalse, s, False)[1])

                return self.createMux(s, inputs, controls, connectOut)

        # render SwitchContainer instances
        elif isinstance(stm, SwitchContainer):
            if s in encl:
                inputs = []
                for _, stms in stm.cases:
                    inputs.append(self.renderForSignal(stms, s, False)[1])

                if stm.default:
                    inputs.append(self.renderForSignal(stm.default, s, False)[1])

                return self.createMux(s, inputs, stm.switchOn, connectOut)
            else:
                raise NotImplementedError(LATCH, MUX)
        else:
            raise TypeError(stm)


def findAllHiddenOperators(signals: RtlSignalBase,
                           seen: Set[Union[RtlSignalBase, Operator]]):
    signals = set(signals)
    while signals:
        s = signals.pop()
        seen.add(s)
        for d in s.drivers:
            if isinstance(d, Operator) and d not in seen:
                seen.add(d)
                yield d
                for op in d.operands:
                    if isinstance(op, RtlSignalBase) and op.hidden and op not in seen:
                        signals.add(op)

#        for e in s.endpoints:
#            if isinstance(e, Operator) and e not in seen:
#                seen.add(e)
#                yield e
#                res = e.result
#                if isinstance(res, RtlSignalBase) and res.hidden and res not in seen:
#                    signals.add(res)
#
