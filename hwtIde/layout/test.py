from os.path import expanduser

from hwt.synthesizer.utils import toRtl
from hwtLib.amba.axis import AxiStream
from layout.examples import LinearDualSubunit
from layout.fromHwtToLayout import Unit_to_Layout
from layout.greedyCycleBreaker import GreedyCycleBreaker
from layout.minWidthLayerer import MinWidthLayerer
from layout.toMxGraph import ToMxGraph
from layout.toSvg import ToSvg
import xml.etree.ElementTree as etree


if __name__ == "__main__":
    u = LinearDualSubunit(AxiStream)
    #u = DualSubunit(AxiStream)
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
    x_step = max(g.nodes, key=lambda x: x.geometry.width).geometry.width + 100
    y_step = max(
        g.nodes, key=lambda x: x.geometry.height).geometry.height + 100

    x_offset = 0
    for i, nodes in enumerate(g.layers):
        nodes.sort(key=lambda n: n.mark)
        y_offset = 0
        for n in nodes:
            n.translate(x_offset, y_offset)
            y_offset += y_step
        x_offset += x_step

    g.width = x_offset
    g.height = y_offset

    def asSvg():
        with open(expanduser("~/test.svg"), "wb") as f:
            root = ToSvg(reversed_edge_stroke="lightcoral").Layout_toSvg(g)
            s = etree.tostring(root)
            f.write(s)

    def asMxGraph():
        with open(expanduser("~/test.xml"), "wb") as f:
            root = ToMxGraph().Layout_toMxGraph(g)
            s = etree.tostring(root)
            f.write(s)

    asMxGraph()
    asSvg()
