from flask.blueprints import Blueprint
from flask.json import jsonify
from flask.templating import render_template
from hwtHls.platform.virtual import VirtualHlsPlatform
from hwtHls.samples.mac import HlsMAC_example
from hwt.synthesizer.utils import toRtl
from hwtHls.codeObjs import ReadOpPromise, HlsOperation, WriteOpPromise
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName


hlsExprTreeBp = Blueprint('hlsExprTree',
                          __name__,
                          template_folder='templates/hls/expr_tree/')


@hlsExprTreeBp.route('/expr-tree-test/')
def expr_tree_test():
    return render_template('expr_tree.html')


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

    for level, _nodes in enumerate(scheduler.schedulization):
        for node in _nodes:
            nodeId = nodeIds[node]
            if isinstance(node, ReadOpPromise):
                label = getSignalName(node.intf)
            elif isinstance(node, HlsOperation):
                label = node.operator.id
            elif isinstance(node, WriteOpPromise):
                label = getSignalName(node.where)
            else:
                raise TypeError(node)

            _node = {"id": nodeId,
                     "label": label,
                     "level": (node.asap_start + node.asap_end) / 2}
            nodes[nodeId] = _node
            for usedBy in node.usedBy:
                edge = {"source": nodeId,
                        "target": nodeIds[usedBy] & 0xffff}
                edges.append(edge)

    data = {
        "nodes": nodes,
        "edges": edges,
    }
    return data


@hlsExprTreeBp.route("/expr-tree-data/", methods=["POST", 'GET'])
def expr_tree_data():
    p = WebDumpHlsPlatform()
    u = HlsMAC_example()
    toRtl(u, targetPlatform=p)
    hls = p.hls[0]
    data = schedulizationGraphAsJSON(hls)
    return jsonify(data)
