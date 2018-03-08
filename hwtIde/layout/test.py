import os

from hwt.hdl.constants import INTF_DIRECTION
from hwt.hdl.portItem import PortItem
from hwt.interfaces.std import Signal
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl
from hwtLib.samples.hierarchy.simpleSubunit import SimpleSubunit
from hwtLib.samples.simple import SimpleUnit
from hwtLib.samples.simpleAxiStream import SimpleUnitAxiStream
from layout.containers import Layout, LayoutPort, LayoutExternalPort
from layout.examples import LinearDualSubunit
from layout.greedyCycleBreaker import GreedyCycleBreaker
from layout.minWidthLayerer import MinWidthLayerer
from layout.toMxGraph import ToMxGraph
from layout.toSvg import ToSvg
import xml.etree.ElementTree as etree


def origin_obj_of_port(intf):
    d = intf._direction
    if intf._interfaces:
        origin = intf
    elif d == INTF_DIRECTION.MASTER:
        # has hierarchy
        origin = intf._sigInside.endpoints[0]
        assert isinstance(origin, PortItem)
    elif d == INTF_DIRECTION.SLAVE:
        origin = intf._sigInside.drivers[0]
        assert isinstance(origin, PortItem)
    else:
        raise ValueError()

    return origin


def _add_port(lep: LayoutExternalPort, lp: LayoutPort, intf: Interface):
    """
    add port to LayoutPort for interface
    """
    origin = origin_obj_of_port(intf)
    new_lp = LayoutPort(origin, lp, intf._name, intf._direction)
    if intf._interfaces:
        for child_intf in intf:
            _add_port(new_lp, child_intf)

    lp.children.append(new_lp)
    new_lp.parent = lp
    lep._port_obj_map[origin] = lp

    return new_lp


def add_port(la: Layout, intf: Interface):
    """
    Add LayoutExternalPort for interface
    """
    ext_p = la.add_port(intf)
    if ext_p.inputs:
        p = ext_p.inputs[0]
    else:
        p = ext_p.outputs[0]

    for i in intf._interfaces:
        _add_port(ext_p, p, i)

    return ext_p


def resolve_child_ports(la: Layout):
    """
    Walk all ports on all nodes and group subinterface connections to only parent interface
    connection if it is possible otherwise flatten ports to simplify layout generation
    """
    for u in la.nodes:
        new_inputs = []
        new_outputs = []
        raise NotImplementedError("[TODO]")


def Unit_to_Layout(u: Unit) -> Layout:
    """
    Build Layout instance from Unit instance

    :attention: unit has to be synthesized
    """

    la = Layout()
    toL = la._node2lnode
    # create subunits
    for su in u._units:
        la.add_unit(su)

    # create subunits from statements
    for stm in u._ctx.statements:
        n = la.add_stm_as_unit(stm)
        toL.update(n._port_obj_map)

    # create ports
    for intf in u._interfaces:
        add_port(la, intf)

    # connect nets
    for s in u._ctx.signals:
        if not s.hidden:
            assert len(s.drivers) == 1, s
            stm = s.drivers[0]
            la_stm = toL[stm]
            if isinstance(stm, PortItem):
                src = la_stm
            else:
                src = la_stm.outputs[0]

            for stm in s.endpoints:
                la_stm = toL[stm]
                if isinstance(stm, PortItem):
                    dst = la_stm
                else:
                    dst = la_stm.inputs[0]
                la.add_edge(s, s.name, src, dst)

    resolve_child_ports(la)

    for n in la.nodes:
        n.initDim()

    return la


if __name__ == "__main__":
    #u = LinearDualSubunit()
    u = SimpleUnitAxiStream()
    toRtl(u)
    g = Unit_to_Layout(u)
    cycleBreaker = GreedyCycleBreaker()
    cycleBreaker.process(g)

    layer = MinWidthLayerer()
    layer.process(g)

    if not g.layers:
        nodes = g.nodes
        nodes.sort(key=lambda n: n.mark)
        for n in nodes:
            g.layers.append([n, ])

    x_offset = 0
    for i, nodes in enumerate(g.layers):
        nodes.sort(key=lambda n: n.mark)
        y_offset = 0
        for n in nodes:
            n.translate(x_offset, y_offset)
            y_offset += 200
        x_offset += 200

    g.width = x_offset
    g.height = y_offset

    # print(s.toJson())
    with open(os.path.expanduser("~/test.svg"), "wb") as f:
        root = ToSvg().Layout_toSvg(g)
        #root = ToMxGraph().Layout_toMxGraph(g)

        s = etree.tostring(root)
        f.write(s)
        print(s)
