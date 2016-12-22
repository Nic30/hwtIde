var expect = chai.expect;
var should = chai.should();

//it('2 nets going down and then left', function() {
//	var nodes = [ {
//		id : 4,
//		name : "selfReference",
//		inputs : [ "clk", "inC", "inD" ],
//		outputs : [ "c", "d" ]
//	} ];
//	// {"id":4, "portIndex":0}
//	var nets = [ {
//		"name" : "C",
//		"source" : {
//			"id" : 4,
//			"portIndex" : 0
//		},
//		"targets" : [ {
//			"id" : 4,
//			"portIndex" : 1
//		} ]
//	}, {
//		"name" : "D",
//		"source" : {
//			"id" : 4,
//			"portIndex" : 1
//		},
//		"targets" : [ {
//			"id" : 4,
//			"portIndex" : 2
//		} ]
//	}, ];
//
//	var links = generateLinks(nets);
//	resolveNodesInLinks(nodes, links);
//	components2columns(nodes, links);
//
//	var router = new NetRouter(nodes, links);
//	var grid = router.grid;
//	router.route();
//
//	var c = links[0];
//	var d = links[1];
//	
//	
//	// path around bottom of component without start
//	expect(c.path.length).to.equal(4);
//	expect(d.path.length).to.equal(3);
//
//	expect(c.start.vertical.length).to.equal(1);
//	expect(d.start.vertical.length).to.equal(1);
//	//expect(d.start).to.equal(c.path[0]);
//
//	for (var i = 0; i < 2; i++) {// two nodes under componet
//		var cp = c.path[i + 1];
//		var dp = d.path[i];
//		
//		//console.log(cp.pos());
//		expect(cp.pos()).to.deep.equal(dp.pos());
//
//		expect(cp.horizontal.length).to.equal(2);
//		expect(cp.vertical.length).to.equal(2);
//
//		expect(dp.horizontal.length).to.equal(2);
//		expect(dp.vertical.length).to.equal(2);
//
//	}
//
//});
it('isOnLineVerticaly', function() {
	var line = [[0,0], [0, 50]];
	expect(isOnLineVerticaly(line, [0,0])).to.be.true;
	expect(isOnLineVerticaly(line, [0,25])).to.be.true;
	expect(isOnLineVerticaly(line, [0,50])).to.be.true;
	expect(isOnLineVerticaly(line, [1,25])).to.be.false;
	
});

it('components2columns', function(){
 var data =	{   "nodes" : [{
        "id" : 1,
        "name" : "Component0",
        "inputs" : [ {"name" :"inA"}],
        "outputs" : [ {"name" :"outA"}]
    } , {
        "id" : 2,
        "name" : "outA",
        "isExternalPort" : true,
        "direction" : DIRECTION.OUT,
        "inputs" : [{"name" :"outA"} ],
        "outputs" : [ ]
    }, {
        "id" : 0,
        "name" : "inA",
        "isExternalPort" : true,
        "direction" : DIRECTION.IN,
        "inputs" : [ ],
        "outputs" : [{"name" :"outA"} ]
    }],
    "nets": [
        {"source" : {
            "id" : 0,
            "portIndex" : 0
          },
         "targets" : [{
            "id" : 1,
            "portIndex" : 0
         }]},
        {"source" : {
             "id" : 1,
             "portIndex" : 0
         },
         "targets" : [{
             "id" : 2,
             "portIndex" : 0
        }]}
    ]};
	var nets = data.nets;
	var nodes = data.nodes;
	COLUMN_WIDTH = findColumnWidth(nodes);
	checkDataConsistency(nodes, nets);
	
	var links = generateLinks(nets);
	resolveNodesInLinks(nodes, links);
	var columns = components2columns(nodes, links);
	expect(columns.length() ).to.equal(3)
	expect(columns.left[0].length ).to.equal(1)
	expect(columns.midleRight[0].length ).to.equal(1)
	expect(columns.midleRight[1].length ).to.equal(1)
	
	console.log(nodes)
 
});

