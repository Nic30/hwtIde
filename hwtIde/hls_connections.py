from connectionsJsonObj import Layout
from hwt.synthesizer.utils import toRtl


def serializeUnit(u):
    toRtl(u)
    la = Layout()
    for su in u._units:
        la.add_unit(su)

    for s in u._ctx.signals:
        if hasattr(s, "_interface") and s._interface._isExtern:
            # [TODO] check if it is extern port of this unit or subunit
            la.add_port(s._interface)

        if s.endpoints:
            la.add_net(s)
    la.resolveGeometry()

    # nets = sorted(nets , key=lambda x : x.name)
    return la.toJson()
