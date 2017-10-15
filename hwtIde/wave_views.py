from flask.blueprints import Blueprint
from flask.templating import render_template
from flask import abort, jsonify, request
from hwtLib.handshaked.fifo import HandshakedFifo
from hwt.interfaces.std import Handshaked
from hwt.simulator.shortcuts import simPrepare
from hwt.simulator.hdlSimulator import HdlSimulator
from hwt.simulator.hdlSimConfig import HdlSimConfig
from hwt.hdlObjects.types.boolean import Boolean
from hwt.hdlObjects.types.bits import Bits
from hwt.hdlObjects.types.enum import Enum
from hwt.hdlObjects.constants import Time

waveBp = Blueprint('wave',
                   __name__,
                   template_folder='templates/wave/')


class WebHdlSimConfig(HdlSimConfig):
    supported_type_classes = (Boolean, Bits, Enum)

    def __init__(self):
        super().__init__()
        self.logPropagation = False
        self.logApplyingValues = False
        self.collectedWave = {}
        # unit :  signal | unit
        # signal : None

    def dumpVal(self, value, typ):
        v = value.val
        vld = value.vldMask
        # w = typ.bit_length()
        if vld != typ._allMask:
            return 'x'
        else:
            return "%x" % v

    def initUnitSignals(self, unit):
        for se in unit._cntx.signals:
            if isinstance(se._dtype, self.supported_type_classes):
                d = self.collectedWave.setdefault(se, [])
                nextVal = se._val
                d.append((0, self.dumpVal(nextVal, se._dtype)))

        for u in unit._units:
            self.initUnitSignals(u)

    def beforeSim(self, simulator, synthesisedUnit):
        self.initUnitSignals(synthesisedUnit)

    def logChange(self, nowTime, sig, nextVal):
        """
        This method is called for every value change of any signal.
        """
        if isinstance(sig._dtype, Bits):
            d = self.collectedWave.setdefault(sig, [])
            d.append((nowTime // Time.ns, self.dumpVal(nextVal, sig._dtype)))


@waveBp.route('/wave-test/')
def connections_test():
    return render_template('wave_test.html')


@waveBp.route("/wave-data/", methods=["POST", 'GET'])
def wave_data():
    # if not request.json:
    #    abort(400)
    # query = request.json
    # print(query)

    waveRange = [0, 200 * Time.ns]

    u = HandshakedFifo(Handshaked)

    u.DEPTH.set(8)
    u, model, procs = simPrepare(u)
    sim = HdlSimulator()

    u.dataIn._ag.data = [1, 2, 3, 4, 5, 6]

    sim.config = WebHdlSimConfig()
    sim.simUnit(model,
                time=waveRange[1] + 1,
                extraProcesses=procs)
    data = []
    for sig, wave in sorted(sim.config.collectedWave.items(), key=lambda x: x[0].name):
        t = sig._dtype
        w = t.bit_length()
        if w == 1:
            typeName = 'bit'
        else:
            typeName = 'bits'

        data.append((sig.name,
                     {'name': typeName, 'width': w},
                     wave))

    return jsonify(data)
