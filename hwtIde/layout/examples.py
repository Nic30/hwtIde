from hwt.interfaces.std import Signal
from hwt.synthesizer.unit import Unit


class SimpleUnit(Unit):
    def __init__(self, intfCls=Signal):
        self._intfCls = intfCls
        super(SimpleUnit, self).__init__()

    def _declr(self):
        i = self._intfCls
        self.a = i()
        self.b = i()

    def _impl(self):
        self.b(self.a)


class DualSubunit(Unit):
    def __init__(self, intfCls=Signal):
        self._intfCls = intfCls
        super(DualSubunit, self).__init__()

    def _declr(self):
        i = self._intfCls
        self.a0 = i()
        self.b0 = i()
        self.a1 = i()
        self.b1 = i()

        self.subunit0 = SimpleUnit(i)
        self.subunit1 = SimpleUnit(i)

    def _impl(self):
        u = self.subunit0
        u.a(self.a0)
        self.b0(u.b)

        u = self.subunit1
        u.a(self.a1)
        self.b1(u.b)


class CyclicDualSubunit(Unit):
    def __init__(self, intfCls=Signal):
        self._intfCls = intfCls
        super(CyclicDualSubunit, self).__init__()

    def _declr(self):
        i = self._intfCls
        self.a0 = i()
        self.b0 = i()
        self.a1 = i()
        self.b1 = i()

        self.subunit0 = DualSubunit(i)
        self.subunit1 = DualSubunit(i)

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
    def __init__(self, intfCls=Signal):
        self._intfCls = intfCls
        super(LinearDualSubunit, self).__init__()

    def _declr(self):
        i = self._intfCls
        self.a0 = i()
        self.b0 = i()
        self.a1 = i()
        self.b1 = i()
        self.c = i()
        self.d = i()

        self.subunit0 = DualSubunit(i)
        self.subunit1 = DualSubunit(i)

    def _impl(self):
        u0 = self.subunit0
        u1 = self.subunit1
        u0.a0(self.a0)
        u0.a1(self.c)

        self.b0(u0.b0)

        u1.a0(self.a1)
        u1.a1(u0.b1)

        self.d(u1.b0)
        self.b1(u1.b1)
