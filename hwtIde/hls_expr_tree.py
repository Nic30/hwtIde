from flask.blueprints import Blueprint
from flask.json import jsonify
from flask.templating import render_template

from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.synthesizer.utils import toRtl
from hwtHls.codeObjs import ReadOpPromise, HlsOperation, WriteOpPromise,\
    HlsConst
from hwtHls.platform.virtual import VirtualHlsPlatform
from importlib import import_module
from hwt.serializer.verilog.serializer import VerilogSerializer


hlsExprTreeBp = Blueprint('hlsExprTree',
                          __name__,
                          template_folder='templates/hls/expr_tree/')


@hlsExprTreeBp.route('/expr-tree/<module_name>/<in_module_name>')
def expr_tree(module_name, in_module_name):
    return render_template('expr_tree.html',
                           MODULE_NAME=module_name,
                           IN_MODULE_NAME=in_module_name)


class WebDumpHlsPlatform(VirtualHlsPlatform):
    """
    Wrapper for HLS target platform which allows to acess
    results of HLS synthesis
    """

    def __init__(self):
        super(WebDumpHlsPlatform, self).__init__()
        self.hls = []

    def onHlsInit(self, hls):
        self.hls.append(hls)


def schedulizationGraphAsJSON(hls):
    scheduler = hls.scheduler
    nodes = [None for _ in range(len(hls.nodes))]
    edges = []
    nodeIds = {}
    for nodeId, node in enumerate(hls.nodes):
        nodeIds[node] = nodeId

    for _nodes in scheduler.schedulization:
        for node in _nodes:
            nodeId = nodeIds[node]
            if isinstance(node, ReadOpPromise):
                label = getSignalName(node.intf)
            elif isinstance(node, HlsOperation):
                label = node.operator.id
            elif isinstance(node, WriteOpPromise):
                label = getSignalName(node.where)
            elif isinstance(node, HlsConst):
                label = VerilogSerializer.asHdl(node.val, None)
            else:
                raise TypeError(node)

            _node = {"id": nodeId,
                     "label": label,
                     "level": (node.asap_start + node.asap_end) / 2
                     }
            nodes[nodeId] = _node
            for usedBy in node.usedBy:
                edge = {"source": nodeId,
                        "target": nodeIds[usedBy]
                        }
                edges.append(edge)

    return {
        "nodes": nodes,
        "edges": edges,
    }


@hlsExprTreeBp.route("/expr-tree-data/<module_name>/<in_module_name>")
def expr_tree_data(module_name, in_module_name):
    # get and construct target unit specified by arguments
    m = import_module(module_name)
    ucls = m
    for name in in_module_name.split("."):
        ucls = getattr(ucls, name)
    u = ucls()

    # synthetize unit and collect expr tree data
    p = WebDumpHlsPlatform()
    toRtl(u, targetPlatform=p)
    hls = p.hls[0]
    data = schedulizationGraphAsJSON(hls)

    return jsonify(data)
