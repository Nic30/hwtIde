

function ExprTreeGraph(svg) {
    var simulation = d3.forceSimulation()
	    .force("link", d3.forceLink().distance(30))
	    .force("collide", d3.forceCollide(function(d) {
	                                           return d.r + 8
	                                     }).iterations(16))
	    .force("charge", d3.forceManyBody().strength(-1000));
    var levellines = null; 
    var levellabels = null;
    var dragging = false;
    var levelize = 0;

    this.data = {nodes:[], edges:[]}
    /* where node = {id: ..., label: ..., level: ...}
     *       edge = {source:nodeId, target:nodeId}
     */

    // link arrow definition
    svg.append('defs')
       .append('marker')
       .attr('id', 'arrowhead')
       .attr('viewBox','-0 -5 10 10')
       .attr('refX', 20)
       .attr('orient', 'auto')
       .attr('markerWidth', 13)
       .attr('markerHeight', 13)
       .attr('xoverflow','visible')
       .append('path')
       .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
       .attr('fill', '#999')
       .style('stroke','none');

    function drag_started(d) {
        if (!d3.event.active)
            simulation.alphaTarget(0.3).restart();
        dragging = true;
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }
    
    function drag_ended(d) {
        if (!d3.event.active)
            simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
        dragging = false;
    } 

    
    this.redraw = function() {
    	var width = parseInt(svg.style("width"))
    	var height = parseInt(svg.style("height"))
    	var data = this.data;
        var levelCnt = 0;

        data.nodes.forEach(function(n) {
            if (n.level > levelCnt)
                levelCnt = n.level;
        })
        var levelHeight = height / levelCnt;

        var y = d3.scaleLinear()
                  .domain([0, levelCnt])
                  .range([levelHeight, d3.max([levelCnt - 1, 1]) * levelHeight])
        
                  
        svg.selectAll(".links").remove()
        var link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(data.edges)
            .enter()
            .append("line")
            .attr('marker-end','url(#arrowhead)')
        
        svg.selectAll(".nodes").remove()
        var node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(data.nodes)
            .enter()
            .append("circle")
            .attr("r", 15)
            .call(d3.drag()
                .on("start", drag_started)
                .on("drag", dragged)
                .on("end", drag_ended))
        
        svg.selectAll(".nodelabels").remove()
        var nodelabels = svg.append("g")
           .attr("class", "nodelabels")
           .selectAll("text")
           .data(data.nodes)
           .enter()
           .append("text")
           .text(function(d) { return d.label })
           .attr("dy", ".35em")  // lower the text little bit
           .attr("x", function(d) { return d.x; }) // set text on same possition as nodes
           .attr("y", function(d) { return d.y; });    
        
        var levels = d3.range(levelCnt).map(
                           function (level){  
                               return {
                                  y: y(level),
                                  level: level 
                               };
                           })
        
        svg.selectAll(".levellines").remove()
        levellines = svg.append("g")
            .attr("class", "levellines")
            .selectAll("line")
            .data(levels)
            .enter()
            .append("line")
            .attr("x1", 0)
            .attr("y1", function (d) { return d.y; })
            .attr("y2", function (d) { return d.y; });
       
       svg.selectAll(".levellabels").remove()
       levellabels = svg.append("g")
            .attr("class", "levellabels")
            .selectAll("text")
            .data(levels)
            .enter()
            .append("text")
            .attr("x", 0)
            .attr("y", function (d) { return d.y + 20; })
            .text(function(d) { return d.level });
       
            
        var ticked = function() {
             var k = simulation.alpha();
             if(levelize && !dragging) {
                 data.nodes.forEach(function(o, i) {
                      o.y = y(o.level);
                 });
             }
            
            link
                .attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });
        
            node
                .attr("cx", function(d) { return d.x; })
                .attr("cy", function(d) { return d.y; });

            nodelabels
                .attr("x", function(d) { return d.x; })
                .attr("y", function(d) { return d.y; }); 
        }
        
        
        simulation
            .nodes(data.nodes)
            .on("tick", ticked);
        
        simulation.force("link")
                  .links(data.edges);    

        // [HOTFIX]
        // wait unitl tree is partialy sorted and then start to order it to levels
        setTimeout(function () {levelize = 1;}, 1000);
        simulation.stop();
        simulation.force("y", d3.forceY(height / 2))
                  .force("x", d3.forceX(width / 2))
                  .alpha(.2).restart();
        levellines.attr("x2", width);
    }

    this.bindData = function (data) {
    	this.data = data;
    }

    this.resize = function(width, height) {
         svg.attr("width", width)
            .attr("height", height);
         this.redraw()
    }
}

var svg = d3.select("#exprtree");
var graph = new ExprTreeGraph(svg);

d3.json("/expr-tree-data/", function(error, data) {
	graph.bindData(data);
    graph.redraw();
});

function resize() {
	var width = window.innerWidth;
    var height = window.innerHeight;
    graph.resize(width, height);
}
d3.select(window).on("resize", resize);