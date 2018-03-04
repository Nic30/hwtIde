

class GeometryRect():
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class GeometryPath():
    def __init__(self, points):
        self.points = points

    def toJson(self):
        return self.points
