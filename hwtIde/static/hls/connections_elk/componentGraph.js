

function ComponentGraph() {
	var self = {};
    self.PORT_HEIGHT = 20;
    self.CHAR_WIDTH = 7.55;
    self.NODE_MIDDLE_PORT_SPACING = 20;

    function widthOfText(text) {
    	if (text)
    	    return text.length * self.CHAR_WIDTH;
    	else
    		return 0;
    }

    function initNodeSizes(d) {
        var labelW = widthOfText(d.name)
        var westCnt = 0;
        var eastCnt = 0;
    	var portW = 0;
    	var max = Math.max
    	
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
        	p.width = 2;
        	p.height = 2;
        })
        
        d.width = max(portW * 2 + self.NODE_MIDDLE_PORT_SPACING, labelW)
        d.height = max(westCnt, eastCnt) * self.PORT_HEIGHT;
    }
    
    self.root = svg.append("g");
    self.layouter = elk.d3adapter();
    
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
    	    .defaultPortSize([2, 2]) // size of port icon
    	    
    	var link = root.selectAll(".link")
    	    .data(graph.links)
    	    .enter()
    	    .append("path")
    	    .attr("class", "link")

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

    	  // apply port positions  
    	  port.transition()
    	    .duration(0)
    	    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"});

    	});
    	
    	layouter.start();

    	// set dimensions and style of node
    	nodeBody
    	    .attr("class", "node")
    	    .attr("width", function(d) { return d.width })
    	    .attr("height", function(d) { return d.height })
    	    .attr("rx", 5)
    	    .attr("ry", 5);

    	// spot node label
    	node.append("text")
    	    .text(function(d) { return d.name; });

    	// spot port name
    	port.append("text")
    	  .attr("y", self.PORT_HEIGHT / 4)
    	  .text(function(d) { return d.name; })
    	  .attr("x", function(d) {
    	  	var side = d.properties.portSide;
    	  	if (side == "WEST") {
    	  	   return 5;
    	  	} else if (side == "EAST") {
    	  	   return -this.getBBox().width - 5;
    	  	} else {
    	  		throw new Error(side);
    	  	}
    	  });

    	// spot input/output marker
    	port.append("use")
    	    .attr("href", getIOMarker)

    	// spot port connection pin
    	port
    	  .append("rect")
    	  .attr("class", "port")
    	  .attr("width", function(d){ return d.width })
    	  .attr("height", function(d){ return d.height })
    }
    return self;
}