

function ComponentGraph() {
    var self = {};
    self.PORT_HEIGHT = 20;
    self.PORT_PIN_SIZE = [7, 10];
    self.CHAR_WIDTH = 7.55;
    self.CHAR_HEIGHT = 13;
    self.NODE_MIDDLE_PORT_SPACING = 20;
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
        if (d.bodyText) {
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
        var labelW = widthOfText(d.name)
        var westCnt = 0;
        var eastCnt = 0;
        var portW = 0;
        var max = Math.max
        var bodyTextSize = initBodyTextLines(d);
        
        d.ports.forEach(function(p) {
            var t = p.properties.portSide;
            if (t == "WEST"){
                westCnt++;    
            } else if (t == "EAST") {
                eastCnt++;
            } else {
                throw new Error(t);
            }
            portW = max(portW, widthOfText(p.name))
            // dimension of connection pin
            p.width = self.PORT_PIN_SIZE[0];
            p.height = self.PORT_PIN_SIZE[1];
        })
        d.portLabelWidth = portW;
        d.width = max(portW * 2 + self.NODE_MIDDLE_PORT_SPACING, labelW) + bodyTextSize[0];
        d.height = max(max(westCnt, eastCnt) * self.PORT_HEIGHT, bodyTextSize[1]);
    }
    
    function renderTextLines(bodyTexts) {
        var padTop = self.BODY_TEXT_PADDING[0];
        var padLeft = self.BODY_TEXT_PADDING[3];
        bodyTexts.each(function() {
            var bodyText = d3.select(this)
            var d = bodyText.data()[0];
            var bodyTextLines = d.bodyText;
            if (bodyTextLines) {
                bodyTextLines.forEach(function (line, dy) {
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
    self.layouter = elk.d3adapter();
    
    /*
     * Set bind graph data to graph rendering engine
     * */
    self.bindData = function (graph) {
        var root = self.root;
        var layouter = self.layouter;
        graph.nodes.forEach(initNodeSizes);
        // config of layouter
        layouter
            .nodes(graph.nodes)
            .links(graph.links)
            .size([width, height])
            .transformGroup(root)
            .options({
              edgeRouting: "ORTHOGONAL",
            })
            .defaultPortSize(self.PORT_PIN_SIZE) // size of port icon
            
        var link = root.selectAll(".link")
            .data(graph.links)
            .enter()
            .append("path")
            .attr("class", "link")
        /*
         * Select net on click
         * */
        link.on("click", function(d) {
                d.selected = !d.selected;
                d3.select(this).classed("link-selected", d.selected);
                console.log("rect");
                //d3.event.stopPropagation();
        });
        
        // by "g" we group nodes along with their ports
        var node = root.selectAll(".node")
            .data(graph.nodes)
            .enter()
            .append("g");
        
        var nodeBody = node.append("rect");
        
        var port = node.selectAll(".port")
            .data(function(d) { return d.ports; })
            .enter()
            .append("g");
        
        // apply layout
        layouter.on("finish", function(d) {
        
          // apply edge routes
          link.transition().attr("d", function(d) {
            var path = "";
            if (d.bendpoints || d.sections.length > 1) {
                throw new Error("NotImplemented");
            }
            
            return elk.section2svgPath(d.sections[0]);
          });
        
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
            .attr("width", function(d) { return d.width })
            .attr("height", function(d) { return d.height })
            .attr("rx", 5)
            .attr("ry", 5);
        
        // spot node label
        node.append("text")
            .text(function(d) { return d.name; });
        
        // spot node body text
        node.append("text")
            .call(renderTextLines)
        
        var PORT_X_OFFSET = self.PORT_PIN_SIZE[0];
        // spot port name
        port.append("text")
          .attr("y", self.PORT_HEIGHT / 4)
          .text(function(d) { 
              if (d.level) {
                  var indent = '-'.repeat(d.level);
                  var side = d.properties.portSide;
                  if (side == "WEST") {
                     return indent + d.name;;
                  } else if (side == "EAST") {
                     return d.name + indent;
                  } else {
                      throw new Error(side);
                  }
              
              } else {
                  return d.name; 
              }
          })
          .attr("x", function(d) {
              var side = d.properties.portSide;
              if (side == "WEST") {
                 return PORT_X_OFFSET;
              } else if (side == "EAST") {
                 return -this.getBBox().width - PORT_X_OFFSET;
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
