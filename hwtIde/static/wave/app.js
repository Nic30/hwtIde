const T_BIT = "bit"
const T_ENUM = "enum"
const T_BITS = "bits"

function randData(n) {
	function random() {
		var r = Math.random()
		if (r < 0.4)
			return [ 0, 1 ]
		else if (r > 0.6)
			return [ 1, 1 ]
		else
			return [ 0, 0 ]
	}
	var data = []
	for (var i = 0; i < n; i++) {
		var d = random()
		// we need to create points when value changes
		// to have right angle curve
		data.push([ i, d ])
	}
	
	return data
}

function randBitsData(n, width) {
	function random() {
		var r = Math.random()
		if (r < 0.2)
			return [ 0, 0]
		else
			return [ Math.ceil(Math.random()*10)+1, mask(width) ]
	}
	var data = []
	for (var i = 0; i < n; i++) {
		var d = random()
		data.push([ i, d ])
	}
	
	return data
}

var signalData = []
for (var i =0; i< 2; i++){
	signalData.push(["clk" + i, {name:T_BIT}, randData(10)])
	signalData.push(["clk" + i, {name:T_BITS, width:8}, randBitsData(10, 8)])
	
}
var rowRange = [0, 10-1]

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

function renderBitLine(parent, data, signalWidth, waveRowHeight, waveRowYpadding, waveRowX, waveRowY){
	var vldMask = mask(signalWidth)
	var invalidRanges = []
	var lastInvalid = null
	var lineData = []
	var lastD=null;
	data.forEach(function (d){
		if (lastD!=null && !valCmp(d[1], lastD[1])) {
			lineData.push([d[0], lastD[1]])
		}
		lastD = d
		lineData.push(d)

		if(valVld(d[1]) === vldMask){
			if (lastInvalid != null){
				invalidRanges.push([lastInvalid[0], d[0]])
				lastInvalid = null
			}
		} else
			if (lastInvalid == null)
				lastInvalid = d
		
	})
	
    var line = d3.line()
    	     .x(function(d) {
    	          return waveRowX(d[0]);
    	      })
    	     .y(function(d) {
    	     	  return waveRowY(valVal(d[1]));
    	      });
		
    // wave line
    g.append("g")
     .attr("clip-path", "url(#clip)")
     .append("path")
     .datum(lineData)
     .attr("class", "line")
     .attr("d", line)
	
	// Add the scatterplot
	parent.selectAll("rect")	
	 .data(invalidRanges)
	 .enter()
	 .append("rect")						
	 .attr("height", waveRowHeight - waveRowYpadding)
	 .attr("width",  function (d){ 
		               return waveRowX(d[1] - d[0]) 
	  })
	 .attr("x", function(d) { 
		 			return waveRowX(d[0]) 
	  })		 
	 .attr("y", function(d) { 
		            return waveRowY(0) - waveRowHeight + waveRowYpadding 
	  })
	  .attr("class", "value-rect-invalid"); 
}

function renderWaveRow(indx, signalType, data, rowRange){
	var waveRowWidth = graphWidth
	var waveRowHeight = 20
	var waveRowYpadding = 5
	var signalWidth = 1

	var waveRowX =  d3.scaleLinear()
					  .domain(rowRange)
					  .range([ 0, waveRowWidth ]);

	var waveRowY = d3.scaleLinear()
	                 .domain([0, 1])
	                 .range([(waveRowHeight + waveRowYpadding) * (indx + 1) - waveRowYpadding,
	                	     (waveRowHeight + waveRowYpadding) * indx + waveRowYpadding] );
	if (signalType.name === T_BIT){
		renderBitLine(g, data, signalWidth, waveRowHeight, waveRowYpadding,
				 waveRowX, waveRowY)
	 } else {
		 var vldMask = mask(signalType.width)
		 var rectG =  g.selectAll("value-rect")	
					   .data(data)
					   .enter()
					   .append("g")	
					   .attr("transform", function(d) {
						  return "translate(" + waveRowX(d[0]) + " ," + (waveRowY(0) - waveRowHeight + waveRowYpadding)  + ")"
					   }).attr("class", function(d){ 
						   if(valVld(d[1]) != vldMask){
							   return "value-rect-invalid"
						   } else {
							   return "value-rect-valid"
						   }
					   })
					   
		 rectG.append("rect")
		   .attr("height", waveRowHeight - waveRowYpadding)
		   .attr("width",  function (d, indx){ 
			 			if (indx+1 == data.length){
			 				var next = d[0]+1
			 			} else {
			 				var next = data[indx+1][0]
			 			}
		               return waveRowX(next-d[0]) 
		    })
		   .attr('rx', 20)
		   .attr('ry', 20)
		   .attr("class", function(d){ 
		 	  if(valVld(d[1]) != vldMask){
		 		 return "value-rect-invalid"
		 	  } else {
		 		 return "value-rect-valid"
		 	  }
		   })
		   
		 rectG
		   .append("text")
		   .text(function(d) {
			   return renderBitsHex(d[1])
		   })
		   .attr("x", function (d, indx){ 
	 			if (indx+1 == data.length){
	 				var next = d[0]+1
	 			} else {
	 				var next = data[indx+1][0]
	 			}
            return waveRowX(next-d[0]) / 2 
		   })
		   .attr("y", (waveRowHeight) / 2 )
		   
	}
	//g.append("text")
	// .data(data)
	// .enter()
    // .text(function(d) {
    //	 return renderer(d[1], width)
    // })
    // .attr("x", function(d) {
    //     return waveRowX(d[0]);
    // })
    // .attr("y", function(d, i) {
    //     return waveRowY(0) - waveRowHeight;
    // })
    // .attr('class', "value-text")
}



// imple graph with grid lines in v4 https://bl.ocks.org/d3noob/c506ac45617cf9ed39337f99f8511218
function make_x_gridlines() {		
    return d3.axisBottom(x)
             .ticks(rowRange[1] - rowRange[0] + 1)
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
var signalNames = signalData.map(function(d){
	return d[0]
})

signalData.forEach(function(data, indx){
	renderWaveRow(indx, data[1], data[2], rowRange)
})