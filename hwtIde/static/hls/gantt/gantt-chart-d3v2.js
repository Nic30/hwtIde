

d3.gantt = function(placeholder) {
    var FIT_TIME_DOMAIN_MODE = "fit";
    var FIXED_TIME_DOMAIN_MODE = "fixed";

    var margin = {
        top : 20,
        right : 40,
        bottom : 20,
        left : 150
    };
    var timeDomainStart = 0;
    var timeDomainEnd = 1000;
    var timeDomainMode = FIT_TIME_DOMAIN_MODE;// fixed or fit
    var taskTypes = [];
    var taskStatus = [];
    var height = document.body.clientHeight - margin.top - margin.bottom - 5;
    var width = document.body.clientWidth - margin.right - margin.left - 5;

    var tickFormat = d3.format("d");

    var keyFunction = function(d) {
        return d.start + d.taskName + d.end;
    };

    var x = d3.scaleLinear()
              .domain([timeDomainStart, timeDomainEnd])
              .range([0, width])
              .clamp(true);

    var y = d3.scaleBand()
              .domain(taskTypes)
              .rangeRound([0, height - margin.top - margin.bottom ], .1);

    var rectTransform = function(d) {
    	return "translate(" + x(d.start) + "," + y(d.taskName) + ")";
    };

    var xAxis = d3.axisBottom()
                  .scale(x)
                  .tickFormat(tickFormat)
                  .tickSize(8)
                  .tickPadding(8);

    var yAxis = d3.axisLeft().scale(y).tickSize(0);

    var initTimeDomain = function() {
        if (timeDomainMode === FIT_TIME_DOMAIN_MODE) {
            if (tasks === undefined || tasks.length < 1) {
                timeDomainStart = 0;
                timeDomainEnd = 1000;
                return;
            }
            tasks.sort(function(a, b) {
                return a.end - b.end;
            });
            timeDomainEnd = tasks[tasks.length - 1].end;
            tasks.sort(function(a, b) {
                return a.start - b.start;
            });
            timeDomainStart = tasks[0].start;
        }
    };

    var initAxis = function() {
        x = d3.scaleTime()
              .domain([ timeDomainStart, timeDomainEnd ])
              .range([ 0, width ])
              .clamp(true);
        y = d3.scaleBand()
              .domain(taskTypes)
              .rangeRound([ 0, height - margin.top - margin.bottom ], .1);
        xAxis = d3.axisBottom()
                  .scale(x)
                  .tickFormat(tickFormat)
                  .tickSize(8)
                  .tickPadding(8);

        yAxis = d3.axisLeft()
                  .scale(y)
                  .tickSize(0);
    };

    function gantt(tasks) {

        initTimeDomain();
        initAxis();

        var svg = placeholder.append("svg")
                    .attr("class", "chart")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom)
                    .append("g")
                    .attr("class", "gantt-chart")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom)
                    .attr("transform",
                          "translate(" + margin.left + ", " + margin.top + ")");

        svg.selectAll(".chart")
           .data(tasks, keyFunction)
           .enter()
           .append("rect")
           .attr("rx", 5)
           .attr("ry", 5)
           .attr("class", function(d) {
               if (taskStatus[d.status] == null) {
                   return "bar";
               }
               return taskStatus[d.status];
           })
           .attr("y", 0)
           .attr("transform", rectTransform)
           .attr("height", function(d) {
                return y.bandwidth();
           })
           .attr("width", function(d) {
               return x(d.end) - x(d.start);
           });

        svg.append("g")
           .attr("class", "x axis")
           .attr("transform", "translate(0, " + (height - margin.top - margin.bottom) + ")")
           .transition()
           .call(xAxis);

        svg.append("g")
           .attr("class", "y axis")
           .transition()
           .call(yAxis);

        return gantt;
    }

    gantt.placeholder = placeholder;

    gantt.redraw = function(tasks) {

        initTimeDomain();
        initAxis();

        var svg = gantt.placeholder.select("svg");

        var ganttChartGroup = svg.select(".gantt-chart");
        var rect = ganttChartGroup.selectAll("rect").data(tasks, keyFunction);

        rect.enter()
            .insert("rect", ":first-child")
            .attr("rx", 5)
            .attr("ry", 5)
            .attr("class", function(d) {
                if (taskStatus[d.status] == null) {
                    return "bar";
                }
                return taskStatus[d.status];
            })
            .transition()
            .attr("y", 0).attr("transform", rectTransform)
            .attr("height", function(d) {
                return y.bandwidth();
            })
            .attr("width", function(d) {
                return (x(d.end) - x(d.start));
            });

        rect.transition()
            .attr("transform", rectTransform)
            .attr("height", function(d) {
                    return y.bandwidth();
            })
            .attr("width", function(d) {
            	return (x(d.end) - x(d.start));
            });

        rect.exit().remove();

        svg.select(".x").transition().call(xAxis);
        svg.select(".y").transition().call(yAxis);

        return gantt;
    };

    gantt.margin = function(value) {
        if (!arguments.length)
            return margin;
        margin = value;
        return gantt;
    };

    gantt.timeDomain = function(value) {
        if (!arguments.length)
            return [ timeDomainStart, timeDomainEnd ];
        timeDomainStart = value[0]
        timeDomainEnd = value[1]
        return gantt;
    };

    /**
     * @param {string}
     *            vale The value can be "fit" - the domain fits the data or
     *            "fixed" - fixed domain.
     */
    gantt.timeDomainMode = function(value) {
        if (!arguments.length)
            return timeDomainMode;
        timeDomainMode = value;
        return gantt;

    };

    gantt.taskTypes = function(value) {
        if (!arguments.length)
            return taskTypes;
        taskTypes = value;
        return gantt;
    };

    gantt.taskStatus = function(value) {
        if (!arguments.length)
            return taskStatus;
        taskStatus = value;
        return gantt;
    };

    gantt.width = function(value) {
        if (!arguments.length)
            return width;
        width = +value;
        return gantt;
    };

    gantt.height = function(value) {
        if (!arguments.length)
            return height;
        height = +value;
        return gantt;
    };

    gantt.tickFormat = function(value) {
        if (!arguments.length)
            return tickFormat;
        tickFormat = value;
        return gantt;
    };

    return gantt;
};
