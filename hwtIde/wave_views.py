from flask import abort, jsonify, request
from flask.blueprints import Blueprint
from flask.templating import render_template
from typing import Union

from hwt.hdl.constants import Time
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.bool import HBool
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.std import Handshaked
from hwt.simulator.hdlSimConfig import HdlSimConfig
from hwt.simulator.hdlSimulator import HdlSimulator
from hwt.simulator.shortcuts import simPrepare
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.synthesizer.unit import Unit
from hwtLib.handshaked.fifo import HandshakedFifo
from json_resp import jsonResp
from pyDigitalWaveTools.vcd.parser import VcdParser
from pyDigitalWaveTools.vcd.common import VcdVarInfo, VcdVarScope


waveBp = Blueprint('wave',
                   __name__,
                   template_folder='templates/wave/')


class WebHdlSimConfig(HdlSimConfig):
    supported_type_classes = (HBool, Bits, HEnum)

    def __init__(self):
        self.logPropagation = False
        self.logApplyingValues = False
        self._scope = None
        self._signals = {}
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

    def registerSignal(self, s):
        if isinstance(s._dtype, self.supported_type_classes):
            name = getSignalName(s)
            parent = self._scope
            if isinstance(s, Interface):
                s = s._sig

            sInfo = VcdVarInfo(
                None, name, s._dtype.bit_length(), "wire", self._scope)

            if parent is None:
                self._signals[name] = sInfo
            else:
                parent.children[name] = sInfo

            d = self.collectedWave[s] = sInfo.data
            nextVal = s._val
            d.append((0, self.dumpVal(nextVal, s._dtype)))

            return sInfo

    def registerInterfaces(self, intf: Union[Interface, Unit]):
        if hasattr(intf, "_interfaces") and intf._interfaces:
            parent = self._scope
            name = intf._name
            info = VcdVarScope(name, parent)
            self._scope = info
            for chIntf in intf._interfaces:
                self.registerInterfaces(chIntf)
            self._scope = parent
            if parent is None:
                self._signals[name] = info
            else:
                parent.children[name] = info
            return info
        else:
            return self.registerSignal(intf)

    def initUnitSignals(self, unit):
        parentScope = self._scope
        self._scope = self.registerInterfaces(unit)
        for s in unit._ctx.signals:
            if s not in self.collectedWave:
                self.registerSignal(s)

        for u in unit._units:
            self.initUnitSignals(u)

        self._scope = parentScope

    def beforeSim(self, simulator, synthesisedUnit):
        self.initUnitSignals(synthesisedUnit)

    def logChange(self, nowTime, sig, nextVal):
        """
        This method is called for every value change of any signal.
        """
        if isinstance(sig._dtype, Bits):
            d = self.collectedWave[sig]
            d.append((nowTime // Time.ns, self.dumpVal(nextVal, sig._dtype)))


@waveBp.route('/wave-test/')
def connections_test():
    return render_template('wave_test.html')


def wave_data_vcd():
    fName = "/home/nic30/Documents/workspace/hwtLib/hwtLib/amba/axiLite_comp/tmp/AxiRegTC_test_write.vcd"
    with open(fName) as vcd_file:
        vcd = VcdParser()
        vcd.parse(vcd_file)
        return jsonResp({n: s.toJson() for n, s in vcd.signals.items()})


@waveBp.route("/wave-data/", methods=["POST", 'GET'])
#@waveBp.route("/wave-data/", methods=["POST", 'GET'])
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

    u.dataIn._ag.data.extend([1, 2, 3, 4, 5, 6])

    sim.config = WebHdlSimConfig()
    sim.simUnit(model,
                until=waveRange[1] + 1,
                extraProcesses=procs)

    return jsonify({n: v.toJson() for n, v in sim.config._signals.items()})
