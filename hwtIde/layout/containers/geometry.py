

class GeometryRect():
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self):
        return "<%s, x:%f, y:%f, width:%f, height:%f>" % (
            self.__class__.__name__, self.x, self.y, self.width, self.height)


class GeometryPath():
    def __init__(self, points):
        self.points = points

    def toJson(self):
        return self.points

    def __repr__(self):
        return "<% %r>" % (self.__class__.__name__, self.points)
