from hwt.hdl.portItem import PortItem
from hwt.interfaces.std import Signal
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import walkPhysInterfaces
from hwt.synthesizer.unit import Unit
from hwtLib.samples.simple import SimpleUnit
from layout.containers import Layout
from layout.greedyCycleBreaker import GreedyCycleBreaker
from layout.minWidthLayerer import MinWidthLayerer


class DualSubunit(Unit):
    def _declr(self):
        self.a0 = Signal()
        self.b0 = Signal()
        self.a1 = Signal()
        self.b1 = Signal()

        self.subunit0 = SimpleUnit()
        self.subunit1 = SimpleUnit()

    def _impl(self):
        u = self.subunit0
        u.a(self.a0)
        self.b0(u.b)

        u = self.subunit1
        u.a(self.a1)
        self.b1(u.b)


class CyclicDualSubunit(Unit):

    def _declr(self):
        self.a0 = Signal()
        self.b0 = Signal()
        self.a1 = Signal()
        self.b1 = Signal()

        self.subunit0 = DualSubunit()
        self.subunit1 = DualSubunit()

    def _impl(self):
        u0 = self.subunit0
        u1 = self.subunit1
        u0.a0(self.a0)
        u0.a1(u1.b0)

        self.b0(u0.b0)

        u1.a0(self.a1)
        u1.a1(u0.b1)

        self.b1(u1.b1)


class LinearDualSubunit(Unit):

    def _declr(self):
        self.a0 = Signal()
        self.b0 = Signal()
        self.a1 = Signal()
        self.b1 = Signal()

        self.subunit0 = DualSubunit()
        self.subunit1 = DualSubunit()

    def _impl(self):
        u0 = self.subunit0
        u1 = self.subunit1
        u0.a0(self.a0)
        u0.a1(1)

        self.b0(u0.b0)

        u1.a0(self.a1)
        u1.a1(u0.b1)

        self.b1(u1.b1)


def Unit_to_Layout(u):
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
        for si in walkPhysInterfaces(intf):
            la.add_port(si)

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

    for n in la.nodes:
        n.initDim()

    return la


if __name__ == "__main__":
    import os
    import xml.etree.ElementTree as etree

    from hwtLib.samples.hierarchy.simpleSubunit import SimpleSubunit
    from hwt.synthesizer.utils import toRtl
    from layout.toMxGraph import ToMxGraph
    from layout.toSvg import ToSvg

    u = LinearDualSubunit()
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
    with open(os.path.expanduser("~/test.xml"), "wb") as f:
        #root = ToSvg().Layout_toSvg(g)
        root = ToMxGraph().Layout_toMxGraph(g)

        s = etree.tostring(root)
        f.write(s)
        print(s)
