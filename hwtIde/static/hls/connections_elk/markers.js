
function addMarkers(svg) {
	var defs = svg.append("defs")
	
	defs.append("g")
	   .attr("id", "westInPortMarker")
	   .append("path")
	   .attr("d", "M 2 -4  7 1  2 6 Z")
	
	defs.append("g")
	   .attr("id", "westOutPortMarker")
	   .append("path")
	   .attr("d", "M 7 -4  2 1  7 6 Z")
	
	defs.append("g")
	   .attr("id", "eastInPortMarker")
	   .append("path")
	   .attr("d", "M 0 -5  -5 0  0 5 Z")
	
	defs.append("g")
	   .attr("id", "eastOutPortMarker")
	   .append("path")
	   .attr("d", "M -5 -5  0 0  -5 5 Z")
}

function getIOMarker(d) {
	var side = d.properties.portSide;
	var portType = d.direction;

	if (side == "WEST") {
		if (portType == "INPUT") {
			return "#westInPortMarker";
		} else if (portType == "OUTPUT") {
			return "#westOutPortMarker";
		}
	} else if (side == "EAST") {
		if (portType == "INPUT") {
			return "#eastInPortMarker";
		} else if (portType == "OUTPUT") {
			return "#eastOutPortMarker";
		}
	}
	throw new Error("Wrong side, portType", side, portType)
}
