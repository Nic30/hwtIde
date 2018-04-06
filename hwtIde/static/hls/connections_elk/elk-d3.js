var elk;
(function (elk) {
  elk.d3adapter = function() {
    return init("adapter");
  };
  elk.d3kgraph = function() {
    return init("kgraph");
  };
  /**
   * Convert section from ELK json to svg path string
   */
  elk.section2svgPath = function (section) {
    var pathBuff = ["M", section.startPoint.x, section.startPoint.y];
    if (section.bendPoints)
      section.bendPoints.forEach(function (bp, i) {
        pathBuff.push("L");
        pathBuff.push(bp.x);
        pathBuff.push(bp.y);
    });
  
    pathBuff.push("L");
    pathBuff.push(section.endPoint.x);
    pathBuff.push(section.endPoint.y);
    return pathBuff.join(" ")
  }
  
  function init(type) {
    var d3elk = {},
    dispatch = d3.dispatch("finish"),
    // containers
    nodes = [],
    links = [],
    graph = {}, // internal (hierarchical graph)
    ports = function(n) {
      // by default the 'ports' field
      return n.ports || [];
    },
    labels = function(n) {
      return n.labels || [];
    },
    options = {},
    // dimensions
    width = 0,
    height = 0,
    defaultNodeSize = [10, 10],
    defaultPortSize = [4, 4],
    transformGroup,
    // kgraph properties that shall be copied
    kgraphKeys = [
      'x', 'y',
      'width', 'height',
      'sourcePoint', 'targetPoint',
      'properties'
    ].reduce(function(p, c) {p[c] = 1; return p;}, {}),
    // a function applied after each layout run
    applyLayout = function() {},
    // location of the elk.js script
    layouterScript = function() {
      var scripts = document.getElementsByTagName('script');
      for (var i = 0; i < scripts.length; ++i) {
      var url = scripts[i].src;  
        if (url.indexOf("elk.js") > -1 || url.indexOf("elk.bundled.js") > -1) {
          return scripts[i].src;
        }
      }
      throw "elk.js library wasn't loaded!";
    },
    // the layouter instance
    layouter;
    
    // try to use a worker?
    if ('<%= worker %>' === 'true' && typeof(Worker) !== 'undefined') {
      var worker = new Worker(layouterScript());
      layouter = {
        layout: function(data) {
          worker.postMessage({
            graph: data.graph,
            options: data.options
          });
        }
      };
      worker.addEventListener('message', function (e) {
        graph = e.data;
        applyLayout(graph);
      }, false);
    } 

    // either we don't want a worker or the worker is not available
    if (!layouter) {
      if (typeof ELK !== "undefined") {
          // elkjs already imported
        layouter = new ELK();
      } else if (typeof module === "object" && module.exports) {
          layouter = require("elkjs");
      } else if (typeof $elkjs !== "undefined") {
        // try to get from global scope, e.g. loaded by bower
          layouter = $elkjs;
      } else {
          throw "elkjs.js library wasn't loaded!"
      }
    }
    /**
     * Setting the available area, the
     * positions of the layouted graph
     * are currently scaled down.
     */
    d3elk.size = function(size) {
      if (!arguments.length) return [width, height];
      width = size[0];
      height = size[1];
      return d3elk;
    };
    /**
     * Sets the group used to perform 'zoomToFit'.
     */
    d3elk.transformGroup = function(g) {
      if (!arguments.length) return transformGroup;
      transformGroup = g;
      return d3elk;
    };
    d3elk.options = function(opts) {
      if (!arguments.length) return options;
      options = opts;
      return d3elk;
    };
    /**
     * D3 Adaptor
     * Allows to use d3 in its known fashion.
     *   Ids are assigned to the specified
     *   nodes and links and a top level node
     *   is constructed.
     */
    if (type === "adapter") {
      /**
       * The nodes of the graph.
       */
      d3elk.nodes = function(ns) {
        if (!arguments.length) return nodes;
        nodes = ns;
        return d3elk;
      };
      /**
       * Accessor function to a node's ports.
       */
      d3elk.ports = function(ps) {
        if (!arguments.length) return ports;
        ports = ps;
        return d3elk;
      };
      /**
       * The links of the graph.
       */
      d3elk.links = function(es) {
        if (!arguments.length) return links;
        links = es;
        return d3elk;
      };
      d3elk.defaultNodeSize = function(dns) {
        if (!arguments.length) return defaultNodeSize;
        defaultNodeSize = dns;
        return d3elk;
      };
      d3elk.defaultPortSize = function(dps) {
        if (!arguments.length) return defaultPortSize;
        defaultPortSize = dps;
        return d3elk;
      };
      d3elk.onError = function(e) {
        console.error(e);
      };
      /**
       * Start the layout process.
       */
      d3elk.start = function() {
        // elk expects string identifiers
        nodes.forEach(function(n, i) {
          n.width = n.width || defaultNodeSize[0];
          n.height = n.height || defaultNodeSize[1];
          n.id = "" + (n.id || i);
          // ports
          n.ports = ports(n);
          n.ports.forEach(function(p) {
            p.width = p.width || defaultPortSize[0];
            p.height = p.height || defaultPortSize[1];
          });
          n.labels = labels(n);
        });
        links.forEach(function(l, i) {
          l.id = "" + (l.id || (i + nodes.length));
          l.source = "" + l.source;
          l.target = "" + l.target;
        });
        // alias applyLayout method
        applyLayout = d3_applyLayout;
        var graph = {
              id: "root",
              properties: { 'algorithm': 'layered' },
              layoutOptions: options,
              children: nodes,
              edges: links,
            }
        
        // start the layouter
        function onSuccess(kgraph)  {
            graph = kgraph;
            applyLayout(kgraph);
        }
        layouter.layout(graph).then(onSuccess, d3elk.onError);
        return d3elk;
      };
      /**
       * Apply layout for d3 style.
       * Copies properties of the layouted graph
       * back to the original nodes and links.
       */
      var d3_applyLayout = function(kgraph) {
        if (kgraph) {
          zoomToFit(kgraph);
          // assign coordinates to nodes
          kgraph.children.forEach(function(n) {
            var d3node = nodes[parseInt(n.id)];
            if (typeof d3node === 'undefined')
              throw new Error("Can not find node with id:" + n.id)
            copyProps(n, d3node);
            if (!((!d3node.ports && !n.ports) || d3node.ports.length == n.ports.length)) {
                throw new Error("Ports from ELK has different dimension than original ports");
            }
            (n.ports || []).forEach(function(p, i) {
              copyProps(p, d3node.ports[i]);
            });
            (n.labels || []).forEach(function(l, i) {
              copyProps(l, d3node.labels[i]);
            });
          });
          // edges
          kgraph.edges.forEach(function(e) {
            var l = links[parseInt(e.id) - nodes.length];
            copyProps(e, l);
            copyProps(e.source, l.source);
            copyProps(e.target, l.target);
            // make sure the bendpoint array is valid
            l.bendPoints = e.bendPoints || [];
          });
        }
        function copyProps(src, tgt, copyKeys) {
          var keys = kgraphKeys;
          if (copyKeys) {
            keys = copyKeys.reduce(function (p, c) {p[c] = 1; return p;}, {});
          }
          for (var k in src) {
            if (keys[k]) {
              tgt[k] = src[k];
            }
          }
        }
        // invoke the 'finish' event
        dispatch.call('finish', {graph: kgraph});
      };
    }
    /*
     * KGraph
     * Allows to use the JSON KGraph format
     */
    if (type === "kgraph") {
      d3elk.nodes = function() {
        var queue = [graph],
            nodes = [],
            parent;
        // note that svg z-index is document order, literally
        while ((parent = queue.pop()) != null) {
          nodes.push(parent);
          (parent.children || []).forEach(function(c) {
            queue.push(c);
          });
        }
        return nodes;
      };
      d3elk.links = function(nodes) {
        return d3.merge(nodes.map(function(n) {
          return n.edges || [];
        }));
      };
      d3elk.kgraph = function(root) {
        applyLayout = d3_kgraph_applyLayout;
        // start the layouter
        layouter.layout({
          "graph": root,
          "options": options,
          "success": function(kgraph) {
            graph = kgraph;
            applyLayout(kgraph);
          },
          "error": function(e) {
            console.error(e);
          }
        });
        return d3elk;
      };
      /**
       * Apply layout for the kgraph style.
       * Converts relative positions to absolute positions.
       */
      var d3_kgraph_applyLayout = function(kgraph) {
        zoomToFit(kgraph);
        var nodeMap = {};
        // convert to absolute positions
        toAbsolutePositions(kgraph, {x: 0, y:0}, nodeMap);
        toAbsolutePositionsEdges(kgraph, nodeMap);
        // invoke the 'finish' event
        dispatch.call('finish', {graph: kgraph});
      };
      var toAbsolutePositions = function(n, offset, nodeMap) {
        n.x = (n.x || 0) + offset.x;
        n.y = (n.y || 0) + offset.y;
        nodeMap[n.id] = n;
        // the offset for the children has to include padding
        var childOffset = {x: n.x, y: n.y};
        if (n.padding) {
          childOffset.x += n.padding.left || 0;
          childOffset.y += n.padding.top || 0;
        }
        // children
        (n.children || []).forEach(function(c) {
          c.parent = n;
          toAbsolutePositions(c, childOffset, nodeMap);
        });
      };
      var isDescendant = function(node, child) {
        var parent = child.parent;
        while (parent) {
          if (parent == node) {
            return true;
          }
          parent = parent.parent;
        }
        return false;
      }
      var toAbsolutePositionsEdges = function(n, nodeMap) {
        // edges
        (n.edges || []).forEach(function (e) {
          // transform edge coordinates to absolute coordinates. Note that
          //  node coordinates are already absolute and that
          //  edge coordinates are relative to the source node's parent node
          //  (unless the target node is a descendant of the source node)
          var srcNode = nodeMap[e.source];
          var tgtNode = nodeMap[e.target];
          var relative = isDescendant(srcNode, tgtNode) ?
                          srcNode : srcNode.parent;
          var offset = {x: 0, y: 0};
          if (relative) {
            offset.x = relative.x;
            offset.y = relative.y;
          }
          if (relative.padding) {
            offset.x += relative.padding.left || 0;
            offset.y += relative.padding.top || 0;
          }
          // ... and apply it to the edge
          if (e.sourcePoint) {
            e.sourcePoint.x += offset.x || 0;
            e.sourcePoint.y += offset.y || 0;
          }
          if (e.targetPoint) {
            e.targetPoint.x += offset.x || 0;
            e.targetPoint.y += offset.y || 0;
          }
          (e.bendPoints || []).forEach(function (bp) {
            bp.x += offset.x;
            bp.y += offset.y;
          });
        });
        // children
        (n.children || []).forEach(function(c) {
          toAbsolutePositionsEdges(c, nodeMap);
        });
      };
    }
    /**
     * If a top level transform group is specified,
     * we set the scale such that the available
     * space is used to its maximum.
     */
    function zoomToFit(kgraph) {
      // scale everything so that it fits the specified size
      var scale = width / kgraph.width || 1;
      var sh = height / kgraph.height || 1;
      if (sh < scale) {
        scale = sh;
      }
      // if a transformation group was specified we
      // perform a 'zoomToFit'
      if (transformGroup) {
        transformGroup.attr("transform", "scale(" + scale + ")");
      }
    }
    
    d3elk.on = function() {
        var value = dispatch.on.apply(dispatch, arguments);
        return value === dispatch ? d3elk : value;
    };
    // return the layouter object
    return d3elk;
  }
  if (typeof module === "object" && module.exports) {
    module.exports = elk;
  }
  return elk;
})(elk || (elk = {}));