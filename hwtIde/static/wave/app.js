var n = 40

function randData(){
	function random(){
		var r = Math.random()
		if (r < 0.4)
			return false
		else if (r>0.6)
			return true
		else 
			return null
	}
	var data = []
	var lastD = null
	for (var i = 0; i< n; i++){
		var d = random()
		// we need to create points when value changes
		// to have right angle curve
		if (d != lastD && i != 0){
			data.push([i, lastD])
		}
		lastD = d
		data.push([i, d])
	}
	
	return data
}

var signalData = []
for (var i =0; i< 30; i++){
	signalData.push(["clk"+i, randData()])
}

var svg = d3.select("svg"), 
    margin = {
		top : 20,
		right : 20,
		bottom : 20,
		left : 40
	}, 
	width = parseInt(svg.style('width')) - margin.left - margin.right,
	height = parseInt(svg.style("height"))	- margin.top - margin.bottom, 
	g = svg.append("g")
		   .attr("transform",
		         "translate(" + margin.left + "," + margin.top + ")");

var x = d3.scaleLinear()
		.domain([ 0, n - 1 ])
		.range([ 0, width ]);

// x axis
g.append("g")
 .attr("class", "axis axis--x")
 .attr("transform", "translate(0," + height + ")")
 .call(d3.axisBottom(x));


var signalNames = signalData.map(function(d){
 	return d[0]
})

//var y = d3.scaleBand()
//          .rangeRound([0, height])
//          .padding(0.1)
//          .domain(signalNames)
//
//const nameScale = d3.scaleOrdinal()
//                    .domain(signalNames)
//                    .range([height, 0]);
var y = d3.scaleLinear()
          .domain([0,1])
          .range([height, 0])

// y axis
g.append("g")
 .attr("class", "axis axis--y")
 .call(d3.axisLeft(y))

function renderWaveRow(indx, data){
	var waveRowWidth = width
	var waveRowHeight = 20
	var waveRowYpadding = 5

	var waveRowX =  d3.scaleLinear()
					  .domain([ 0, n - 1 ])
					  .range([ 0, waveRowWidth ]);

	var waveRowY = d3.scaleLinear()
	                 .domain([0, 1])
	                 .range([(waveRowHeight + waveRowYpadding) * (indx + 1) - waveRowYpadding,
	                	     (waveRowHeight + waveRowYpadding) * indx]);

	var line = d3.line()
	   .x(function(d) {
	        return waveRowX(d[0]);
	    })
	   .y(function(d) {
	   		return waveRowY(d[1]);
	    });
	
	// wave line
	g.append("g")
	 .attr("clip-path", "url(#clip)")
	 .append("path")
	 .datum(data)
	 .attr("class", "line")
	 .attr("d", line)

	// Add the scatterplot
	g.selectAll("invalid-rect")	
	    .data(data)
	    .enter()
	    .filter(function(d, indx) { return d[1] === null && (indx===0 || data[indx-1][1] !== null) })
	    .append("rect")						
	    .attr("height", waveRowHeight)
	    .attr("width", waveRowWidth/n)
	    .style("fill",  "red")
	    .attr("x", function(d) { return waveRowX(d[0]) })		 
	    .attr("y", function(d) { return waveRowY(0)- waveRowHeight }); 
	
}
signalData.forEach(function(data, indx){
	renderWaveRow(indx, data[1])
})


// imple graph with grid lines in v4 https://bl.ocks.org/d3noob/c506ac45617cf9ed39337f99f8511218
function make_x_gridlines() {		
    return d3.axisBottom(x)
             .ticks(n)
}

//// gridlines in y axis function
//function make_y_gridlines() {		
//    return d3.axisLeft(y)
//        	 .ticks(signalData[0][1].length)
//}

// add the X gridlines
g.append("g")			
    .attr("class", "grid")
    .attr("transform", "translate(0," + height + ")")
    .call(make_x_gridlines()
        .tickSize(-height)
        .tickFormat("")
    )

//// add the Y gridlines
//g.append("g")			
//    .attr("class", "grid")
//    .call(make_y_gridlines()
//        .tickSize(-width)
//        .tickFormat("")
//    )
//