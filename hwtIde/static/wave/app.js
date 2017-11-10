// zoom+drag https://bl.ocks.org/mbostock/6123708

var svg = d3.select("#wave-graph");

function WaveGraph(svg) {
	var g = svg.append("g");
	this.g = g;
	this.xaxisScale = null;
	this.yaxisScale = null;
	this.yaxisG = null;
	this.xaxisG = null;
	this.waveRowX = null;
	this.sizes = {
		row : {
			range : [ 0, 200 ],
			height : 20,
			ypadding : 5,
		},
		margin : {
			top : 20,
			right : 20,
			bottom : 20,
			left : 180
		},
		width : -1,
		height : -1
	};
	this.data = [];
    
    this.setSizes = function () {
    	var s = this.sizes;
    	s.width = (parseInt(svg.style('width'))
    			   - s.margin.left
    			   - s.margin.right);
    	s.height = (parseInt(svg.style("height"))
    			    - s.margin.top
    			    - s.margin.bottom);
    	g.attr("transform",
    			"translate(" + s.margin.left + "," + s.margin.top + ")");
    }

    this.drawYHelpLine = function () {
    	var height = this.sizes.height;
    	var verticalHelpLine = g.append('line')
    							.attr('x1', 0)
    							.attr('y1', 0)
    							.attr('x2', 0)
    							.attr('y2', height)
    							.attr('class', 'verticalHelpLine')

    	var marginLeft = this.sizes.margin.left;
    	function moveVerticalHelpLine() {
    		var xPos = d3.mouse(this)[0] - marginLeft;
    	    if (xPos < 0)
    	    	xPos = 0;
    		d3.select(".verticalHelpLine")
    	      .attr("transform", function () {
    	        return "translate(" + xPos + ",0)";
    	       });
    	}
    	
    	svg.on('mousemove', moveVerticalHelpLine);
    }

    this.drawGridLines = function () {
    	// simple graph with grid lines in v4
    	// https://bl.ocks.org/d3noob/c506ac45617cf9ed39337f99f8511218
    	var height = this.sizes.height;
    	var xaxisScale = this.xaxisScale;
    	var xValues = xaxisScale.ticks(10)
    	                        .map(function(d){
    									return xaxisScale(d)
    							})
    	// add the X gridlines
    	var gridLines = this.g.selectAll(".grid-line-x")
	                          .data(xValues);

    	gridLines
           .enter()
           .append("line")
    	   .attr("class", "grid-line-x")
    	   .merge(gridLines)
    	   .attr('x1', function (d) { return d })
           .attr('y1', 0)
           .attr('x2', function (d) { return d })
           .attr('y2', height)

        gridLines.exit().remove();
    }
    
    this.drawXAxis = function () {
    	var sizes = this.sizes;
    	var xaxisScale = d3.scaleLinear()
                           .domain(sizes.row.range)
                           .range([ 0, sizes.width]);
        this.xaxisScale = xaxisScale;
    	this.waveRowX = xaxisScale;
        
    	//var axisX = g.selectAll(".axis-x")
        // https://bl.ocks.org/HarryStevens/54d01f118bc8d1f2c4ccd98235f33848
    	// General Update Pattern, I https://bl.ocks.org/mbostock/3808218
    	// http://bl.ocks.org/nnattawat/9054068
        var xaxisG = this.xaxisG
    	if (xaxisG) {
        	var xaxis = this.xaxis;
            xaxisG.call(xaxis.scale(xaxisScale))
        } else { 
        	var xaxis = this.xaxis = d3.axisTop(xaxisScale)
    	    this.xaxisG = this.g.append("g")
                          .attr("class", "axis axis-x")
                          .attr("transform", "translate(0,0)")
                          .call(xaxis)
        }
    }
    
    this.draw = function () {
    	this.setSizes();

    	var sizes = this.sizes;
    	var graph = this;
    	var signalData = this.data;

    	this.drawXAxis();
    	this.drawGridLines();
    	this.drawYHelpLine();

    	// drawWaves
        var valueRows = this.g.selectAll(".value-row")
    	                      .data(graph.data)
        
    	function renderWaveRows(selection) {
            selection.each(function(d, i) {
        	   renderWaveRow(i, d[1], d[2], graph, d3.select(this))
            });
        }
    	                      
        valueRows.enter()
                 .append("g")
                 .attr("class", "value-row")
                 .merge(valueRows)
                 .call(renderWaveRows)

    	// drawWaveLabels
    	var signalNames = signalData.map(function(d) {
    		return d[0]
    	})
    	var namesHeight = signalData.length * (sizes.row.height + sizes.row.ypadding);
    	var yaxisScale = d3.scaleBand()
                           .rangeRound([0, namesHeight])
                           .domain(signalNames)
        this.yaxisScale = yaxisScale;
        // y axis
        if (this.yaxisG)
        	this.yaxisG.remove()
        this.yaxisG = g.append("g")
                  .attr("class", "axis axis-y")
                  .call(d3.axisLeft(yaxisScale))
    }

    this.bindData = function(signalData) {
        this.data = signalData;
    }
    var graph = this
    var defaultSize = graph.sizes.row.range;

    function zoomed() {
        var t = d3.event.transform;
        var width = graph.sizes.width
        var intervalRange = defaultSize[1] - defaultSize[0];
        var newRange = defaultSize.map(function (x) {
        	return (x  - (t.x / width * intervalRange)) / t.k
        })
        if (newRange[0] < 0)
        	newRange[0] = 0
        graph.sizes.row.range = newRange; 
        graph.draw()
     }

    var margin = this.sizes.margin;
    var maxT = 500;
    var zoom = d3.zoom()
        .scaleExtent([0, 40])
        .translateExtent([[0, 0], [maxT, 0]])
        .extent([[0, 0], [maxT, 0]])
        .on("zoom", zoomed);
    svg.call(zoom)
}


var waveGraph = new WaveGraph(svg);

d3.json("/wave-data", function(signalData) {
    waveGraph.bindData(signalData);
    waveGraph.draw();
})

function resize() {
	waveGraph.setSizes()
	waveGraph.draw()
}
d3.select(window).on("resize", resize);
