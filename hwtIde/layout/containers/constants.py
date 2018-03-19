from enum import Enum
from hwt.hdl.constants import INTF_DIRECTION


class NodeType(Enum):
    # a normal node is created from a node of the original graph.
    NORMAL = 0
    # a dummy node created to split a long edge.
    LONG_EDGE = 1
    # a node representing an external port.
    EXTERNAL_PORT = 2
    # a dummy node created to cope with ports at the northern or southern side.
    NORTH_SOUTH_PORT = 3
    # a dummy node to represent a mid-label on an edge.
    LABEL = 4
    # a dummy node originating from a node spanning multiple layers.
    BIG_NODE = 5
    # a dummy node representing a breaking point used to 'wrap' graphs.
    BREAKING_POINT = 6


class PortType(Enum):
    INPUT = 0
    OUTPUT = 1

    @classmethod
    def from_dir(cls, direction):
        if direction == INTF_DIRECTION.SLAVE:
            return cls.INPUT
        elif direction == INTF_DIRECTION.MASTER:
            return cls.OUTPUT
        else:
            raise ValueError(direction)

    @classmethod
    def opposite(cls, t):
        if t == cls.INPUT:
            return cls.OUTPUT
        elif t == cls.OUTPUT:
            return cls.INPUT
        else:
            raise ValueError(t)


class PortSide(Enum):
    EAST = 0
    WEST = 1
    SOUTH = 2
    NORTH = 3

    @staticmethod
    def opposite(side):
        d = {PortSide.EAST: PortSide.WEST,
             PortSide.WEST: PortSide.EAST,
             PortSide.SOUTH: PortSide.NORTH,
             PortSide.NORTH: PortSide.SOUTH}
        return d[side]


class PortConstraints(Enum):
    # Undefined constraints.
    UNDEFINED = 0
    # All ports are free.
    FREE = 1
    # The side is fixed for each port.
    FIXED_SIDE = 2
    # The side is fixed for each port, and the order of ports is fixed for
    # each side.
    FIXED_ORDER = 3
    # The side is fixed for each port, the order or ports is fixed for each side and
    # the relative position of each port must be preserved. That means if the node is
    # resized by factor x, the port's position must also be scaled by x.
    FIXED_RATIO = 4
    # The exact position is fixed for each port.
    FIXED_POS = 5

    def isPosFixed(self):
        """
        Returns whether the position of the ports is fixed. Note that this is not true
        if port ratios are fixed.

        @return true if the position is fixed
        """
        return self == PortConstraints.FIXED_POS

    def isRatioFixed(self):
        """
        Returns whether the ratio of port positions is fixed. Note that this is not true
        if the port positions are fixed.

        @return true if the ratio is fixed
        """
        return self == PortConstraints.FIXED_RATIO

    def isOrderFixed(self):
        """
        Returns whether the order of ports is fixed.

        @return true if the order of ports is fixed
        """
        return (self == PortConstraints.FIXED_ORDER
                or self == PortConstraints.FIXED_RATIO
                or self == PortConstraints.FIXED_POS)

    def isSideFixed(self):
        """
        Returns whether the sides of ports are fixed.

        @see PortSide
        @return true if the port sides are fixed
        """
        return self == PortConstraints.FREE and self != PortConstraints.UNDEFINED


class EdgeRouting(Enum):
    # undefined edge routing.
    UNDEFINED = 0
    # polyline edge routing.
    POLYLINE = 1
    # orthogonal edge routing.
    ORTHOGONAL = 2
    # splines edge routing.
    SPLINES = 4
