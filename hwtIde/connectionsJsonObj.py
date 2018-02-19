from flask.wrappers import Response
from itertools import chain
import json
import os
from stat import S_ISDIR
import time
from typing import List

from hwt.hdl.constants import INTF_DIRECTION, DIRECTION, DIRECTION_to_str
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
import xml.etree.ElementTree as etree


UNIT_HEADER_OFFSET = 20
PORT_HEIGHT = 20
PORT_X_PADDING = 20
UNIT_PADDING = 5


def width_of_str(s):
    return len(s) * 5


class IdCtx(dict):
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


def jsonResp(data):
    return Response(response=json.dumps(
        data,
        default=_defaultToJson),
        status=200, mimetype="application/json")


def _defaultToJson(obj):
    if hasattr(obj, "toJson"):
        return obj.toJson()
    return obj.__dict__


class GeometryRect():
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def toMxGraph(self, as_="geometry"):
        return etree.Element(
            "mxGeometry",
            {"x": self.x,
             "y": self.y,
             "width": self.width,
             "height": self.height,
             "as": as_})

    def toJson(self):
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }


class GeometryPath():
    def __init__(self, points):
        self.points = points

    def toJson(self):
        return self.points


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

    def __init__(self, id_ctx: IdCtx, parent: "LayoutUnit",
                 on_parent_index: int, name: str, direction):
        self.parent = parent
        self.on_parent_index = on_parent_index
        self.name = name
        self.direction = direction
        self.geometry = None
        self.id = id_ctx.register(self)

    def updateGeometry(self, x_offset, y_offset, width):
        y = y_offset + UNIT_HEADER_OFFSET + self.on_parent_index * PORT_HEIGHT
        self.geometry = GeometryRect(x_offset, y, width, PORT_HEIGHT)

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

    def __init__(self, id_ctx: IdCtx, unit: Unit, name: str, class_name: str):
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

    def add_port(self, intf: Interface):
        if intf._direction == INTF_DIRECTION.MASTER:
            portArr = self.outputs
        elif intf._direction == INTF_DIRECTION.SLAVE:
            portArr = self.inputs
        else:
            raise Exception()

        p = LayoutPort(self._id_ctx, self,
                       len(portArr), intf._name,
                       intf._direction)
        portArr.append(p)

    @classmethod
    def fromIntfUnit(cls, id_ctx: IdCtx, u: Unit):
        self = cls(id_ctx, u, u._name, u.__class__.__name__)
        for intf in u._interfaces:
            self.add_port(intf)

        return self

    def getMxGraphId(self):
        raise self.id + 2

    def toMxGraph(self):
        c = mxCell(
            value=self.name,
            style="rounded=0;whiteSpace=wrap;html=1;",
            parent=1, vertex=1)
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
    def __init__(self, id_ctx: IdCtx, intf):
        super(LayoutExternalPort, self).__init__(
            id_ctx, intf._sigInside,
            intf._name, intf.__class__.__name__)
        self.add_port(intf)
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
    def __init__(self, id_ctx: IdCtx,
                 signal: RtlSignal,
                 source: LayoutPort,
                 endpoints: List[LayoutPort], name=None):
        self.id = id_ctx.register(signal, self)
        self.name = name
        self.source = source
        self.endpoints = endpoints

    def getMxGraphId(self):
        return self.id + 2

    def toMxGraph(self):
        for ep in self.endpoints:
            srcX, srcY, srcId = self.source.getMxGraphId()
            dstX, dstY, dstId = ep.getMxGraphId()
            c = mxCell(
                "mxCell",
                {
                    "id": self.getMxGraphId(),
                    "style": ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;" +
                              "exitX=%f;exitY=%f;entryX=%f;entryY=%f;" % (dstX, dstY, srcX, srcY) +
                              "jettySize=auto;orthogonalLoop=1;"),
                    "edge": "1",
                    "parent": "1",
                    "source": srcId,
                    "target": dstId,
                })
            yield c

    def toJson(self):
        j = {}
        if self.name:
            j['name'] = self.name
        j['source'] = self.source.id
        j['targets'] = list(map(lambda t: t.id, self.targets))

        return j


def mxCell(**kvargs):
    return etree.Element("mxCell", attrib=kvargs)


class Layout():
    def __init__(self):
        self.nets = []
        self.nodes = []
        self.id_ctx = IdCtx()

    def add_unit(self, u: Unit):
        n = LayoutUnit.fromIntfUnit(self.id_ctx, u)
        self.nodes.append(n)

    def add_port(self, intf: Interface):
        n = LayoutExternalPort(self.id_ctx, intf)
        self.nodes.append(n)

    def add_net(self, s: RtlSignal):
        o_to_l = self.id_ctx.orig_to_layout
        n = LayoutNet(self.id_ctx,
                      o_to_l[s],
                      [o_to_l[e] for e in s.endpoints],
                      name=s.name)
        self.nets.append(n)

    def resolveGeometry(self):
        offset = 0
        for n in self.nodes:
            n.updateGeometry(offset, 0)
            offset += 200

    def toMxGraph(self):
        gm = etree.Element("mxGraphModel")
        root = etree.Element("root")
        gm.append(root)
        topCell = mxCell(id=0)
        mainCell = mxCell(id=1, parent=0)
        root.extend([topCell, mainCell])

        for n in self.nodes:
            gm.append(n.toMxGraph())

    def toJson(self):
        # nets = sorted(nets , key=lambda x : x.name)
        return {"nodes": self.nodes,
                "nets": self.nets}


class FSEntry():
    def __init__(self, name, isGroup):
        self.isGroup = isGroup
        self.name = name
        self.size = ""
        self.type = ""
        self.dateModified = None
        self.children = []

    @classmethod
    def fromFile(cls, fileName):
        st = os.stat(fileName)

        self = cls(os.path.basename(fileName), S_ISDIR(st.st_mode))
        self.size = st.st_size
        # "%Y/%m/%d  %H:%M:%S"
        self.dateModified = time.strftime(
            "%Y/%m/%d  %H:%M:%S", time.gmtime(st.st_ctime))

        return self

    def toJson(self):
        return {"group": self.isGroup,
                "data": {"name": self.name,
                         "size": self.size,
                         "type": self.type,
                         "dateModified": self.dateModified},
                "children": []
                }
