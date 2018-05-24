from collections import defaultdict
from itertools import chain
from typing import Union, List, Set, Optional, Tuple

from elkContainer.constants import PortType, PortSide
from elkContainer.lNode import LNode
from elkContainer.lPort import LPort
from fromHwtToElk.utils import ValueAsLNode,\
    isUselessTernary, isUselessEq, NetCtxs
from hwt.hdl.assignment import Assignment
from hwt.hdl.ifContainter import IfContainer
from hwt.hdl.operator import Operator, isConst
from hwt.hdl.statements import HdlStatement
from hwt.hdl.switchContainer import SwitchContainer
from hwt.hdl.types.array import HArray
from hwt.hdl.value import Value
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.netlist import walk_assignments
from fromHwtToElk.statementRendererUtils import VirtualLNode,\
    walkStatementsForSig
from hwt.hdl.operatorDefs import AllOps


FF = "FF"
LATCH = "LATCH"
MUX = "MUX"
RAM_WRITE = "RAM_WRITE"
RAM_READ = "RAM_READ"
CONNECTION = "CONNECTION"

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


class StatementRenderer():
    def __init__(self, node: LNode, toL, portCtx, rootNetCtxs):
        self.stm = node.originObj
        self.toL = toL
        self.portCtx = portCtx
        self.rootNetCtxs = rootNetCtxs
        self.isVirtual = isinstance(node, VirtualLNode)

        if self.isVirtual:
            self.node = node.parent
            self.netCtxs = rootNetCtxs
        else:
            self.node = node
            self.netCtxs = NetCtxs()

    def addInputPort(self, node, name,
                     inpValue: Union[Value, RtlSignalBase],
                     side=PortSide.WEST):
        """
        Add and connect input port on subnode
        """
        root = self.node
        port = node.addPort(name, PortType.INPUT, side)
        if isinstance(inpValue, Value):
            v = ValueAsLNode(root, inpValue).east[0]
            root.addEdge(v, port)
        else:
            if isinstance(inpValue, LPort):
                root.addEdge(inpValue, port)
            elif inpValue.hidden:
                self.renderOperatorTree(inpValue)
            else:
                if self.portCtx is None:
                    # connect from original signal
                    self.rootNetCtxs.getDefault(inpValue).addEndpoint(port)
                else:
                    # connect this input from port of wrap
                    _inpValue = self.portCtx.getInside(
                        inpValue, PortType.INPUT)
                    root.addEdge(_inpValue, port)

                    # connect parent signal to port of wrap
                    oinpValue = self.portCtx.getOutside(inpValue)
                    self.rootNetCtxs.getDefault(
                        inpValue).addEndpoint(oinpValue)

    def addOutputPort(self, node: LNode, name: str,
                      out: Optional[RtlSignalBase],
                      side=PortSide.EAST):
        """
        Add and connect output port on subnode
        """
        oPort = node.addPort(name, PortType.OUTPUT, side)
        if out is not None:
            if isinstance(out, LPort):
                self.node.addEdge(oPort, out)
            elif out.hidden:
                raise NotImplementedError()
            else:
                if self.portCtx is None:
                    self.rootNetCtxs.getDefault(out).addDriver(oPort)
                else:
                    _out = self.portCtx.getInside(out, PortType.OUTPUT)
                    self.node.addEdge(oPort, _out)
                    ooPort = self.portCtx.getOutside(out)
                    self.rootNetCtxs.getDefault(out).addDriver(ooPort)

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
        root = self.node
        addInputPort = self.addInputPort

        n = root.addNode(MUX)
        if isinstance(control, (RtlSignalBase, Value)):
            control = [control, ]

        for c in control:
            addInputPort(n, "", c, PortSide.SOUTH)

        for i in inputs:
            addInputPort(n, "", i)

        oPort = self.addOutputPort(n, "",
                                   output if connectOut else None)

        return n, oPort

    def createAssignment(self, assig: Assignment, connectOut: bool):
        pctx = self.portCtx
        if assig.indexes:
            raise NotImplementedError()
        elif connectOut:
            dst = assig.dst
            rootNetCtxs = self.rootNetCtxs
            if pctx is None:
                # connect to original dst signal directly
                src = assig.src
                rootNetCtxs.getDefault(dst).addDriver(src)
                assert rootNetCtxs[dst] is rootNetCtxs[src]
                if isinstance(src, RtlSignalBase) and src.hidden:
                    self.renderOperatorTree(src)
                return None, dst
            else:
                # connect src to dst port on this wrap
                dstPort = pctx.getInside(dst,
                                         PortType.OUTPUT)
                raise NotImplementedError()
                # connect original signal from port on this wrap

                odstPort = pctx.getOutside(dst)
                rootNetCtxs.getDefault(dst).addDriver(odstPort)
                return None, dstPort
        else:
            return None, assig.src

    def connectInput(self, signal: RtlSignalBase, port: LPort):
        """
        :param signal: signal to connect to specified port
        :param port: input port which should be connected with specified signal
        """

        if signal.hidden:
            # later connect driver of this signal to output port
            self.netCtxs.getDefault(signal).addEndpoint(port)
        else:
            node = self.node
            portCtx = self.portCtx
            rootNetCtxs = self.rootNetCtxs

            if portCtx is None:
                _port = port
            else:
                # spot input port on this wrap node if required
                src = portCtx.register(signal, PortType.INPUT)
                # connect input port on wrap node with specified output port
                node.addEdge(src, port)

                # get input port from parent view
                _port = portCtx.getOutside(signal)

            # later connect signal in root to input port or 
            rootNetCtxs.getDefault(signal).addEndpoint(_port)

    def addOperatorAsLNode(self, op: Operator):
        root = self.node
        if op.operator == AllOps.INDEX:
            inputNames = ["in", "index"]
        else:
            inputNames = [None for _ in op.operands]

        u = root.addNode(originObj=op, name=op.operator.id)
        u.addPort(None, PortType.OUTPUT, PortSide.EAST)

        for inpName, op in zip(inputNames, op.operands):
            p = u.addPort(inpName,  PortType.INPUT,  PortSide.WEST)

            if isConst(op):
                op = op.staticEval()
                v = ValueAsLNode(root, op).east[0]
                root.addEdge(v, p)
            else:
                self.connectInput(op, p)
                if op.hidden:
                    self.renderOperatorTree(op)

        return u

    def renderOperatorTree(self, signal):
        """
        :param signal: top signal of hidden operator tree
        :note: operator tree is constrained by signals with hidden==False
        :note: statement nodes are not connected automatically
        """
        #print("renderOperatorTree", signal)
        assert len(signal.drivers) == 1, signal
        driver = signal.drivers[0]
        if isinstance(driver, Operator):
            d = self.addOperatorAsLNode(driver)
            self.netCtxs.getDefault(signal).addDriver(d.east[0])

    def renderContent(self):
        """
        Walk from outputs to inputs
        for each public signal register port of wrap node if required
        lazy load all operator and statement nodes for signals
        """
        stm = self.stm
        portCtx = self.portCtx
        # for each inputs and outputs render expression trees

        # walk statements and render muxs and memories
        for o in stm._outputs:
            if portCtx is not None:
                portCtx.register(o, PortType.OUTPUT)
            self.renderForSignal(stm, o, True)

        if not self.isVirtual:
            self.netCtxs.applyConnections(self.node)

    # def makeConnections(self, s: RtlSignalBase):
    #    """
    #    :ivar s: signal to make connections from
    #    :ivar toL: dictionary for resolving layout node for hdl node
    #    :ivar root: node of parent statement
    #    """
    #    toL = self.toL
    #    root = self.node
    #    driverPorts = set()
    #    endpointPorts = set()
    #    extra = self.extraConn
    #
    #    # connect all drivers of this signal with all endpoints
    #    for stm in s.drivers:
    #        if isinstance(stm, Operator):
    #            node = toL[stm]
    #            driverPorts.add(node.east[0])
    #
    #    for stm in s.endpoints:
    #        if isinstance(stm, Operator):
    #            node = toL.get(stm, None)
    #            if node is not None and node.parent is root:
    #                for op, port in zip(stm.operands, node.west):
    #                    if op is s:
    #                        endpointPorts.add(port)
    #
    #    _extra = extra.get(s, None)
    #    if _extra is not None:
    #        for src in _extra[0]:
    #            driverPorts.add(src)
    #        for dst in _extra[1]:
    #            endpointPorts.add(dst)
    #
    #    net = self.rootNetCtxs.get(s, None)
    #    if net is not None:
    #        for src in driverPorts:
    #            net.addDriver(src)
    #        for dst in endpointPorts:
    #            net.addEndpoint(dst)
    #    else:
    #        for src in driverPorts:
    #            for dst in endpointPorts:
    #                root.addEdge(src, dst, name=s.name, originObj=s)
    #
    def renderForSignal(self, stm: Union[HdlStatement, List[HdlStatement]],
                        s: RtlSignalBase,
                        connectOut) -> Tuple[LNode, Union[RtlSignalBase, LPort]]:
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
            return self.createAssignment(stm, connectOut)

        encl = stm._enclosed_for
        full_ev_dep = stm._is_completly_event_dependent
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
                raise NotImplementedError(LATCH, stm)
            else:
                # MUX
                controls = [stm.cond]
                inputs = [self.renderForSignal(stm.ifTrue, s, False)[1]]
                for c, stms in stm.elIfs:
                    controls.append(c)
                    inputs.append(
                        self.renderForSignal(stms, s, False)[1])
                if stm.ifFalse:
                    inputs.append(self.renderForSignal(
                        stm.ifFalse, s, False)[1])

                return self.createMux(s, inputs, controls, connectOut)

        # render SwitchContainer instances
        elif isinstance(stm, SwitchContainer):
            if s in encl:
                inputs = []
                for _, stms in stm.cases:
                    inputs.append(self.renderForSignal(stms, s, False)[1])

                if stm.default:
                    inputs.append(self.renderForSignal(
                        stm.default, s, False)[1])

                return self.createMux(s, inputs, stm.switchOn, connectOut)
            else:
                raise NotImplementedError(LATCH, MUX)
        else:
            raise TypeError(stm)
