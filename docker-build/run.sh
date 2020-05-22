#!/bin/bash

# Usage:
# ./run.sh <bc_file> <entrypoint>
# Example: 
# ./run.sh memcached worker_libevent

if [ "$#" -ne 1 ]; then
    echo "Usage: ./run.sh <bc_file_name>"
    exit 1
fi

BC=$1

APP="$(cut -d'.' -f1 <<< $BC)"

set -x

wpa -print-fp -ander -dump-callgraph ./bitcodes/$BC.bc
python3 convertSvfCfgToHumanReadable.py callgraph_final.dot > callgraphs/$BC.svf.type.cfg

spa -condition-cfg ./bitcodes/$BC.bc 2>&1 | tee callgraphs/$BC.svf.conditional.direct.calls.cfg

spa -simple ./bitcodes/$BC.bc 2>&1 | tee callgraphs/$BC.svf.function.pointer.allocations.wglobal.cfg

python3 python-utils/graphCleaner.py --fpanalysis --funcname main --output callgraphs/$BC.svf.new.type.fp.wglobal.cfg --directgraphfile callgraphs/$BC.svf.conditional.direct.calls.cfg --funcpointerfile callgraphs/$BC.svf.function.pointer.allocations.wglobal.cfg -c callgraphs/$BC.svf.type.cfg

mkdir outputs
mkdir stats
python3 createSyscallStats.py -c ./callgraphs/glibc.callgraph --apptopropertymap app.to.properties.json --binpath ./binaries --outputpath outputs/ --apptolibmap app.to.lib.map.json --sensitivesyscalls sensitive.syscalls --sensitivestatspath stats/sensitive.stats --syscallreductionpath stats/syscallreduction.stats --libdebloating --othercfgpath ./otherCfgs/ --cfgpath callgraphs --singleappname $APP

python security-evaluation/getBlockedPayloads.py --blockedSyscallsTempSpl security-evaluation/removedViaTemporalSpecialization.txt --blockedSyscallsLibDeb security-evaluation/removedViaLibDebloating.txt 2>&1 | tee $APP.shellcode.payload.txt
python security-evaluation/getBlockedPayloadsROP.py --blockedSyscallsTempSpl security-evaluation/removedViaTemporalSpecialization.txt --blockedSyscallsLibDeb security-evaluation/removedViaLibDebloating.txt 2>&1 | tee $APP.rop.payload.txt

cp $APP.shellcode.payload.txt /results/
cp $APP.rop.payload.txt /results/

cp stats/sensitive.stats /results/$APP.sensitive.stats
cp outputs/syscall.count-TABLE2.out /results/$APP.syscall.count
