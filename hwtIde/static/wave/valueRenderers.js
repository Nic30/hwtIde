function valCmp(a, b) {
	return (a[0] == b[0]) && (a[1] == b[1])
}
function valVal(a) {
	return a[0]
}
function valVld(a) {
	return a[1]
}
function mask(bits) {
	return (1 << bits) - 1
}
function renderBit(val, width) {
	if (val[0] == 1) {
		if (val[1])
			return "1"
		else
			return "0"
	} else {
		return "X"
	}
}
function renderBitsDec(val, width) {
	if (val[0] == mask(width)) {
		return val[0].toString()
	} else {
		return "X"
	}
}
function renderBitsHex(val, width) {
	var v = val[0].toString(16)
	var vld = val[1].toString(16)
	var chars = Math.ceil(width / 16)

	if (v.length < chars)
		v = "0".repeat(chars - v.length) + v

	for (var i = 0; i < chars; i++) {
		if (!(vld.length < i && vld[i] == 'f'))
			v[i] = 'X'
	}
	return "0x"+v
}


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

function renderBitsLine(parent, data, signalWidth, waveRowHeight, waveRowYpadding, waveRowX, waveRowY){
	var vldMask = mask(signalWidth)
	var waveRowHeight = 20
	var waveRowYpadding = 5

	var rectG =  g.selectAll("value-rect")	
				  .data(data)
				  .enter()
				  .append("g")	
				  .attr("transform", function(d) {
					  return "translate(" + 
					  		[waveRowX(d[0]) , (waveRowY(0) - waveRowHeight + waveRowYpadding)]
					  					  + ")"
				  }).attr("class", function(d){ 
				   if(valVld(d[1]) != vldMask){
					   return "value-rect-invalid"
				   } else {
					   return "value-rect-valid"
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
	 	  	         ' L '+[5, 0]+' Z'
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
	   .attr("y", (waveRowHeight) / 2 +  waveRowYpadding)
}

function renderWaveRow(indx, signalType, data, rowRange){
	var waveRowWidth = graphWidth
	var waveRowHeight = 20
	var waveRowYpadding = 5

	var waveRowX =  d3.scaleLinear()
					  .domain(rowRange)
					  .range([0, waveRowWidth]);

	var waveRowY = d3.scaleLinear()
	                 .domain([0, 1])
	                 .range([(waveRowHeight + waveRowYpadding) * (indx + 1) - waveRowYpadding,
	                	     (waveRowHeight + waveRowYpadding) * indx + waveRowYpadding] );
	if (signalType.name === T_BIT){
		var signalWidth = 1
		renderBitLine(g, data, signalWidth, waveRowHeight, waveRowYpadding,
				 waveRowX, waveRowY)
	 } else {
		 renderBitsLine(parent, data, signalType.width, waveRowHeight, waveRowYpadding, 
				 waveRowX, waveRowY)
	}
}