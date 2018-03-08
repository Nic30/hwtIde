from hwt.interfaces.std import Signal
from hwt.synthesizer.unit import Unit
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