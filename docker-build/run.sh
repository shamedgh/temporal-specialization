#!/bin/bash

# Usage:
# ./run.sh <bc_file> <entrypoint>
# Example: 
# ./run.sh memcached

if [ "$#" -ne 2 ]; then
    echo "Usage: ./run.sh <bc_file_name> <entrypoint>"
    exit 1
fi

BC=$1
ENTRY=$2

set -x

rm callgraphs/*.svf.cfg

cp -r /debloating-vol/temporal-specialization-artifacts/bitcodes ./bitcodes
wpa -print-fp -ander -dump-callgraph ./bitcodes/$BC.bc
python3 convertSvfCfgToHumanReadable.py callgraph_final.dot > callgraphs/$BC.svf.type.cfg

spa -condition-cfg ./bitcodes/$BC.bc 2>&1 | tee callgraphs/$BC.svf.conditional.direct.calls.cfg

spa -simple ./bitcodes/$BC.bc 2>&1 | tee callgraphs/$BC.svf.function.pointer.allocations.wglobal.cfg

python3 python-utils/graphCleaner.py --fpanalysis --funcname $ENTRY --output $BC.svf.new.type.fp.wglobal.cfg --directgraphfile callgraphs/$BC.svf.conditional.direct.calls.cfg --funcpointerfile callgraphs/$BC.svf.function.pointer.allocations.wglobal.cfg -c callgraphs/$BC.svf.type.cfg

mkdir outputs
mkdir stats
python3 createSyscallStats.py -c ./callgraphs/glibc.callgraph --apptopropertymap app.to.properties.json --binpath ./binaries --outputpath outputs/ --apptolibmap app.to.lib.map.json --sensitivesyscalls sensitive.syscalls --sensitivestatspath stats/sensitive.stats --syscallreductionpath stats/syscallreduction.stats --libdebloating --othercfgpath ./otherCfgs/ --cfgpath callgraphs

