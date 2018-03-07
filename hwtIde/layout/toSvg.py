from itertools import chain

from layout.containers import LayoutPort, LayoutNode, Layout,\
    LayoutExternalPort, LayoutEdge, LayoutIdCtx, UNIT_HEADER_OFFSET, PORT_HEIGHT
from layout.geometry import GeometryRect
import xml.etree.ElementTree as etree


def svg_rect_from_geom(geom: GeometryRect, label=None):
    g = etree.Element("g")
    r = svg_rect(geom.x, geom.y, geom.width, geom.height)
    g.append(r)
    if label is not None:
        g.append(svg_text(geom.x + geom.width / 2,
                          # center text in the middle
                          geom.y + PORT_HEIGHT * 0.7, label))
    return g


def svg_rect(x, y, width, height):
    return etree.Element("rect", attrib={
        "style": "fill:cornflowerblue;stroke:black;stroke-width:2;",
        "x": str(x),
        "y": str(y),
        "width": str(width),
        "height": str(height)
    })


def svg_text(x, y, text):
    t = etree.Element("text", attrib={"x": str(x),
                                      "y": str(y),
                                      "fill": "black",
                                      "text-anchor": "middle"})
    t.text = text
    return t


def svg_line(points):
    p_str = " ".join("%r,%r" % p for p in points)
    return etree.Element("polyline", attrib={
        "points": p_str,
        "style": "fill:none;stroke:black;stroke-width:2",
        "marker-start": "url(#markerCircle)",
        "marker-end": "url(#markerArrow)",
    })


class ToSvg():
    def __init__(self):
        self.id_ctx = LayoutIdCtx()

        self._toSvg = {
            LayoutNode: self.LayoutNode_toSvg,
            LayoutEdge: self.LayoutEdge_toSvg,
            LayoutExternalPort: self.LayoutExternalPort_toSvg,
            Layout: self.Layout_toSvg,
        }

    def LayoutPort_coordinates(self, lp):
        p = lp.parent.geometry
        g = lp.geometry
        is_out = g.x >= p.x + p.width / 2
        if is_out:
            x = p.x + p.width
        else:
            x = p.x

        y = (g.y + PORT_HEIGHT / 2)

        return x, y

    def getSvgId(self, obj):
        return str(self.id_ctx[obj] + 2)

    def LayoutNode_toSvg(self, lu: LayoutNode):
        n = svg_rect_from_geom(lu.geometry, label=lu.name)

        for lp in chain(lu.inputs, lu.outputs):
            for obj in self.LayoutPort_toSvg(lp):
                n.append(obj)
        yield n

    def LayoutPort_toSvg(self, lp: LayoutPort):
        yield svg_rect_from_geom(lp.geometry, label=lp.name)

    def LayoutExternalPort_toSvg(self, lep: LayoutExternalPort):
        yield svg_rect_from_geom(lep.geometry, label=lep.name)

    def LayoutEdge_toSvg(self, ln: LayoutNode):
        if ln.reversed:
            _src = ln.dst
            _dst = ln.src
        else:
            _src = ln.src
            _dst = ln.dst

        srcX, srcY = self.LayoutPort_coordinates(_src)
        dstX, dstY = self.LayoutPort_coordinates(_dst)
        points = [(srcX, srcY), (dstX, dstY)]
        yield svg_line(points)

    def Layout_toSvg(self, la) -> etree.Element:
        svg = etree.Element("svg", {
            # [TODO]
            "width": str(la.width),
            "height": str(la.height),
        })
        defs = etree.fromstring(
            """
            <defs>
                <marker id="markerCircle" markerWidth="8" markerHeight="8" refX="5" refY="5">
                    <circle cx="2" cy="2" r="2" style="stroke: none; fill:#000000;"/>
                </marker>
                <marker id="markerArrow" markerWidth="13" markerHeight="13"
                    refX="10" refY="6" orient="auto">
                    <path d="M2,2 L2,11 L10,6 L2,2" style="fill: #000000;" />
                </marker>
            </defs>""".replace("  ", ""))
        svg.append(defs)

        for n in la.edges:
            for l in self.toSvg(n):
                svg.append(l)

        for n in la.nodes:
            for obj in self.toSvg(n):
                svg.append(obj)

        return svg

    def toSvg(self, obj):
        yield from self._toSvg[obj.__class__](obj)
