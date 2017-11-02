
function renderBitLine(parent, data, signalWidth, waveRowHeight, waveRowYpadding, waveRowX, waveRowY){
	var invalidRanges = []
	var lastInvalid = null
	var lineData = []
	var lastD=null;
	data.forEach(function (d){
		if (lastD != null && !d[1] != lastD[1]) {
			lineData.push([ d[0], lastD[1] ])
		}
		lastD = d
		lineData.push(d)

		if(d[1].indexOf('x') < 0){
			if (lastInvalid == null)
				lastInvalid = d
		} else
			if (lastInvalid != null){
				invalidRanges.push([lastInvalid[0], d[0]])
				lastInvalid = nullrenderWaveRow // [TODO]
			}
		
	})
	
    var line = d3.line()
    	     .x(function(d) {
    	          return waveRowX(d[0]);
    	      })
    	     .y(function(d) {
    	    	 let _d = d[1]
    	    	 if (_d == '1'){
    	     	    return waveRowY(1);
    	    	 } else if (_d == '0' || _d == 'x') {
    	    		 return waveRowY(0)
    	    	 } else {
    	    		 throw new Error("Not implemented: ", _d)
    	    	 }
    	      })
    	      .curve(d3.curveStepAfter)
		
    // wave line
    parent.append("g")
     .attr("clip-path", "url(#clip)")
     .append("path")
     .datum(lineData)
     .attr("class", "value-line")
     .attr("d", line)

	
	// Add the scatterplot
	parent.selectAll("rect")	
	 .data(invalidRanges)
	 .enter()
     .append('g')
	 .attr("class", "value-rect-invalid")
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
}

function renderBitsLine(parent, data, signalWidth, waveRowHeight,
		                waveRowYpadding, waveRowX, waveRowY) {
	var waveRowHeight = 20
	var waveRowYpadding = 5

	var rectG =  parent.selectAll("value-rect")	
				       .data(data)
				       .enter()
				       .append("g")	
				       .attr("transform", function(d) {
				  	     return "translate(" + 
				  	     		[waveRowX(d[0]) , (waveRowY(0) - waveRowHeight + waveRowYpadding)]
				  	     					  + ")"
				       }).attr("class", function(d){ 
				        if(d[1].indexOf('x') < 0){
				  	      return "value-rect-valid"
				        } else {
				  	      return "value-rect-invalid"
				        }
				       })
				   
	 rectG.append("path")
	 	  .attr("d", function(d, indx){
	 		  //  <==> like shape
 	 		  if (indx+1 == data.length){
	 	 		var next = d[0]+1
		 	  } else {
		 	  	var next = data[indx+1][0]
		 	  }
	 	      var right = waveRowX(next-d[0])
	 	      var top = waveRowHeight
	 	  	  return 'M '+ [0, top/2] + 
	 	  	         ' L ' + [5, top] + 
	 	  	         ' L '+ [right - 5, top] + 
	 	  	         ' L '+ [right, top/2] +
	 	  	         ' L '+ [right - 5, 0] + 
	 	  	         ' L '+ [5, 0] +' Z'
	 	  })
	   
	 rectG
	   .append("text")
	   .text(function(d) {
		   return d[1]
	   })
	   .attr("x", function (d, indx){ 
			if (indx+1 == data.length){
				var next = d[0]+1
			} else {
				var next = data[indx+1][0]
			}
			return waveRowX(next-d[0]) / 2 
	   })
	   .attr("y", (waveRowHeight) / 2 +  waveRowYpadding)
}

function renderWaveRow(indx, signalType, data, graph){
	var waveRowHeight = graph.sizes.row.height;
	var waveRowYpadding = graph.sizes.row.ypadding;
	var rowRange = graph.sizes.row.range;
	var waveRowX = graph.waveRowX;
	var parent = graph.g;
	var waveRowY = d3.scaleLinear()
	                 .domain([0, 1])
	                 .range([(waveRowHeight + waveRowYpadding) * (indx + 1) - waveRowYpadding,
	                	     (waveRowHeight + waveRowYpadding) * indx + waveRowYpadding] );
	var last = data[data.length-1]
	if(last[0]< rowRange[1])
		data.push([rowRange[1], last[1]])
	
	if (signalType.name === T_BIT){
		var signalWidth = 1
		renderBitLine(parent, data, signalWidth, waveRowHeight, waveRowYpadding,
				      waveRowX, waveRowY)
	} else {
		 renderBitsLine(parent, data, signalType.width, waveRowHeight, waveRowYpadding, 
				        waveRowX, waveRowY)
	}
}