from hwt.hdl.constants import DIRECTION_to_str, DIRECTION, INTF_DIRECTION


class ToJson():
    def LPort_toJson(self, lp):
        return {"id": lp.id,
                "geometry": self.toJson(lp.geometry),
                "name": lp.name}

    def LNode_toJson(self, lu):
        toJson = self.toJson
        return {"name": lu.name,
                "id": lu.id,
                "isExternalPort": False,
                "geometry": toJson(lu.geometry),
                "inputs":  [toJson(i)
                            for i in self.inputs],
                "outputs": [toJson(o)
                            for o in self.outputs]
                }

    def LayoutExternalPort_toJson(self, lep):
        j = self.LNode_toJson(lep)
        j["direction"] = DIRECTION_to_str[DIRECTION.opposite(
            INTF_DIRECTION.asDirection(lep.direction))]
        j["isExternalPort"] = True
        return j

    def LayoutNet_toJson(self, ln):
        j = {}
        if ln.name:
            j['name'] = ln.name
        j['source'] = ln.source.id
        j['endpoints'] = list(map(lambda t: t.id, self.endpoints))

        return j

    def Layout_toJson(self, la):
        # nets = sorted(nets , key=lambda x : x.name)
        toJson = self.toJson
        return {"nodes": [toJson(n) for n in la.nodes],
                "nets": [toJson(n) for n in la.nets]}

    def GeometryRect_toJson(self, gr):
        return {
            "x": gr.x,
            "y": gr.y,
            "width": gr.width,
            "height": gr.height
        }
