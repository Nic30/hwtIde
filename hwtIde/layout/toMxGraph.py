from layout.containers.geometry import GeometryRect
from layout.containers.lEdge import LEdge
from layout.containers.lGraph import Layout
from layout.containers.lNode import LNode, LayoutExternalPort
from layout.containers.lPort import LPort
from layout.containers.sizeConfig import PORT_HEIGHT, UNIT_HEADER_OFFSET
import xml.etree.ElementTree as etree


class LayoutIdCtx(dict):
    # {LayoutObj: int}
    def __getitem__(self, obj):
        try:
            return dict.__getitem__(self, obj)
        except KeyError:
            pass

        return self._register(obj)

    def _register(self, obj) -> int:
        i = len(self)
        self[obj] = i
        return i


def mxCell(**kvargs):
    return etree.Element("mxCell", attrib=kvargs)


class ToMxGraph():
    def __init__(self):
        self.id_ctx = LayoutIdCtx()

        self._toMxGraph = {
            LNode: self.LNode_toMxGraph,
            LEdge: self.LEdge_toMxGraph,
            LayoutExternalPort: self.LayoutExternalPort_toMxGraph,
            Layout: self.Layout_toMxGraph,
            GeometryRect: self.GeometryRect_toMxGraph
        }

    def LPort_coordinates(self, lp):
        p = lp.getNode().geometry
        g = lp.geometry
        x_rel = (g.x - p.x) / p.width
        y_rel = (g.y - p.y + PORT_HEIGHT / 2) / p.height
        assert x_rel >= 0.0 and x_rel <= 1.0, x_rel
        assert y_rel >= 0.0 and y_rel <= 1.0, y_rel
        if x_rel >= 0.5:
            x_rel = 1
        return x_rel, y_rel

    def getMxGraphId(self, obj):
        return str(self.id_ctx[obj] + 2)

    def LNode_toMxGraph(self, lu: LNode):
        _id = self.getMxGraphId(lu)
        c = mxCell(
            value="",
            id=_id,
            style="rounded=0;whiteSpace=wrap;html=1;",
            parent="1", vertex="1")
        g = lu.geometry
        c.append(self.GeometryRect_toMxGraph(g))
        yield c

        label = mxCell(
            id=self.getMxGraphId((lu, lu.name)),
            value=lu.name,
            style=("text;html=1;resizable=0;points=[];autosize=1;align=left;"
                   "verticalAlign=top;spacingTop=0;"),
            vertex="1",
            parent=_id,
        )
        lg = GeometryRect(0, 0, g.width, UNIT_HEADER_OFFSET)
        label.append(self.GeometryRect_toMxGraph(lg))
        yield label

        for lp in lu.iterPorts():
            yield from self.LPort_toMxGraph(lp, _id, g)

    def LPort_toMxGraph(self, lp: LPort, parentId, parentGeom):
        p = mxCell(
            value=lp.name,
            id=self.getMxGraphId(lp),
            style="rounded=0;whiteSpace=wrap;html=1;",
            parent=parentId, vertex="1")
        g = lp.geometry
        g = GeometryRect(g.x - parentGeom.x, g.y -
                         parentGeom.y, g.width, g.height)
        p.append(self.GeometryRect_toMxGraph(g))
        yield p

    def LayoutExternalPort_toMxGraph(self, lep):
        if len(lep.west) + len(lep.east) == 1:
            c = mxCell(id=self.getMxGraphId(lep),
                       value=lep.name,
                       style="rounded=0;whiteSpace=wrap;html=1;",
                       vertex="1",
                       parent="1")
            c.append(self.GeometryRect_toMxGraph(lep.geometry))

            yield c
        else:
            yield from self.LNode_toMxGraph(lep)

    def LEdge_toMxGraph(self, e: LEdge):
        if e.reversed:
            _src = e.dst
            _dst = e.src
        else:
            _src = e.src
            _dst = e.dst

        srcId = self.getMxGraphId(_src.getNode())
        srcX, srcY = self.LPort_coordinates(_src)
        dstId = self.getMxGraphId(_dst.getNode())
        dstX, dstY = self.LPort_coordinates(_dst)

        c = mxCell(
            id=self.getMxGraphId(e),
            style=("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;" +
                   "exitX=%f;exitY=%f;entryX=%f;entryY=%f;"
                   % (srcX, srcY, dstX, dstY) +
                   "jettySize=auto;orthogonalLoop=1;"),
            edge="1",
            parent="1",
            source=srcId,
            target=dstId,
        )
        c.append(etree.Element("mxGeometry", {
                 "relative": "1", "as": "geometry"}))
        yield c

    def Layout_toMxGraph(self, la) -> etree.Element:
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

        for n in la.nodes:
            for obj in self.toMxGraph(n):
                root.append(obj)

        for n in la.edges:
            for l in self.toMxGraph(n):
                root.append(l)

        return gm

    def GeometryRect_toMxGraph(self, g, as_="geometry"):
        return etree.Element(
            "mxGeometry",
            {"x": str(g.x),
             "y": str(g.y),
             "width": str(g.width),
             "height": str(g.height),
             "as": as_})

    def toMxGraph(self, obj):
        yield from self._toMxGraph[obj.__class__](obj)
