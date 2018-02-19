import xml.etree.ElementTree as etree


class GeometryRect():
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def toMxGraph(self, as_="geometry"):
        return etree.Element(
            "mxGeometry",
            {"x": str(self.x),
             "y": str(self.y),
             "width": str(self.width),
             "height": str(self.height),
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
