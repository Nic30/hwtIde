#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Applications of Evolutionary Computing: EvoWorkshops 2001: EvoCOP, EvoFlight p. 174+
"""

from os.path import expanduser

from examples import DualSubunit, CyclicDualSubunit, UnitWithDistributedSig
from hwtIde.examples import LinearDualSubunit
from hwtIde.fromHwtToLayout import Unit_to_LGraph
from hwtLib.amba.axis import AxiStream
from hwtLib.samples.hierarchy.groupOfBlockrams import GroupOfBlockrams
from hwtLib.samples.hierarchy.netFilter import NetFilter
from hwtLib.samples.hierarchy.simpleSubunit import SimpleSubunit
from hwtLib.samples.hierarchy.simpleSubunit2 import SimpleSubunit2
from hwtLib.samples.hierarchy.simpleSubunit3 import SimpleSubunit3
from hwtLib.samples.hierarchy.unitToUnitConnection import UnitToUnitConnection
from hwtLib.samples.showcase0 import Showcase0
from hwtLib.samples.timers import TimerInfoTest
from layeredGraphLayouter.containers.lGraph import LGraph
from layeredGraphLayouter.crossing.layerSweepCrossingMinimizer import LayerSweepCrossingMinimizer
from layeredGraphLayouter.greedyCycleBreaker import GreedyCycleBreaker
from layeredGraphLayouter.minWidthLayerer import MinWidthLayerer
from layeredGraphLayouter.toMxGraph import ToMxGraph
from layeredGraphLayouter.toSvg import ToSvg
import xml.etree.ElementTree as etree
from hwtLib.tests.synthesizer.interfaceLevel.subunitsSynthesisTC import synthesised
from layeredGraphLayouter.edgeManipulators.longEdgeSplitter import LongEdgeSplitter


def renderer_temporal(g: LGraph):
    if not g.layers:
        nodes = g.nodes
        nodes.sort(key=lambda n: n.mark)
        for n in nodes:
            g.layers.append([n, ])

    x_padding = 50
    y_padding = 50
    x_step = max(g.nodes, key=lambda x: x.geometry.width).geometry.width + 100

    x_offset = x_padding
    max_y = 0
    for nodes in g.layers:
        y_offset = y_padding
        for n in nodes:
            n.translate(x_offset, y_offset)
            y_offset += n.geometry.height + y_padding

        max_y = max(max_y, y_offset)
        x_offset += x_step

    g.width = x_offset
    g.height = max_y


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
        g = Unit_to_LGraph(u)
        cycleBreaker = GreedyCycleBreaker()
        layerer = MinWidthLayerer()
        longEdgeSplit = LongEdgeSplitter()
        crossMin = LayerSweepCrossingMinimizer()

        cycleBreaker.process(g)
        layerer.process(g)
        longEdgeSplit.process(g)
        crossMin.process(g)
        renderer_temporal(g)

        def asSvg():
            with open(expanduser("~/layeredGraphs/%s.svg" % name), "wb") as f:
                root = ToSvg(reversed_edge_stroke="lightcoral").LGraph_toSvg(g)
                s = etree.tostring(root)
                f.write(s)

        def asMxGraph():
            with open(expanduser("~/layeredGraphs/%s.xml" % name), "wb") as f:
                root = ToMxGraph().LGraph_toMxGraph(g)
                s = etree.tostring(root)
                f.write(s)

        asSvg()
        asMxGraph()
