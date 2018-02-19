from itertools import chain

from hwt.hdl.constants import INTF_DIRECTION, DIRECTION, DIRECTION_to_str
from hwt.hdl.portItem import PortItem
from hwt.hdl.statements import HdlStatement
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl
import xml.etree.ElementTree as etree
from layoutGeometry import GeometryRect


UNIT_HEADER_OFFSET = 20
PORT_HEIGHT = 20
PORT_X_PADDING = 20
UNIT_PADDING = 5


def width_of_str(s):
    return len(s) * 12


def mxCell(**kvargs):
    return etree.Element("mxCell", attrib=kvargs)


class LayoutIdCtx(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.max_id = 0
        self.orig_to_layout = {}

    def register(self, origObj, layoutObj) -> int:
        assert origObj not in self.orig_to_layout, origObj
        i = self.max_id
        self[i] = layoutObj
        self.orig_to_layout[origObj] = layoutObj
        self.max_id += 1
        return i


class LayoutPort():
    """
    Port for component in component diagram

    :ivar parent: parent unit of this port
    :ivar on_parent_index: index of this port on parent
    :ivar name: name of this port
    :ivar direction: direction of this port
    :ivar geometry: absolute geometry in layout
    :ivar id: unique id in layout diagram
    """

    def __init__(self, id_ctx: LayoutIdCtx, portItem: PortItem, parent: "LayoutUnit",
                 on_parent_index: int, name: str, direction):
        self.parent = parent
        self.on_parent_index = on_parent_index
        self.name = name
        self.direction = direction
        self.geometry = None
        self.id = id_ctx.register(portItem, self)

    def updateGeometry(self, x_offset, y_offset, width):
        y = y_offset + UNIT_HEADER_OFFSET + self.on_parent_index * PORT_HEIGHT
        self.geometry = GeometryRect(x_offset, y, width, PORT_HEIGHT)

    def getMxGraphId(self):
        p = self.parent.geometry
        g = self.geometry
        x_rel = (g.x - p.x) / p.width
        y_rel = (g.y - p.y) / p.height
        assert x_rel >= 0.0 and x_rel <= 1.0
        assert y_rel >= 0.0 and y_rel <= 1.0

        return x_rel, y_rel, self.parent.getMxGraphId()

    def toJson(self):
        return {"id": self.id,
                "geometry": self.geometry.toJson(),
                "name": self.name}


class LayoutUnit():
    """
    Component for component diagram

    :ivar name: name of this unit
    :ivar class_name: name of class of this unit
    :ivar inputs: list of LayoutPort for each input of this unit
    :ivar outputs: list of LayoutPort for each output of this unit
    :ivar _id_ctx: id context for resolution of unique ids
        for each diagram object
    :ivar id: unique diagram id of this object
    """

    def __init__(self, id_ctx: LayoutIdCtx, unit: Unit, name: str, class_name: str):
        self.name = name
        self.class_name = class_name
        self.inputs = []
        self.outputs = []
        self._id_ctx = id_ctx
        self.id = id_ctx.register(unit, self)
        self.geometry = None

    def updateGeometry(self, x, y):
        label_w = width_of_str(self.name)
        port_w = max(*map(lambda p: width_of_str(p.name),
                          chain(self.inputs, self.outputs)),
                     label_w / 2)
        width = max(port_w, label_w)
        height = UNIT_HEADER_OFFSET + \
            max(len(self.inputs), len(self.outputs)) * PORT_HEIGHT

        port_width = width / 2
        for i in self.inputs:
            i.updateGeometry(x, y, port_width)

        o_x_offset = x + port_width
        for o in self.outputs:
            o.updateGeometry(o_x_offset, y, port_width)

        self.geometry = GeometryRect(x, y, width, height)

    def add_port(self, intf: Interface, reverse_dir=False):
        d = intf._direction
        if d == INTF_DIRECTION.MASTER:
            if reverse_dir:
                portArr = self.inputs
            else:
                portArr = self.outputs
            pi = intf._sigInside.endpoints[0]
        elif d == INTF_DIRECTION.SLAVE:
            if reverse_dir:
                portArr = self.outputs
            else:
                portArr = self.inputs
            pi = intf._sigInside.drivers[0]
        else:
            raise Exception()

        assert isinstance(pi, PortItem)
        p = LayoutPort(self._id_ctx, pi, self,
                       len(portArr), intf._name, d)
        portArr.append(p)

    @classmethod
    def fromIntfUnit(cls, id_ctx: LayoutIdCtx, u: Unit):
        self = cls(id_ctx, u, u._name, u.__class__.__name__)
        for intf in u._interfaces:
            self.add_port(intf)

        return self

    def getMxGraphId(self):
        return str(self.id + 2)

    def toMxGraph(self):
        c = mxCell(
            value=self.name,
            id=self.getMxGraphId(),
            style="rounded=0;whiteSpace=wrap;html=1;",
            parent="1", vertex="1")
        c.append(self.geometry.toMxGraph())
        return c

    def toJson(self):
        return {"name": self.name,
                "id": self.id,
                "isExternalPort": False,
                "geometry": self.geometry.toJson(),
                "inputs":  [i.toJson()
                            for i in self.inputs],
                "outputs": [o.toJson()
                            for o in self.outputs]
                }


class LayoutExternalPort(LayoutUnit):
    def __init__(self, id_ctx: LayoutIdCtx, intf):
        super(LayoutExternalPort, self).__init__(
            id_ctx, intf,
            intf._name, intf.__class__.__name__)
        self.add_port(intf, reverse_dir=True)
        self.direction = intf._direction

    def toMxGraph(self):
        c = mxCell(id=self.getMxGraphId(),
                   value=self.name,
                   style="rounded=0;whiteSpace=wrap;html=1;",
                   vertex="1",
                   parent="1")
        c.append(self.geometry.toMxGraph())
        return c

    def toJson(self):
        j = super(LayoutExternalPort, self).toJson()
        j["direction"] = DIRECTION_to_str[DIRECTION.opposite(
            INTF_DIRECTION.asDirection(self.direction))]
        j["isExternalPort"] = True
        return j


class LayoutNet():
    def __init__(self, id_ctx: LayoutIdCtx,
                 signal: RtlSignal,
                 name=None):

        self.id = id_ctx.register(signal, self)
        self.name = name
        self.source = None
        self.endpoints = None

    def getMxGraphId(self):
        return str(self.id + 2)

    def toMxGraph(self):
        for ep in self.endpoints:
            srcX, srcY, srcId = self.source.getMxGraphId()
            dstX, dstY, dstId = ep.getMxGraphId()
            assert srcX >= 0.5, self.source.name
            srcX = 0
            assert dstX < 0.5, ep.name
            dstX = 1
            c = mxCell(
                id=self.getMxGraphId(),
                style=("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;" +
                       "exitX=%f;exitY=%f;entryX=%f;entryY=%f;" % (dstX, dstY, srcX, srcY) +
                       "jettySize=auto;orthogonalLoop=1;"),
                edge="1",
                parent="1",
                source=srcId,
                target=dstId,
            )
            c.append(etree.Element("mxGeometry", {
                     "relative": "1", "as": "geometry"}))
            yield c

    def toJson(self):
        j = {}
        if self.name:
            j['name'] = self.name
        j['source'] = self.source.id
        j['endpoints'] = list(map(lambda t: t.id, self.endpoints))

        return j


class Layout():
    def __init__(self):
        self.nets = []
        self.nodes = []
        self.id_ctx = LayoutIdCtx()

    def add_stm_as_unit(self, stm: HdlStatement) -> LayoutUnit:
        u = LayoutUnit(self.id_ctx, stm, stm.__class__.__name__,
                       stm.__class__.__name__)
        dummy_obj = object()
        u.outputs.append(LayoutPort(self.id_ctx, dummy_obj,
                                    u, 0, "out", INTF_DIRECTION.MASTER))
        dummy_obj = object()
        u.inputs.append(LayoutPort(self.id_ctx, dummy_obj,
                                   u, 0, "in", INTF_DIRECTION.SLAVE))
        self.nodes.append(u)
        return u

    def add_unit(self, u: Unit) -> LayoutUnit:
        n = LayoutUnit.fromIntfUnit(self.id_ctx, u)
        self.nodes.append(n)
        return n

    def add_port(self, intf: Interface) -> LayoutExternalPort:
        n = LayoutExternalPort(self.id_ctx, intf)
        self.nodes.append(n)
        return n

    def register_net(self, s: RtlSignal) -> LayoutNet:
        n = LayoutNet(self.id_ctx, s, name=s.name)
        self.nets.append(n)
        return n

    def resolveGeometry(self) -> None:
        offset = 0
        for n in self.nodes:
            n.updateGeometry(offset, 0)
            offset += 200

    def toMxGraph(self) -> etree.Element:
        gm = etree.Element("mxGraphModel", {
            "dx": "0",
            "dy": "0",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            # "pageWidth":"0",
            # "pageHeight":"0"
            "background": "#ffffff",
            "math": "0",
            "shadow": "0"
        })
        root = etree.Element("root")
        gm.append(root)
        topCell = mxCell(id="0")
        mainCell = mxCell(id="1", parent="0")
        root.extend([topCell, mainCell])

        for n in self.nets:
            for l in n.toMxGraph():
                root.append(l)

        for n in self.nodes:
            root.append(n.toMxGraph())

        return gm

    def toJson(self):
        # nets = sorted(nets , key=lambda x : x.name)
        return {"nodes": [n.toJson() for n in self.nodes],
                "nets": [n.toJson() for n in self.nets]}


def getParentUnit(intf):
    while isinstance(intf._parent, Interface):
        intf = intf._parent

    return intf._parent


def Unit_to_Layout(u):
    toRtl(u)
    la = Layout()

    # create subunits
    for su in u._units:
        la.add_unit(su)

    for stm in u._ctx.statements:
        la.add_stm_as_unit(stm)

    # create ports and nets
    for s in u._ctx.signals:
        if not s.hidden:
            la.register_net(s)
            if hasattr(s, "_interface"):
                intf = s._interface
                if intf._isExtern and getParentUnit(intf) is u:
                    la.add_port(s._interface)

    # create
    o_to_l = la.id_ctx.orig_to_layout
    for s in u._ctx.signals:
        if not s.hidden:
            n = o_to_l[s]
            assert len(s.drivers) == 1, s
            for stm in s.drivers:
                la_stm = o_to_l[stm]
                assert n.source is None
                if isinstance(stm, PortItem):
                    n.source = la_stm
                else:
                    n.source = la_stm.outputs[0]

            eps = n.endpoints = []
            for stm in s.endpoints:
                la_stm = o_to_l[stm]
                if isinstance(stm, PortItem):
                    eps.append(la_stm)
                else:
                    eps.append(la_stm.inputs[0])

    la.resolveGeometry()

    # nets = sorted(nets , key=lambda x : x.name)
    return la


if __name__ == "__main__":
    import os
    from hwtLib.samples.hierarchy.simpleSubunit import SimpleSubunit
    u = SimpleSubunit()
    s = Unit_to_Layout(u)
    # print(s.toJson())
    with open(os.path.expanduser("~/test.xml"), "wb") as f:
        s = etree.tostring(s.toMxGraph())
        f.write(s)
        print(s)
