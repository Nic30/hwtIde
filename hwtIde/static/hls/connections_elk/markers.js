
function addMarkers(svg) {
    var defs = svg.append("defs");
    var w = 7;
    var h = 10;
    var PORT_PIN_SIZE = [7, 20];
    function addMarker(id, arrowTranslate, arrowRotate=0) {
    	var rightArrow = "M 0 4  2 4  2 0  7 5  2 10  2 6  0 6 Z";
        var trans = "";
        if (arrowRotate != 0)
        	trans += "rotate(" + arrowRotate + ")";
        if (arrowTranslate[0] != 0 || arrowTranslate[1] != 0)
        	trans += "translate(" + arrowTranslate[0] + ", " + arrowTranslate[1] + ")";
        var cont = defs.append("g")
        .attr("id", id)
        .attr("class", "port")
        .append("path")
        .attr("d", rightArrow)
        if (trans)
        	cont
            .attr("transform", trans);
    }
    addMarker("westInPortMarker", [0, h/2]);
    addMarker("westOutPortMarker",[0, -h*1.5], 180);

    addMarker("eastInPortMarker", [-w, -h*1.5], 180);
    addMarker("eastOutPortMarker",[0, h/2]);

    addMarker("northInPortMarker", [w/2, -h], 90);
    addMarker("northOutPortMarker",[w/2, 0], 270);

    addMarker("southInPortMarker", [w/2, h], 270);
    addMarker("southOutPortMarker",[w/2, 0], 90);
}

var PORT_MARKERS = {
		"WEST": {
			"INPUT": "#westInPortMarker",
			"OUTPUT": "#westOutPortMarker"},
		"EAST": {
			"INPUT": "#eastInPortMarker",
			"OUTPUT": "#eastOutPortMarker"},
		"NORTH": {
			"INPUT": "#northInPortMarker",
			"OUTPUT": "#northOutPortMarker"},
	    "SOUTH": {
	    	"INPUT": "#southInPortMarker" ,
	    	"OUTPUT": "#southOutPortMarker"},
};

function getIOMarker(d) {
    var side = d.properties.portSide;
    var portType = d.direction;
    var marker = PORT_MARKERS[side][portType];
    if (marker === undefined) {
    	throw new Error("Wrong side, portType", side, portType)
    }
    return marker;
}
