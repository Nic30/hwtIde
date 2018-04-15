from flask import render_template, request, jsonify
from flask.blueprints import Blueprint
import glob
from importlib import import_module
import json
import os
import sys

from elkContainer.idStore import ElkIdStore
from fromHwtToElk.convertor import Unit_to_LNode
from fsEntry import FSEntry
from hwtLib.tests.synthesizer.interfaceLevel.subunitsSynthesisTC import synthesised
from json_resp import jsonResp
from hwt.synthesizer.dummyPlatform import DummyPlatform
from hwt.hdl.assignment import Assignment
from hwt.hdl.operator import isConst
from hwt.hdl.types.slice import Slice
from hwt.code import Concat


WORKSPACE_DIR = "../../hwtLib/hwtLib/samples"
sys.path.append(WORKSPACE_DIR)

connectionsBp = Blueprint('connections', __name__,
                          template_folder='templates/hls/')


@connectionsBp.route(r'/hls/connections-save', methods=['POST'])
def connections_save():
    data = request.get_json()
    path = data["path"]
    path = os.path.join(WORKSPACE_DIR, path)
    if path.endswith(".json"):
        nodes = data["nodes"]
        nets = data["nets"]
        with open(path, mode='w') as f:
            json.dump(
                {"name": data["name"], "nodes": nodes, "nets": nets},
                f, indent=4)
        return jsonify(success=True)
    else:
        raise Exception("Not implemented")


@connectionsBp.route('/connections/')
def connections():
    return render_template('hls/connections.html')


@connectionsBp.route('/connections-elk/<module_name>/<in_module_name>')
def connections_elk(module_name, in_module_name):
    return render_template('hls/connections_elk.html',
                           MODULE_NAME=module_name,
                           IN_MODULE_NAME=in_module_name)


@connectionsBp.route('/connections-tests/')
def connections_test():
    return render_template('hls/connections_test.html')


@connectionsBp.route('/hls/connections-data-ls/')
@connectionsBp.route('/hls/connections-data-ls/<path:path>')
def connectionDataLs(path=""):
    data = []
    path = os.path.join(WORKSPACE_DIR, path)
    assert os.path.exists(path), (path, os.getcwd())
    for f in glob.glob(path + "/*"):
        data.append(FSEntry.fromFile(f))
    return jsonResp(data)


#@connectionsBp.route('/hls/connections-data/<path:path>')
# def connectionData(path):
#    # path = os.path.join(WORKSPACE_DIR, path)
#    # if path.endswith(".py"):
#    #    path = path[:-3]
#        # try:
#        #    module = importlib.reload(sys.modules[path])
#        # except KeyError:
#        #    module = importlib.import_module(path.replace("/", "."))
#
#    # from hwtLib.samples.hierarchy.netFilter import NetFilter
#    # u = NetFilter()
#
#    from hwtLib.samples.hierarchy.simpleSubunit import SimpleSubunit
#    u = SimpleSubunit()
#
#    # from hwtLib.samples.hierarchy.simpleSubunit import SimpleSubunit
#    # u = SimpleSubunit()
#    # for _ in u._toRtl():
#    #    pass
#    data = Unit_to_LNode(u)
#
#    # elif path.endswith(".json"):
#    #    with open(path) as f:
#    #        data = f.read()
#    # else:
#    #    raise Exception("not implemented")
#    return jsonResp(data)


def indexedAssignmentsToConcatenation(netlist):
    signalsToReduce = set()

    for s in netlist.signals:
        if len(s.drivers) > 1:
            compatible = True
            for d in s.drivers:
                if not isinstance(d, Assignment)\
                        or len(d.indexes) != 1\
                        or not isConst(d.indexes[0]):
                    compatible = False
                    break

            if compatible:
                signalsToReduce.add(s)

    for s in signalsToReduce:
        inputs = []
        for d in list(s.drivers):
            i = d.indexes[0].staticEval()
            assert i.vldMask, s
            if isinstance(i._dtype, Slice):
                i = (int(i.val[0]), int(i.val[1]))
            else:
                i = int(i)
                i = (i, i + 1)
            v = d.src
            inputs.append((i, v))
            d._destroy()

        inputs.sort(key=lambda x: x[0])
        s(Concat(*map(lambda x: x[1], inputs)))


@connectionsBp.route("/hls/connections-data-elk/<module_name>/<in_module_name>")
def connectionDataElk(module_name, in_module_name):
    # get and construct target unit specified by arguments
    m = import_module(module_name)
    ucls = m
    for name in in_module_name.split("."):
        ucls = getattr(ucls, name)
    u = ucls()
    plat = DummyPlatform()
    plat.beforeHdlArchGeneration.append(indexedAssignmentsToConcatenation)
    # synthetize unit and convert it to json
    synthesised(u, plat)
    g = Unit_to_LNode(u)
    idStore = ElkIdStore()
    data = g.toElkJson(idStore)
    assert len(g.children) == idStore.nodeCnt, (len(
        g.children), idStore.nodeCnt)
    return jsonify(data)
