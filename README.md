# hwtIde


HwtIde is web based prototype of IDE for https://github.com/Nic30/hwt .
It contains various tools for hardware development.


## Wave viewer
Prototype of wave viewer, input is vcd/outputs from HWT simulator in memory.

![Wave viewer](/doc/wave.png)

## Connection editor
Simple component connection editor used for visualization of of hierarchical components and simple editing.

![Connections viewer](/doc/connections.png)

## Connection visualizer
Simple component connection visualizer for visualization of of hierarchical components. Using ELK (Eclipse Layout Kernel).

![Connections viewer](/doc/connections_elk.png)


## HLS visualizations
* Gantt graph, pipeline mapping graphs etc.

![pepeline_graph](/doc/pipeline_graph.png)

![gantt](/doc/gantt.png)


# Installation
* NOT RECOMENDED, it is only prototype
* "pip3 install flask hwtLib hwtHls"
* download repo and run "npm install" in  hwtIde/static to download node packages for frontend

run by executing app.py
