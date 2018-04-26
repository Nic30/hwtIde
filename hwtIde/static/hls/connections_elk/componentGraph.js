

function ComponentGraph() {
    var self = {};
    self.PORT_HEIGHT = 20;
    self.PORT_PIN_SIZE = [7, 10];
    self.CHAR_WIDTH = 7.55;
    self.CHAR_HEIGHT = 13;
    self.NODE_MIDDLE_PORT_SPACING = 20;
    self.MAX_NODE_BODY_TEXT_SIZE = [400, 400];
    // top, right, bottom, left
    self.BODY_TEXT_PADDING = [15, 10, 10, 10];

    function widthOfText(text) {
        if (text)
            return text.length * self.CHAR_WIDTH;
        else
            return 0;
    }

    /*
     * Split bodyText of one to lines and resolve dimensions of body text
     * */
    function initBodyTextLines(d) {
        var max = Math.max
        if (d.bodyText != null) {
            d.bodyText = d.bodyText.split("\n");
            var bodyTextW = 0;
            d.bodyText.forEach(function (line) {
                bodyTextW = max(bodyTextW, line.length);
            })
            bodyTextW *= self.CHAR_WIDTH;
            var bodyTextH = d.bodyText.length * self.CHAR_HEIGHT;  
        } else {
            var bodyTextW = 0;
            var bodyTextH = 0;
        }
        var pad = self.BODY_TEXT_PADDING;
        if (bodyTextW  > 0)
            bodyTextW += pad[1] + pad[3];
        if (bodyTextH  > 0)
            bodyTextH += pad[0] + pad[2];
        return [bodyTextW, bodyTextH];
    }

    /*
     * Init bodyText and resolve size of node from body text and ports 
     * */
    function initNodeSizes(d) {
    	if (d.children) {
            if (d.ports != null)
                d.ports.forEach(function(p) {
                	p.ignoreLabel = true;
                });
    		return;
    	}

        var labelW = widthOfText(d.name)
        var westCnt = 0;
        var eastCnt = 0;
        var portW = 0;
        var max = Math.max
        var bodyTextSize = initBodyTextLines(d);
        var MBT = self.MAX_NODE_BODY_TEXT_SIZE;
        bodyTextSize[0] = Math.min(bodyTextSize[0], MBT[0]);
        bodyTextSize[1] = Math.min(bodyTextSize[1], MBT[1]);

        if (d.ports != null)
          d.ports.forEach(function(p) {
              var t = p.properties.portSide;
              if (t == "WEST"){
                  westCnt++;    
              } else if (t == "EAST") {
                  eastCnt++;
              } else {
                  throw new Error(t);
              }
              var indent = 0;
              if (p.level > 0)
            	  indent = (p.level + 1) * self.CHAR_WIDTH;
              portW = max(portW, widthOfText(p.name) + indent)
              // dimension of connection pin
              p.width = self.PORT_PIN_SIZE[0];
              p.height = self.PORT_PIN_SIZE[1];
          })
        var portColums = 0;
        if (westCnt) portColums += 1;
        if (eastCnt) portColums += 1;
        var middleSpacing = 0;
        if (portColums == 2) middleSpacing = self.NODE_MIDDLE_PORT_SPACING
        
        d.portLabelWidth = portW;
        d.width = max(portW * portColums + middleSpacing, labelW) + bodyTextSize[0];
        d.height = max(max(westCnt, eastCnt) * self.PORT_HEIGHT, bodyTextSize[1]);
    }
    
    function renderTextLines(bodyTexts) {
        var padTop = self.BODY_TEXT_PADDING[0];
        var padLeft = self.BODY_TEXT_PADDING[3];
        bodyTexts.each(function() {
            var bodyText = d3.select(this)
            var d = bodyText.data()[0];
            var bodyTextLines = d.bodyText;
            var MBT = self.MAX_NODE_BODY_TEXT_SIZE;
            MBT = [MBT[0] /self.CHAR_WIDTH, MBT[1] / self.CHAR_HEIGHT];
            
            if (bodyTextLines && (d.children == null || d.children.length == 0)) {
                bodyTextLines.forEach(function (line, dy) {
                    if (line.length > MBT[0])
                        line = line.slice(0, MBT[0] - 3) + "...";
                    if (dy > MBT[1])
                        return;
                    bodyText
                       .append("tspan")
                       .attr("x", d.portLabelWidth + padLeft)
                       .attr("y", padTop)
                       .attr("dy", dy + "em")
                       .text(line);
                });
            }
        });
        
    }
    
    self.root = svg.append("g");
    self.layouter = elk.d3kgraph();
    
    /*
     * Set bind graph data to graph rendering engine
     * */
    self.bindData = function (graph) {
        var root = self.root;
        var layouter = self.layouter;
        // config of layouter
        layouter
            .kgraph(graph)
            .size([width, height])
            .transformGroup(root)
            .options({
              edgeRouting: "ORTHOGONAL",
            })
            .defaultPortSize(self.PORT_PIN_SIZE) // size of port icon
        var nodes = layouter.getNodes().slice(1); // skip root node
        var edges = layouter.getEdges();
        nodes.forEach(initNodeSizes);
            
        // by "g" we group nodes along with their ports
        var node = root.selectAll(".node")
            .data(nodes)
            .enter()
            .append("g");
        
        var nodeBody = node.append("rect");
        
        var port = node.selectAll(".port")
            .data(function(d) { return d.ports || []; })
            .enter()
            .append("g");
        
        var link = root.selectAll(".link")
            .data(edges)
            .enter()
            .append("path")
            .attr("class", "link")
        /*
         * Select net on click
         * */
        link.on("click", function(d) {
        	    var doSelect = !d.selected;
                var l = d3.select(this);
                var data = l.data()[0];
                // propagate click on all nets with same source
                var src = data.source;
                var srcP = data.sourcePort;
                link.classed("link-selected", function (d) {
                    if (d.source == src && d.sourcePort == srcP) {
                    	d.selected = doSelect;
                    }
                    return d.selected;
                });
                d3.event.stopPropagation();
        });
        

        // apply layout
        layouter.on("finish", function(graph) {
          nodeBody
            .attr("width", function(d) { return d.width })
            .attr("height", function(d) { return d.height });

          var junctionPoints = [];
          // apply edge routes
          link.transition().attr("d", function(d) {
            var path = "";
            if (d.bendpoints || d.sections.length > 1) {
                throw new Error("NotImplemented");
            }
            if(d.junctionPoints)
            	d.junctionPoints.forEach(function (jp) {
            		junctionPoints.push(jp);
            	});
            return elk.section2svgPath(d.sections[0]);
          });
          var junctionPoints = root.selectAll(".junction-point")
              .data(junctionPoints)
              .enter()
              .append("circle")
              .attr("r", "3")
              .attr("cx", function(d) {
            	  return d.x;
              })
              .attr("cy", function(d) {
            	  return d.y;
              })
              .attr("class", "junction-point");
          
          // apply node positions
          node.transition()
            .duration(0)
            .attr("transform", function(d) { return "translate(" + d.x + " " + d.y + ")"});
          
          var PORT_Y_OFFSET = (self.PORT_PIN_SIZE[1] - 2) / 2;
          // apply port positions  
          port.transition()
            .duration(0)
            .attr("transform", function(d) { return "translate(" + d.x + "," + (d.y + PORT_Y_OFFSET) + ")"});
        
        });
        
        layouter.start();
        
        // set dimensions and style of node
        nodeBody
            .attr("class", function (d) { 
                if (d.isExternalPort) {
                    return "node-external-port";
                } else {
                    return "node";
                }
            })
            .attr("rx", 5)
            .attr("ry", 5);
        
        // spot node label
        node.append("text")
            .text(function(d) { return d.name; });
        
        // spot node body text
        node.append("text")
            .call(renderTextLines)
        

        // spot port name
        port.append("text")
          .attr("y", self.PORT_HEIGHT / 4)
          .text(function(d) {
        	  if (d.ignoreLabel)
        		  return "";
        	  else if (d.level) {
                  var indent = '-'.repeat(d.level);
                  var side = d.properties.portSide;
                  if (side == "WEST") {
                     return indent + d.name;;
                  } else if (side == "EAST") {
                     return d.name + indent;
                  } else {
                      throw new Error(side);
                  }
              
              } else
                  return d.name; 
          })
          .attr("x", function(d) {
              var side = d.properties.portSide;
              if (side == "WEST") {
                 return 7;
              } else if (side == "EAST") {
                 return -this.getBBox().width - self.CHAR_WIDTH/2;
              } else {
                  throw new Error(side);
              }
          });
        
        // spot input/output marker
        port.append("use")
            .attr("href", getIOMarker)
        
    }
    return self;
}
