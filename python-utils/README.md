# Python Utils

This repository is used as a set of tools which provide basic python
functionalities required across different projects. Each part of the repo has
been described in separate sections below.

## Call Graph

## Syscall Converter


##Call Graph Manipulation
The graph class can generally be used for any graph operations. We have 
gathered a set of pre-defined functionalities which are used in manipulating 
the call graph, which have been explained below:

### Function Pointer Analysis ###
There are cases which functions are only assigned to function pointers in certain 
paths of the call graph which aren't accessible from a specific starting 
point. In these cases, if the functions aren't ever called directly, since 
the point where their address is being taken is never reached in our respective 
path, we can remove any indirect invocations of these functions. We first 
need to run a Simple Program Analysis using our customized SVF, to create a 
graph showing where each function's address is being taken and use it to 
prune the graph.

```
python3.7 graphCleaner.py --fpanalysis --funcname main --output tmp.cfg --directgraphfile ~/webserver-asr/process-separation/scripts/httpd.svf.conditional.direct.calls.cfg --funcpointerfile ~/webserver-asr/process-separation/scripts/httpd.function.pointer.allocations.cfg -c ~/webserver-asr/process-separation/scripts/httpd.apr.svf.type.cfg
```
--fpanalysis: specifies we want to run the function pointer analysis
-c: initial call function graph
--output: path to store pruned CFG
--directgraphfile: path to CFG with direct function calls ONLY
--funcpointerfile: path to file consisting function pointer assignments (SPA result)
--funcname: function name which is our starting point (e.g. main)


### Condition Edge Removal ###
```
python3.7 graphCleaner.py --minremovable -c ~/webserver-asr/process-separation/scripts/httpd.apr.svf.type.fp.cfg --minremovestart main --minremoveend apr_proc_create --conditionalgraphfile ~/webserver-asr/process-separation/scripts/httpd.svf.conditional.direct.calls.cfg --minremovemaxdepth 10
```

## Prerequisites

This project has only been tested on Ubuntu 18.04. Due to usage of specific
debian-based tools (such as dpkg and apt-file) use on other operating systems
at your own risk.
All the scripts have been written in coordinance with python version 3.7.

## Authors

* **SeyedHamed Ghavamnia**

