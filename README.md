# hwtIde

## Note that this is only proof of concept and this project will probably be never finished or fully working it exits in order to test the ideas before the become an independent software. The thing which will remain there is an prototype of original application and the final application is stored elsewhere.

HwtIde is web based prototype of IDE for https://github.com/Nic30/hwt .
It contains various tools for hardware development.


## Wave viewer
Prototype of wave viewer, input is vcd/outputs from HWT simulator in memory.
Using [d3-wave](https://github.com/Nic30/d3-wave) library.

## Connection editor
Simple component connection editor used for visualization of of hierarchical components and simple editing.

![Connections viewer](/doc/connections.png)

## Connection visualizer
Simple component connection visualizer for visualization of of hierarchical components. Using ELK (Eclipse Layout Kernel) and [d3-hwschematic](https://github.com/Nic30/d3-hwschematic) library. 


## HLS visualizations
* Gantt graph, pipeline mapping graphs etc.

![pepeline_graph](/doc/pipeline_graph.png)

![gantt](/doc/gantt.png)


# Installation
* NOT RECOMENDED, think of this as an example which we tried before a developing of real app.
* "pip3 install flask hwtLib hwtHls"
* download repo and run "npm install" in  hwtIde/static to download node packages for frontend

run by executing app.py


# Connected similar projects
* https://github.com/1138-4EB/hwd-ide

# Similar projects
* https://github.com/GIBIS-UNIFESP/wiRedPanda
* https://github.com/TerosTechnology/terosHDL
* https://github.com/YosysHQ/yosys
