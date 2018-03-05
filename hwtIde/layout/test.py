from layout.containers import Unit_to_Layout
from layout.greedyCycleBreaker import GreedyCycleBreaker
from layout.minWidthLayerer import MinWidthLayerer
from hwt.synthesizer.unit import Unit
from hwt.interfaces.std import Signal
from hwtLib.samples.simple import SimpleUnit


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
