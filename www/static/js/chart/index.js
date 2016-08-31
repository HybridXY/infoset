function AreaChart(uid, datapoint, target, width, height, fill) {
	/*
	Function for creating and appending charts to DOM

    Args:
        uid: Unique Hash of Agent
        datapoint: uniqu

    Returns:
        Home Page
	*/
	//Create URL to request data
	var dataroute = "/fetch/agent/graph/" + uid + "/" + datapoint;
	var graph_width = width;
	var graph_height = height;

	var margin = {top: 20, right: 20, bottom: 30, left: 20},
	    width = graph_width - margin.left - margin.right,
	    height = graph_height - margin.top - margin.bottom;


	//Scale x axis properly
	var x = d3.time.scale()
	    .range([0, width]);

	//Scale y axis properly
	var y = d3.scale.linear()
	    .range([height, 0]);


	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom")
	    .innerTickSize(-height)
	    .outerTickSize(0)
	    .tickPadding(10);


	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left")
	    .innerTickSize(-width)
	    .outerTickSize(0)
	    .tickPadding(10);

	var line = d3.svg.line()
		.defined(function(d) {return d.y; })
	    .x(function(d) { return x(d.x); })
	    .y(function(d) { return y(d.y); });

	var area = d3.svg.area()
		.defined(line.defined())
	    .x(function(d) { return x(d.x); })
	    .y0(height)
	    .y1(function(d) { return y(d.y); });

	var svg = d3.select(target).append("svg")
	    .attr("width", width + margin.left + margin.right)
	    .attr("height", height + margin.top + margin.bottom)
	    .attr("class", "center-block")
	  	.append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    
    d3.json(dataroute, function(error, data){

		data.forEach(function(d) { d.x = new Date(d.x * 1000); });
		 

		x.domain(d3.extent(data, function(d) { return d.x; }));
		y.domain([0, d3.max(data, function(d) { return d.y; })]);

		svg.append("path")
		  .datum(data)
		  .attr("class", "area")
		  .attr("fill", fill)
		  .attr("d", area);

		svg.append("g")
		  .attr("class", "x axis")
		  .attr("class", "grid")		  
		  .attr("transform", "translate(0," + height + ")")
		  .call(xAxis);


		  svg.append("g")			
		  .attr("class", "grid")
		  .call(yAxis); 

		svg.append("g")
		  .attr("class", "y axis")
		  .attr("class", "grid")		  
		  .call(yAxis)
		.append("text")
		  .attr("transform", "rotate(-90)")
		  .attr("y", 6)
		  .attr("dy", ".71em")
		  .style("text-anchor", "end")
		  .text("Data");
    });
}

function StackedArea(uid, datapoint, target, width, height, colors){
	
	var dataroute = "/fetch/agent/graph/stacked/" + uid + "/" + datapoint;
	var margin = {top: 20, right: 20, bottom: 30, left: 80},
	    width = 630 - margin.left - margin.right,
	    height = 240 - margin.top - margin.bottom;

	var x = d3.time.scale()
	    .range([0, width]);

	var y = d3.scale.linear()
	    .range([height, 0]);

	var z = d3.scale.category20c();
	
	if (datapoint === "memory") {
		colors = ['#71D5C3', '#009DB2', '#21D5C3', '#98e1d4', '#f0e0a0'];		
	} else if (datapoint === "load") {
        colors = ['#F37372','#FA9469','#FDBB5D']
	}


	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom")
	    .innerTickSize(-height)
	    .outerTickSize(0)
	    .tickPadding(10);

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left")
	    .innerTickSize(-width)
	    .outerTickSize(0)
	    .tickPadding(10);

	var stack = d3.layout.stack()
	    .offset("zero")
	    .values(function(d) { return d.values; })
	    .x(function(d) { return d.x; })
	    .y(function(d) { return d.y; });

	var nest = d3.nest()
	    .key(function(d) { return d.group; });

	var area = d3.svg.area()
	    .x(function(d) { return x(d.x); })
	    .y0(function(d) { return y(d.y0); })
	    .y1(function(d) { return y(d.y0 + d.y); });

	var svg = d3.select(target).append("svg")
	    .attr("width", width + margin.left + margin.right)
	    .attr("height", height + margin.top + margin.bottom)
	  .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.json(dataroute, function(error, data) {
	  if (error) throw error;
	  
	  data.forEach(function(d) { d.x = new Date(d.x * 1000); });

	  if (datapoint === "memory") {
  		  data.forEach(function(d) { d.y = d.y / 10000000000; });
	  }
	  
	  var layers = stack(nest.entries(data));

	  x.domain(d3.extent(data, function(d) { return d.x; }));
	  y.domain([0, d3.max(data, function(d) { return d.y0 + d.y; })]);

	  svg.selectAll(".layer")
	      .data(layers)
	    .enter().append("path")
	      .attr("class", "layer")
	      .attr("d", function(d) { return area(d.values); })
	      .style("fill", function(d, i) { return colors[i]; })

	  svg.append("g")
	      .attr("class", "x axis")
	      .attr("class", "grid")
	      .attr("transform", "translate(0," + height + ")")
	      .call(xAxis);

	  svg.append("g")
	      .attr("class", "y axis")
  	      .attr("class", "grid")
	      .call(yAxis);
	});
}