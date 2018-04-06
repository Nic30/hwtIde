#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Applications of Evolutionary Computing: EvoWorkshops 2001: EvoCOP, EvoFlight p. 174+
"""

from examples import DualSubunit, CyclicDualSubunit, UnitWithDistributedSig
from hwtIde.examples import LinearDualSubunit
from hwtLib.amba.axis import AxiStream
from hwtLib.samples.hierarchy.groupOfBlockrams import GroupOfBlockrams
from hwtLib.samples.hierarchy.netFilter import NetFilter
from hwtLib.samples.hierarchy.simpleSubunit import SimpleSubunit
from hwtLib.samples.hierarchy.simpleSubunit2 import SimpleSubunit2
from hwtLib.samples.hierarchy.simpleSubunit3 import SimpleSubunit3
from hwtLib.samples.hierarchy.unitToUnitConnection import UnitToUnitConnection
from hwtLib.samples.showcase0 import Showcase0
from hwtLib.samples.timers import TimerInfoTest
from hwtLib.tests.synthesizer.interfaceLevel.subunitsSynthesisTC import synthesised
from fromHwtToLayout import Unit_to_LNode
from elkContainer.idStore import ElkIdStore


if __name__ == "__main__":
    units = [
        UnitWithDistributedSig(),
        LinearDualSubunit(AxiStream),
        DualSubunit(AxiStream),
        CyclicDualSubunit(AxiStream),
        NetFilter(),
        GroupOfBlockrams(),
        SimpleSubunit(),
        SimpleSubunit2(),
        SimpleSubunit3(),
        UnitToUnitConnection(),
        TimerInfoTest(),
        Showcase0(),
    ]

    for u in units:
        synthesised(u)
        name = u._name
        print(name)
        g = Unit_to_LNode(u)
        idStore = ElkIdStore()
        print(g.toElkJson(idStore))
