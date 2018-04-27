from typing import Optional, Callable, Union, Dict, Set, Tuple, List

from elkContainer.lNode import LNode
from fromHwtToElk.extractSplits import extractSplits
from fromHwtToElk.flattenPorts import flattenPorts
from fromHwtToElk.flattenTrees import flattenTrees
from fromHwtToElk.mergeSplitsOnInterfaces import mergeSplitsOnInterfaces
from fromHwtToElk.reduceUselessAssignments import reduceUselessAssignments
from fromHwtToElk.resolveSharedConnections import resolveSharedConnections
from fromHwtToElk.utils import addOperatorAsLNode, addPortToLNode,\
    addStmAsLNode, addPort, ternaryAsSimpleAssignment,\
    isUselessTernary, ValueAsLNode
from hwt.hdl.operator import Operator, isConst
from hwt.hdl.portItem import PortItem
from hwt.synthesizer.unit import Unit
from elkContainer.constants import PortType, PortSide
from hwt.hdl.assignment import Assignment
from hwt.hdl.ifContainter import IfContainer
from hwt.hdl.switchContainer import SwitchContainer
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.hdl.statements import HdlStatement
from itertools import chain
from _collections import defaultdict
from elkContainer.lPort import LPort
from hwt.synthesizer.rtlLevel.netlist import walk_assignments
from hwt.hdl.types.array import HArray
from hwt.hdl.value import Value


def lazyLoadNode(root, stm, toL):
    try:
        return toL[stm]
    except KeyError:
        if isinstance(stm, Operator):
            if isUselessTernary(stm):
                node = ternaryAsSimpleAssignment(root, stm)
            else:
                node = addOperatorAsLNode(root, stm)
            toL[stm] = node
            return node
        else:
            raise


def walkSignalEndpointsToStatements(sig):
    assert sig.hidden, sig
    for ep in sig.endpoints:
        if isinstance(ep, Operator):
            yield from walkSignalEndpointsToStatements(ep.result)
        else:
            yield ep


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


def sortStatementPorts(root):
    pass


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

        for e in s.endpoints:
            if isinstance(e, Operator) and e not in seen:
                seen.add(e)
                yield e
                res = e.result
                if isinstance(res, RtlSignalBase) and res.hidden and res not in seen:
                    signals.add(res)


FF = "FF"
LATCH = "LATCH"
MUX = "MUX"
RAM_WRITE = "RAM_WRITE"
RAM_READ = "RAM_READ"
CONNECTION = "CONNECTION"


def createRamReadNode(root: LNode,
                      s: RtlSignalBase,
                      clk: Optional[RtlSignalBase],
                      addr: RtlSignalBase,
                      inp: RtlSignalBase,
                      lateConnections, rootPortCtx,
                      connectOut):
    n = root.addNode(RAM_READ)
    if clk is not None:
        clkPort = n.addPort("clk", PortType.INPUT, PortSide.WEST)
        lateConnections[clk][1].append(clkPort)

    aPort = n.addPort("addr", PortType.INPUT, PortSide.WEST)
    memPort = n.addPort("mem", PortType.OUTPUT, PortSide.EAST)
    inPort = n.addPort("in", PortType.INPUT, PortSide.WEST)
    lateConnections[addr][1].append(aPort)
    lateConnections[inp][1].append(inPort)

    if connectOut:
        lateConnections[s][0].append(memPort)


def createFFNode(root: LNode,
                 o: RtlSignalBase,
                 clk: RtlSignalBase,
                 i: RtlSignalBase,
                 lateConnections, rootPortCtx,
                 connectOut):
    n = root.addNode(RAM_READ)
    clkPort = n.addPort("clk", PortType.INPUT, PortSide.WEST)
    lateConnections[clk][1].append(clkPort)

    iPort = n.addPort("i", PortType.INPUT, PortSide.WEST)
    oPort = n.addPort("o", PortType.OUTPUT, PortSide.EAST)
    lateConnections[i][1].append(iPort)

    if connectOut:
        lateConnections[o][0].append(oPort)


def createMux(root: LNode,
              o: RtlSignalBase,
              inputs: List[Union[RtlSignalBase, Value]],
              control: Union[RtlSignalBase, List[RtlSignalBase]],
              output: RtlSignalBase,
              lateConnections, rootPortCtx,
              connectOut):

    n = root.addNode(MUX)
    if isinstance(control, (RtlSignalBase, Value)):
        control = [control, ]

    for c in control:
        cPort = n.addPort("c", PortType.INPUT, PortSide.WEST)
        if isinstance(c, Value):
            v = ValueAsLNode(root, c).east[0]
            root.addEdge(v, cPort)
        else:
            lateConnections[c][1].append(cPort)

    for i in inputs:
        iPort = n.addPort("i", PortType.INPUT, PortSide.WEST)
        if isinstance(i, Value):
            v = ValueAsLNode(root, i).east[0]
            root.addEdge(v, iPort)
        else:
            lateConnections[i][1].append(iPort)

    oPort = n.addPort("o", PortType.OUTPUT, PortSide.EAST)
    if connectOut:
        lateConnections[o][0].append(oPort)


def walkStatementsForSig(statments, s):
    for stm in statments:
        if s in stm._outputs:
            yield stm


def renderStatementForSignal(root: LNode, stm: HdlStatement,
                             s: RtlSignalBase,
                             lateConnections, rootPortCtx):
    """
    Walk statement and render nodes which are representing
    hardware components (MUX, LATCH, FF, ...) for specified signal
    """
    if isinstance(stm, Assignment):
        if not stm.indexes:
            dst = rootPortCtx[stm.dst]
            lateConnections[stm.src][1].append(dst)
        else:
            raise NotImplementedError()

        return

    encl = stm._enclosed_for
    full_ev_dep = stm._is_completly_event_dependent
    now_ev_dep = stm._now_is_event_dependent
    ev_dep = full_ev_dep or now_ev_dep
   
    if isinstance(stm, IfContainer):
        if isinstance(s._dtype, HArray):
            clk = stm.cond
            for a in walk_assignments(stm, s):
                assert len(a.indexes) == 1, "one address per RAM port"
                addr = a.indexes[0]
            createRamReadNode(root, s, clk, addr, a.src,
                              lateConnections, rootPortCtx)
        elif full_ev_dep:
            # ff with optional MUX
            assert not stm.elIfs and not stm.ifFalse, stm
            onlyAssignments = True
            for subStm in walkStatementsForSig(stm.ifTrue, s):
                if not isinstance(subStm, Assignment):
                    onlyAssignments = False
                    _stm = renderStatementForSignal(root, subStm,
                                                    s, lateConnections,
                                                    rootPortCtx)
                    subStatements.append()
        elif o not in encl:
            ctx.registerLatch(o)
            if i > 1:
                ctx.registerMUX(stm, o, i)
        elif i > 1:
            ctx.registerMUX(stm, o, i)
        else:
            # just a connection
            continue
    elif isinstance(stm, SwitchContainer):
        raise NotImplementedError()
    else:
        raise TypeError(stm)

def renderContentOfStatement(root: LNode, toL, rootPortCtx):
    stm = root.originObj

    # for each inputs and outputs render expression trees
    signalsAndOps = set()
    ops = findAllHiddenOperators(
        [sig for sig in chain(stm._inputs, stm._outputs) if sig.hidden],
        signalsAndOps)
    ops = list(ops)

    # sig: (extra src ports, extra dst ports)
    lateConnections = defaultdict(lambda: ([], []))
    # walk statements and render muxs and memories
    for o in stm._outputs:
        renderStatementForSignal(root, stm, o,
                                 lateConnections,
                                 rootPortCtx)

    for op in ops:
        addOperatorAsLNode(root, op)

    for s in signalsAndOps:
        if isinstance(s, RtlSignalBase):
            connectSignalInStatement(s, toL, root, lateConnections)


def connectSignalInStatement(s: RtlSignalBase,
                             toL: Dict[Union[HdlStatement, Operator], LNode],
                             root: LNode,
                             extra: Tuple[List[LPort], List[LPort]]):
    """
    :ivar s: signal to make connections from
    :ivar toL: dictionary for resolving layout node for hdl node
    :ivar root: node of parent statement
    """
    driverPorts = set()
    endpointPorts = set()

    # connect all drivers of this signal with all endpoints
    for stm in s.drivers:
        if isinstance(stm, Operator):
            node = toL[stm]
            driverPorts.add(node.east[0])

    for stm in s.endpoints:
        if isinstance(stm, Operator):
            node = toL[stm]
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


def connectSignalToStatements(s, toL, stmPorts, root):
    driverPorts = set()
    endpointPorts = set()

    def addEndpoint(ep):
        if isinstance(ep, PortItem):
            dst = toL[ep]
            endpointPorts.add(dst)
        else:
            laStm = toL[ep]
            dst = stmPorts[laStm].register(s, PortType.INPUT)
            endpointPorts.add(dst)

    # connect all drivers of this signal with all endpoints
    for stm in s.drivers:
        node = toL[stm]
        if isinstance(stm, PortItem):
            src = node
        elif isinstance(stm, Operator):
            continue
        else:
            src = stmPorts[node].register(s, PortType.OUTPUT)

        driverPorts.add(src)

    for stm in s.endpoints:
        if isinstance(stm, Operator):
            for ep in walkSignalEndpointsToStatements(stm.result):
                addEndpoint(ep)
        else:
            addEndpoint(stm)

    for src in driverPorts:
        for dst in endpointPorts:
            root.addEdge(src, dst, name=s.name, originObj=s)


def UnitToLNode(u: Unit, node: Optional[LNode]=None, toL: Optional[dict]=None) -> LNode:
    """
    Build LNode instance from Unit instance

    :attention: unit has to be synthesized
    """
    if toL is None:
        toL = {}
    if node is None:
        root = LNode(name=u._name, originObj=u, node2lnode=toL)
    else:
        root = node

    stmPorts = {}

    # create subunits
    for su in u._units:
        n = root.addNode(name=su._name, originObj=su)
        #UnitToLNode(su, n, toL)
        for intf in su._interfaces:
            addPortToLNode(n, intf)

    # create subunits from statements
    for stm in u._ctx.statements:
        n = addStmAsLNode(root, stm)
        stmPorts[n] = Signal2stmPortCtx(n)

    # create ports
    for intf in u._interfaces:
        addPort(root, intf)

    # connect nets
    for s in u._ctx.signals:
        if not s.hidden:
            connectSignalToStatements(s, toL, stmPorts, root)

    for stm in u._ctx.statements:
        n = toL[stm]
        renderContentOfStatement(n, toL, stmPorts[n])

    # optimizations
    # reduceUselessAssignments(root)
    extractSplits(root, u._ctx.signals, toL)
    flattenTrees(root, lambda node: node.name == "CONCAT")
    mergeSplitsOnInterfaces(root)
    resolveSharedConnections(root)

    sortStatementPorts(root)
    # required for to json conversion
    flattenPorts(root)

    return root
