# Temporal Specialization 

Temporal Specialization can be used to develop specialized system call 
filters for
server applications based on their phase of execution. We differentiate
 between the
initialization phase and serving phase, where the former is related to
bootstrap operations performed by applications and the latter is related to
operations which are continuously executed by the server to handle client
requests.

## Overview of steps to achieve Temporal Specialization
1. Generate LLVM IR after Link-time Optimization(LTO) for the application. 
2. Generate call graph for the application and the shared libraries it uses. 
3. Use developer provided function name as entry point into the serving phase. 
4. Extract set of system calls that would be used in serving phase. 
5. Create seccomp filters to block execution of any other system call. 


## Artifacts Evaluation

This repository has been created for the Artifact Evaluation process of Usenix
Security 2020. We have provided the resources to reproduce all of the main 
results presented in the paper. We have listed what will and will not be
covered through the scripts presented in this repository below.

Will be covered:
* The entire toolchain:
    * LLMV Pass for Type-based pruning
    * LLVM Pass for Address-taken pruning
    * Python scripts for generating list of filtered system calls
    * Python scripts for comparing results with library debloating
* Security evaluation - shellcodes and ROP
    * Python scripts to perform security evaluation for shellcodes and ROP payloads

Will NOT be covered:
* Kernel security evaluation
* Installing SECCOMP filters in applications (We have presented
instructions on how to perform this manually)

## Description

The source code along with all the helper scripts are part of this repo. 
Before running evaluations, it is necessary to get all the prerequisites
installed. These include Clang+LLVM and modified SVF. 

There are 2 ways to set up these prerequisites: 
1. Use a prebuilt container, or
2. Install everything on your system. 
 
Currently our prototype consists of two main parts. The analysis is mainly
done through LLVM passes, which require LLVM-7. Then we use python scripts to
further parse and analyze the results of the LLVM passes. 

To ease the process, we have provided the bitcode for tested applications
in the *bitcodes* folder of this repository.

**To Run using docker container**
```
sudo apt install docker.io
```
For steps on how to run the analysis, refer to docker-build/README.md
Once done, continue evaluation by following from step 3. 

**To Run all steps on your system**

Follow these steps to install all required applications before starting the
analysis. 
 
## 1. Initialization
This repository has multiple submodules which must be loaded using the
following command:
```
git submodule update --init --recursive
```

## 2. LLVM Passes
Install Clang-7 and LLVM-7
```
sudo apt install clang-7
sudo apt install llvm-7
```

### 2.1 Compiling SVF

The submodule SVF in the repository holds our modified SVF source code. You
can follow the commands for compiling it using the original commands from the
[repository](https://github.com/SVF-tools/SVF).
**Please make sure to use the same LLVM version for both compiling SVF and any
application you would like to use. We have only tested LLVM-7 with our
toolchain.**

### 2.2 Generating bitcodes

Sources for all tested applications can be found in: [To Be Added] 
To build each application using LTO and generate bitcode, run
```
$./configure CC=clang-7 CFLAGS="-flto -O2"  LDFLAGS="-flto -Wl,-plugin-opt=save-temps" 
$ make clean; make
```
This generates and saves bitcodes at the end of each compiler step. We use the final 
IR generated named "<application>.0.5.precodegen.bc"

For convenience, we have pre-generated these IRs and they can be found in
bitcodes/ .

## 3. Call-graph extraction
### SVF with Type-based Pruning (callgraph-wtype-based)
We use Andersen's points-to analysis algorithm to generate the callgraph of
the application. We have modified [SVF](https://github.com/SVF-tools/SVF) to
prune spurious edges which do not match argument types (only struct types).
This is the main element used in our temporal specialization approach.

```
export SVF_HOME=[path-to-svf-home]  (e.g. in Docker image: /usr/svf/)
export PATH=$SVF_HOME/Release-build/bin:$PATH
```
You can use the following command to make sure the path is set correctly:
```
which wpa
```
It should return the path to the wpa binary.
You should run the following command to generate the call graph in the DOT
format.
```
wpa -print-fp -ander -dump-callgraph ./bitcodes/httpd.apr.bc
```
It should take around 15 minutes to run for Apache httpd mentioned
above. But it can vary depending on the application.
Running the pass above generates two files name callgraph\_final.dot and
callgraph\_initial.dot. We will use the first to generate our main callgraph. 
We need to convert it to a more human-readable format. To do so we will use
the convertSvfCfgToHumanReadable.py script.
```
python3.7 convertSvfCfgToHumanReadable.py callgraph_final.dot > callgraphs/httpd.apr.svf.type.cfg
```
We will need the generated call graph for our final analysis where we identify
which system calls can be filtered after entering the serving phase.

### Call Graph with Direct Edges Only (callgraph-direct-only)
We need to generate a simple call graph, containing only edges with direct
callsites and without any indirect callsites. This is used for pruning
inaccessible targets of indirect callsites in the next step.
We have generated a simple program analysis tool (spa) which is an LLVM pass 
in our modified SVF repository.

```
spa -condition-cfg ./bitcodes/httpd.apr.bc 2>&1 | tee httpd.apr.svf.conditional.direct.calls.cfg
```
We need this call graph for pruning the inaccessible targets of callsites.
Please store this file for further reference.

### Function Address Allocation Analysis (callgraph-fp-allocations)
The last LLVM pass is the function pointer allocation analysis tool. This tool
is used to extract places in the code where functions are assigned to function
pointers. The following command can be used to parse the application bitcode and
generate the function pointer allocation file.
```
spa -simple ./bitcodes/httpd.apr.bc 2>&1 | tee httpd.apr.svf.function.pointer.allocations.wglobal.cfg
```
We will use the combination of this file and the file generated in the
previous step to create the pruned call graph.

## 4. Python Scripts
After generating the required call graphs through LLVM passes we use python
scripts to combine the graphs and identify which system calls can be futher 
filtered in the serving phase.

### Call Function Pointer Target Pruning (callgraph-final)
We first have to merge all the previously generated call graphs into our final
call graph which has its inaccessible callsite targets pruned. 

For this, we use the following script. We need to pass the name of the function name 
which starts executing upon when the application is run. This is provided using 
--funcname argument.
```
python3.7 graphCleaner.py --fpanalysis --funcname main --output callgraphs/httpd.apr.svf.new.type.fp.wglobal.cfg --directgraphfile callgraphs/httpd.apr.svf.conditional.direct.calls.cfg --funcpointerfile callgraphs/httpd.apr.svf.function.pointer.allocations.wglobal.cfg -c callgraphs/httpd.apr.svf.type.cfg
```
Arguments:

--funcname: Function which is executed upon running the application. Usually main,
unless any test is being run.

--output: Path to store the final call graph.

--directgraphfile: Path to the call graph generated in the
**callgraph-direct-only** step.

--funcpointerfile: Path to the call graph generated in the
**callgraph-fp-allocations** step.

-c: Path to the main call graph generated by running our modified SVF with
type-based pruning (**callgraph-wtype-based**)

### Filtered System Call Extraction
In this step we use the final call graph along with other artifacts generated
beforehand to create the final list of system calls which can be filtered
after the application enters the serving phase.

This script has a configuration file which needs to be modified to correspond
to the filenames used in the previous sections. In case you have used the
default filenames provided in this guide, you do not need to modify anything
and can proceed to the next step. The call graphs generated in the previous
steps must exist in the path provided by the *--cfgpath* option. If you have
changed any of the file names modify them respectively in the JSON file named
app.to.properties.json.

```
mkdir outputs
mkdir stats
python3.7 createSyscallStats.py -c ./callgraphs/glibc.callgraph --apptopropertymap app.to.properties.json --binpath ./binaries --outputpath outputs/ --apptolibmap app.to.lib.map.json --sensitivesyscalls sensitive.syscalls --sensitivestatspath stats/sensitive.stats --syscallreductionpath stats/syscallreduction.stats --libdebloating --othercfgpath ./otherCfgs/ --cfgpath callgraphs
```
We will describe each argument in the following sections.

**-c** As we mention in the paper, we use a one-time approach to generate a call
graph for glibc. We pass the call graph of glibc through this argument.

**--libdebloating**
We have the option of comparing and using library debloating in our temporal
specialization. This is enabled through passing this argument. We need to
provide the call graph for all libraries in this case. Explained further
below. We use the method proposed by
(piece-wise)[https://www.usenix.org/system/files/conference/usenixsecurity18/sec18-quach.pdf]
to generate statistics regarding the improvement compared with library
debloating. For the sake of simplicity we will suppose the libraries have each
been analyzed by a library debloating tool and their call graph has been
generated. We have provided the call graph for all libraries required by the
applications in our dataset in the *otherCfgs* folder. 
*The folder *libdebloating*
contains instructions on how to generate these call graphs for interested
users.*

**--othercfgpath**
In case we use the *libdebloating* option, we have to specify the path for all
library call graphs. We have provided the call graph for all libraries
required for the applications in our dataset in the *otherCfgs* folder.

**--sensitivesyscalls**
In our paper we have generated specific statistics regarding sensitive system
calls. The list of these system calls can be specified through an argument
passed to this script.

**--binpath**
As we mentioned in our paper, some applications and libraries make direct
system calls. We consider these direct system calls as necessary throughout
the application life cycle regardless of whether or not they are used in the
initialization or serving phase.

**--apptopropertymap**
We need to pass the name of the function executed upon starting the serving
phase through a configuration file. We also specify the path for our call
graphs using a JSON file. The apptopropertymap can be used to specify the path
to this file.

**--apptolibmap**
We also need to specify which libraries are used by each application. We have
already prepared this file for the applications in our dataset.

**--outputpath**
Path to the output folder where we will store the output files.

**--sensitivestatspath**
Path for file to store statistics on sensitive system calls.

**--syscallreductionpath**
Path for file containing statistics on system calls filtered in the serving
phase.

**--cfgpath**
We suppose all call graphs are stored in a specific folder. The name of each
call graph is specified in the JSON file.

**--singleappname**
The main JSON file has the option of enabling and disabling each application.
But in case you only want to run the analysis for one application without
modifying the JSON file, you can use this option and pass the name of your
requested application. The tool will only analyze this single application
bypassing the enable setting in the JSON file. The rest of the settings for
the application will still be read from the JSON file.


## 5. Security Evaluation

For security evaluation, we collected a set of 547 shellcodes payloads and 17 
ROP payloads. Using equivalence classes mentioned in the paper, a total of 
1726 shellcodes were generated. To run tests for applications, refer to 
security-evaluation/README.md.

Note that we have extended our payload database since the paper submission.
While the number of tested payloads in the paper is 566, in the camera-ready
version we plan to include results from our latest set which has 1726
shellcodes. Similarly, for ROP payloads we have extended our payload set from 13
to 16 ROP payloads. 
