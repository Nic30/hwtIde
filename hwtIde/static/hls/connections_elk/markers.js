
function addMarkers(svg) {
	var defs = svg.append("defs")
        function addMarker(id, arrowPath, arrowTranslate) {
          var cont = defs.append("g")
	    .attr("id", id)
            .attr("class", "port")
	    .append("path")
	    .attr("d", arrowPath)
            .attr("transform", "translate(" + arrowTranslate[0] + ", " + arrowTranslate[1] + ")");
        
        }
        var right = "M 0 4  2 4  2 0  7 5  2 10  2 6  0 6 Z";
        var left = "M 7 4  5 4  5 0  0 5  5 10  5 6  7 6 Z";
        addMarker("westInPortMarker", right, [0, -4])
	addMarker("westOutPortMarker", left, [0, -4])
        addMarker("eastInPortMarker", left, [0, -4])
        addMarker("eastOutPortMarker", right, [0, -4])
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
