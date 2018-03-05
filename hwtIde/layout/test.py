from layout.containers import Unit_to_Layout
from layout.greedyCycleBreaker import GreedyCycleBreaker
from layout.minWidthLayerer import MinWidthLayerer


if __name__ == "__main__":
    import os
    from hwtLib.samples.hierarchy.simpleSubunit import SimpleSubunit
    from hwt.synthesizer.utils import toRtl
    import xml.etree.ElementTree as etree
    from layout.toMxGraph import ToMxGraph

    u = SimpleSubunit()
    toRtl(u)
    g = Unit_to_Layout(u)
    cycleBreaker = GreedyCycleBreaker()
    cycleBreaker.process(g)

    layer = MinWidthLayerer()
    layer.process(g)

    if not g.layers:
        g.layers.append(g.nodes)

    x_offset = 0
    y_offset = 0
    for i, nodes in enumerate(g.layers):
        nodes.sort(key=lambda n: n.mark)
        for n in nodes:
            n.translate(x_offset, y_offset)
        x_offset += 200

    # print(s.toJson())
    with open(os.path.expanduser("~/test.xml"), "wb") as f:
        toMx = ToMxGraph()
        s = etree.tostring(toMx.Layout_toMxGraph(g))
        f.write(s)
        print(s)
