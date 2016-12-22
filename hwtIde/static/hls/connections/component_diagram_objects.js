function drawExternalPorts(svgGroup, exterPortNodes){
	svgGroup.selectAll(".external-port").remove();
	var IMG_WIDTH = 30;
	var externalPorts = svgGroup.selectAll(".external-port")
		.data(exterPortNodes)
		.enter()
		.append("g")
		.classed({"external-port" :true});
	
	// adding external port icon
	externalPorts.append("image")
	.attr("xlink:href", function(d) { 
		return "/static/hls/connections/graphic/INshort.png"; 
	})
	.attr("x", function(d) {
		return (d.direction == DIRECTION.IN)?-IMG_WIDTH:0;
	})
	.attr("width", IMG_WIDTH)
	.attr("height", PORT_HEIGHT);
	// adding text for external port
	externalPorts.append("text")
		.attr("x", function(d) {
			return (d.direction == DIRECTION.IN)?-IMG_WIDTH:IMG_WIDTH;
		})
		.attr("y", PORT_HEIGHT -1)
		.text(function(d) {
			return d.name;
		})
		.attr('text-anchor', function(d){
			return (d.direction == DIRECTION.IN)?"end":'start';
		})
	// positioning whole g of external port
	externalPorts.attr("transform", function(d) {
		if (d.direction == DIRECTION.IN){
			var x = d.x + d.width +10;
			var y = d.y +1.5* PORT_HEIGHT;
		}else{
			var x = d.x -10;
			var y = d.y + 1.5* PORT_HEIGHT;
		}
		return "translate(" + x + "," + y + ")"; 
	})
	
	return externalPorts;
}


function drawComponents(svgGroup, componentNodes){
	//alias component body
	svgGroup.selectAll(".component").remove()
	var componentWrap = svgGroup.selectAll(".component")
		.data(componentNodes)
		.enter()
		.append("g")
	    .classed({"component": true})
	    .attr("transform", function (d) {
			return "translate(" + d.x + "," + d.y + ")";
		});
	
	// body background
	componentWrap.append("rect")
	    .attr("rx", 5) // this make rounded corners
	    .attr("ry", 5)
	    .attr("border", 1)
	    .attr("stroke", "#BDBDBD")
	    .attr("stroke-width", "1")
	    .attr("fill", "url(#blue_grad)")
	    //.style("filter", "url(#dropShadow)")
	    .attr("width", function(d) { return d.width})
	    .attr("height", function(d) { return d.height});

	componentWrap.append('text')
		.classed({"component-title": true})
		.attr("y", 0)	
		.attr("x", function(d){
			return d.width/2;
		})
		.text(function(d) {
		    return d.name;
		});

	// [TODO] porty s dratkem ven z komponenty, ruzne typy portu viz stream/bus/wire ve Vivado
	// input port wraps
	var port_inputs = componentWrap.append("g")
		.attr("transform", function(d) { 
			return "translate(" + 0 + "," + 2*PORT_HEIGHT + ")"; 
		})
		.selectAll("g .port-input")
		.data(function (d){
			return d.inputs;
		})
		.enter()
		.append('g')
		.classed({"port-input": true})
		.on("click", onPortClick)
		.on("mousemove", onPortMouseMove)
		.on("mouseout", onPortMouseOut);

	// input port icon [TODO] only for special types of connection, this is only example how to use it
	port_inputs.append("image")
		.attr("xlink:href", function(d) { 
			return "/static/hls/connections/graphic/arrow_right.ico"; 
		})
		.attr("y", function(d, i){
			return (i-0.5)*PORT_HEIGHT;
		})
		.attr("width", 10)
		.attr("height", PORT_HEIGHT);
	
	// portName text [TODO] intelligent alignment of port name
	port_inputs.append('text')
		.attr("x", 10)
		.attr("y", function(d, i){
			return (i+0.3)*PORT_HEIGHT;
		})
		.attr("height", PORT_HEIGHT)
		.text(function(port) { 
			return port.name; 
		});
	
	// output port wraps
	var port_out = componentWrap.append("g")
		.attr("transform", function(d) { 
			var componentWidth = d3.select(this).node().parentNode.__data__.width;
			return "translate(" + componentWidth + "," + 2*PORT_HEIGHT + ")"; 
		})
		.selectAll("g .port-group")
		.data(function (d){
			return d.outputs;
		})
		.enter()
		.append('g')
		.classed({"port-output": true})
		.on("click", onPortClick)
		.on("mousemove", onPortMouseMove)
		.on("mouseout", onPortMouseOut);

	//  output port image
	port_out.append("image")
		.attr("xlink:href", function(d) { 
			return "/static/hls/connections/graphic/arrow_right.ico"; 
		})
		.attr("x", -10)
		.attr("y", function(d, i){
			return (i-0.5)*PORT_HEIGHT;
		})
		.attr("width", 10)
		.attr("height", PORT_HEIGHT);	

	// portName text
	port_out.append('text') 
		.attr("x", -10)	// posunuty okrej o 10 dolava
		.attr("y", function(d, i){
			return (i+0.3)*PORT_HEIGHT; //Zuzana: neviem ci je spravne manualne posunutie prvku ale vyzera to dobre, zalezi aj od velkosti fontu
		})
		.attr("height", PORT_HEIGHT)
		.text(function(port) { 
			return port.name; 
		});


	
	return componentWrap;
}