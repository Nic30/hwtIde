const T_BIT = "bit"
const T_ENUM = "enum"
const T_BITS = "bits"

// zoom+drag https://bl.ocks.org/mbostock/6123708

var svg = d3.select("#wave-graph");

function WaveGraph(svg) {
    var g = svg.append("g");
    this.g = g;
    this.xaxisScale = null;
    this.yaxisScale = null;
    this.yaxis = null;
    this.xaxis = null;
    this.waveRowX = null;
    this.sizes = {
    		row: {
    			range: [0, 200],
    			height: 20,
    			ypadding: 5,
    		},
    	    margin: {
    			top : 20,
    			right : 20,
    			bottom : 20,
    			left : 180
    		},
    		width: -1,
    		height: -1
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

    	function moveVerticalHelpLine() {
    		var xPos = d3.mouse(this)[0];
    	    d3.select(".verticalHelpLine")
    	      .attr("transform", function () {
    	        return "translate(" + xPos + ",0)";
    	       });
    	}
    	
    	g.on('mousemove', moveVerticalHelpLine);
    }

    this.drawGridLines = function () {
    	// simple graph with grid lines in v4
    	// https://bl.ocks.org/d3noob/c506ac45617cf9ed39337f99f8511218
    	var height = this.sizes.height;
    	var xaxisScale = this.xaxisScale;
    	
    	// add the X gridlines
    	this.g.selectAll("g .grid")
    	      .attr("class", "grid")
    	      .attr("transform", "translate(0," + height + ")")
    	      .call(
    	    		d3.axisBottom(xaxisScale)
     	              .ticks(10)
    	              .tickSize(-height)
    	              .tickFormat("")
    	      )
    }
    
    this.drawXAxis = function () {
    	var sizes = this.sizes;
    	var xaxisScale = d3.scaleLinear()
                           .domain(sizes.row.range)
                           .range([ 0, sizes.width]);
        this.xaxisScale = xaxisScale;
        
        this.xaxis = g.selectAll(".axis-x")
                      .enter()
                      .append("g")
                      .attr("class", "axis axis-x")
                      .attr("transform", "translate(0,0)")
                      .call(d3.axisTop(xaxisScale));
    	this.waveRowX = d3.scaleLinear()
                          .domain(sizes.row.range)
                          .range([0, sizes.width]);
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


    	graph.data.forEach(function(data, indx) {
    		renderWaveRow(indx, data[1], data[2], graph)
    	})
    	
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
        this.yaxis = g.append("g")
                      .attr("class", "axis axis-y")
                      .call(d3.axisLeft(yaxisScale))
    }

    this.bindData = function(signalData) {
        this.data = signalData;
    }

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
