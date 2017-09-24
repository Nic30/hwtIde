const T_BIT = "bit"
const T_ENUM = "enum"
const T_BITS = "bits"

// zoom+drag https://bl.ocks.org/mbostock/6123708	
var rowRange = [0, 200]

var svg = d3.select("svg"), 
    margin = {
		top : 20,
		right : 20,
		bottom : 20,
		left : 40
	}, 
	graphWidth = parseInt(svg.style('width')) - margin.left - margin.right,
	height = parseInt(svg.style("height"))	- margin.top - margin.bottom, 
	g = svg.append("g")
		   .attr("transform",
		         "translate(" + margin.left + "," + margin.top + ")");

var x = d3.scaleLinear()
		  .domain(rowRange)
		  .range([ 0, graphWidth]);

// x axis
g.append("g")
 .attr("class", "axis axis--x")
 .attr("transform", "translate(0,0)")
 .call(d3.axisTop(x));


//var y = d3.scaleBand()
//          .rangeRound([0, height])
//          .padding(0.1)
//          .domain(signalNames)
//
//const nameScale = d3.scaleOrdinal()
//                    .domain(signalNames)
//                    .range([height, 0]);
//var y = d3.scaleLinear()
//          .domain([0,1])
//          .range([height, 0])
//
//// y axis
//g.append("g")
// .attr("class", "axis axis--y")
// .call(d3.axisLeft(y))


function verticalHelpLine(graph, height) {
	
	var verticalHelpLine = graph.append('line')
								.attr('x1', 0)
								.attr('y1', 0)
								.attr('x2', 0)
								.attr('y2', height)
								.attr('class', 'verticalHelpLine')

	function moveVerticalHelpLine(){
		var xPos = d3.mouse(this)[0];
	    d3.select(".verticalHelpLine")
	      .attr("transform", function () {
	        return "translate(" + xPos + ",0)";
	       });
	}
	
	graph.on('mousemove', moveVerticalHelpLine);
}

function gridLines(graph, height, rowRange){
	// imple graph with grid lines in v4 https://bl.ocks.org/d3noob/c506ac45617cf9ed39337f99f8511218
	
	function make_x_gridlines() {
		return d3.axisBottom(x)
	             .ticks(10)
	}
	
	//// gridlines in y axis function
	//function make_y_gridlines() {		
	//    return d3.axisLeft(y)
	//        	 .ticks(signalData[0][1].length)
	//}
	
	// add the X gridlines
	graph.append("g")			
	    .attr("class", "grid")
	    .attr("transform", "translate(0," + height + ")")
	    .call(make_x_gridlines()
	        .tickSize(-height)
	        .tickFormat("")
	    )
	
	//// add the Y gridlines
	//graph.append("g")			
	//    .attr("class", "grid")
	//    .call(make_y_gridlines()
	//        .tickSize(-width)
	//        .tickFormat("")
	//    )
	//
}

gridLines(g, height, rowRange)
verticalHelpLine(g, height)


d3.json("/wave-data", function(signalData) {
	var signalNames = signalData.map(function(d){
		return d[0]
	})

	signalData.forEach(function(data, indx){
		renderWaveRow(indx, data[1], data[2], rowRange)
	})
})
//rendering logic here//for (var i =0; i< 2; i++){
//	signalData.push(["clk" + i, {name:T_BIT}, randData(10)])
//	signalData.push(["clk" + i, {name:T_BITS, width:8}, randBitsData(10, 8)])
//	
//}