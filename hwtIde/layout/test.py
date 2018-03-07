from hwt.hdl.portItem import PortItem
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import walkPhysInterfaces
from layout.containers import Layout
from layout.greedyCycleBreaker import GreedyCycleBreaker
from layout.minWidthLayerer import MinWidthLayerer


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
