from layout.containers import LayoutPort, LayoutNode, Layout,\
    LayoutExternalPort, LayoutEdge, LayoutIdCtx, PORT_HEIGHT
from layout.geometry import GeometryRect
import xml.etree.ElementTree as etree


EXTERNAL_PORT_FILL = "mediumpurple"
COMPONENT_FILL = "cornflowerblue"


def svg_rect_from_geom(geom: GeometryRect, label=None, fill=COMPONENT_FILL):
    g = etree.Element("g")
    r = svg_rect(geom.x, geom.y, geom.width, geom.height, fill=fill)
    g.append(r)
    if label is not None:
        g.append(svg_text(geom.x + geom.width / 2,
                          # center text in the middle
                          geom.y + PORT_HEIGHT * 0.7, label))
    return g


def svg_rect(x, y, width, height, fill=COMPONENT_FILL):
    return etree.Element("rect", attrib={
        "style": "fill:%s;stroke:black;stroke-width:2;" % fill,
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


def svg_line(points, stroke="black"):
    p_str = " ".join("%r,%r" % p for p in points)
    return etree.Element("polyline", attrib={
        "points": p_str,
        "style": "fill:none;stroke:%s;stroke-width:2" % stroke,
        #"marker-start": "url(#markerCircle)",
        "marker-end": "url(#markerArrow)",
    })


class ToSvg():
    def __init__(self, reversed_edge_stroke="black"):
        self.reversed_edge_stroke = reversed_edge_stroke
        self.id_ctx = LayoutIdCtx()

        self._toSvg = {
            LayoutNode: self.LayoutNode_toSvg,
            LayoutEdge: self.LayoutEdge_toSvg,
            LayoutExternalPort: self.LayoutExternalPort_toSvg,
            Layout: self.Layout_toSvg,
        }

    def LayoutPort_coordinates(self, lp: LayoutPort):
        p = lp.getNode().geometry
        g = lp.geometry
        is_on_right = g.x >= p.x + p.width / 2
        if is_on_right:
            x = p.x + p.width
        else:
            x = p.x

        y = (g.y + PORT_HEIGHT / 2)

        return x, y

    def getSvgId(self, obj):
        return str(self.id_ctx[obj] + 2)

    def LayoutNode_toSvg(self, lu: LayoutNode, fill=COMPONENT_FILL):
        n = svg_rect_from_geom(lu.geometry, label=lu.name, fill=fill)

        for lp in lu.iterPorts():
            for obj in self.LayoutPort_toSvg(lp):
                n.append(obj)
        yield n

    def LayoutPort_toSvg(self, lp: LayoutPort):
        yield svg_rect_from_geom(lp.geometry, label=lp.name)

    def LayoutExternalPort_toSvg(self, lep: LayoutExternalPort):
        if len(lep.left) + len(lep.right) == 1:
            yield svg_rect_from_geom(lep.geometry,
                                     label=lep.name,
                                     fill=EXTERNAL_PORT_FILL)
        else:
            yield from self.LayoutNode_toSvg(lep, fill=EXTERNAL_PORT_FILL)

    def LayoutEdge_toSvg(self, ln: LayoutNode):
        if ln.reversed:
            _src = ln.dst
            _dst = ln.src
            stroke = self.reversed_edge_stroke
        else:
            _src = ln.src
            _dst = ln.dst
            stroke = "black"

        srcX, srcY = self.LayoutPort_coordinates(_src)
        dstX, dstY = self.LayoutPort_coordinates(_dst)
        points = [(srcX, srcY), (dstX, dstY)]

        yield svg_line(points, stroke=stroke)

    def Layout_toSvg(self, la: Layout) -> etree.Element:
        svg = etree.Element("svg", {
            "width": str(la.width),
            "height": str(la.height),
        })
        defs = etree.fromstring(
            """
            <defs>
                <marker id="markerCircle" markerWidth="8" markerHeight="8" refX="5" refY="5">
                    <circle cx="2" cy="2" r="2" style="stroke: none; fill:#000000;"/>
                </marker>
                <marker id="markerArrow" viewBox="0 0 10 10" refX="1" refY="5" 
                      markerUnits="strokeWidth" markerWidth="5" markerHeight="5"
                      orient="auto">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/>
                </marker>
            </defs>""".replace("  ", ""))
        svg.append(defs)

        for n in la.nodes:
            for obj in self.toSvg(n):
                svg.append(obj)

        for n in la.edges:
            for l in self.toSvg(n):
                svg.append(l)

        return svg

    def toSvg(self, obj):
        yield from self._toSvg[obj.__class__](obj)
