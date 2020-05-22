"""
Extract the syscalls for each process

"""
import logging
import os
import sys
import json
import extractSyscallFromSvf
import extractSyscallFromImportTable

sys.path.insert(0, './python-utils/')

import util
import graph
import binaryAnalysis
import syscall

sys.path.insert(0, './library-debloating')
import piecewise
import re
import optparse

def isValidOpts(opts):
    """
    Check if the required options are sane to be accepted
        - Check if the provided files exist
        - Check if two sections (additional data) exist
        - Read all target libraries to be debloated from the provided list
    :param opts:
    :return:
    """
    if not options.cfginput or not options.othercfgpath or not options.apptopropertymap or not options.binpath or not options.cfgpath or not options.outputpath or not options.apptolibmap or not options.sensitivesyscalls or not options.sensitivestatspath or not options.syscallreductionpath:
        parser.error("All options -c, --othercfgpath, --apptopropertymap, --binpath, --outputpath, --apptolibmap, --sensitivesyscalls, --sensitivestatspath, --syscallreductionpath and --cfgpath should be provided.")
        return False

    return True

def setLogPath(logPath):
    """
    Set the property of the logger: path, config, and format
    :param logPath:
    :return:
    """
    if os.path.exists(logPath):
        os.remove(logPath)

    rootLogger = logging.getLogger("coverage")
    if options.debug:
        logging.basicConfig(filename=logPath, level=logging.DEBUG)
        rootLogger.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(filename=logPath, level=logging.INFO)
        rootLogger.setLevel(logging.INFO)

#    ch = logging.StreamHandler(sys.stdout)
    consoleHandler = logging.StreamHandler()
    rootLogger.addHandler(consoleHandler)
    return rootLogger
#    rootLogger.addHandler(ch)

if __name__ == "__main__":

    """
    Find system calls for function
    """
    usage = "Usage: %prog -f <Target program cfg> -c <glibc callgraph file>"

    parser = optparse.OptionParser(usage=usage, version="1")

    parser.add_option("-c", "--cfginput", dest="cfginput", default=None, nargs=1,
                      help="Libc CFG input for creating graph from CFG")

    parser.add_option("", "--cfginputseparator", dest="cfginputseparator", default=":", nargs=1,
                      help="Libc CFG separator")

    parser.add_option("", "--apptopropertymap", dest="apptopropertymap", default=None, nargs=1,
                      help="File containing application to property mapping")

    parser.add_option("", "--binpath", dest="binpath", default=None, nargs=1,
                      help="Path to binary folders")

    parser.add_option("", "--cfgpath", dest="cfgpath", default=None, nargs=1,
                      help="Path to call function graphs")

    parser.add_option("", "--othercfgpath", dest="othercfgpath", default=None, nargs=1,
                      help="Path to other call graphs")

    parser.add_option("", "--outputpath", dest="outputpath", default=None, nargs=1,
                      help="Path to output folder")

    parser.add_option("", "--apptolibmap", dest="apptolibmap", default=None, nargs=1,
                      help="JSON containing app to library mapping")

    parser.add_option("", "--sensitivesyscalls", dest="sensitivesyscalls", default=None, nargs=1,
                      help="File containing list of sensitive system calls considered for stats")

    parser.add_option("", "--sensitivestatspath", dest="sensitivestatspath", default=None, nargs=1,
                      help="Path to file to store sensitive syscall stats")

    parser.add_option("", "--syscallreductionpath", dest="syscallreductionpath", default=None, nargs=1,
                      help="Path to file to store system call reduction stats")

    parser.add_option("", "--singleappname", dest="singleappname", default=None, nargs=1,
                      help="Name of single application to run, if passed the enable/disable in the JSON file will not be considered")

    parser.add_option("", "--libdebloating", dest="libdebloating", action="store_true", default=False,
                      help="Enable/disable library debloating (based on Nibbler and Piece-wise")

    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Debug enabled/disabled")

    (options, args) = parser.parse_args()
    if isValidOpts(options):
        rootLogger = setLogPath("createsyscallstats.log")
        try:
            appToPropertyFile = open(options.apptopropertymap, 'r')
            appToPropertyStr = appToPropertyFile.read()
            appToPropertyMap = json.loads(appToPropertyStr)
        except Exception as e:
            rootLogger.warning("Trying to load app to property map json from: %s, but doesn't exist: %s", options.apptopropertymap, str(e))
            rootLogger.debug("Finished loading json")
            sys.exit(-1)

        sensitiveSyscallSet = set()

        sensitiveSyscallFile = open(options.sensitivesyscalls, 'r')
        sensitiveSyscallLine = sensitiveSyscallFile.readline()
        while ( sensitiveSyscallLine ):
            sensitiveSyscallSet.add(sensitiveSyscallLine.strip())
            sensitiveSyscallLine = sensitiveSyscallFile.readline()

        sensitiveSyscallOutfile = open(options.sensitivestatspath, 'w')
        syscallReductionFile = open(options.syscallreductionpath, 'w')
        sensitiveSyscallStatLine = "{};{};{};{}\n"
        syscallReductionStatLine = "{};{};{};{}\n"

        syscallTranslator = syscall.Syscall(rootLogger)
        syscallMap = syscallTranslator.createMap()

        cfginput = options.cfginput
        binbasepath = options.binpath
        cfgbasepath = options.cfgpath
        outputbasepath = options.outputpath
        binprofiler = True
        if ( options.libdebloating ):
            syscallReductionFile.write(syscallReductionStatLine.format("Application", "# Import Table Syscalls", "# Piecewise Master", "# Piecewise Worker", "# Temporal Master Syscalls", "# Temporal Worker Syscalls"))
            syscallReductionFile.flush()
        else:
            syscallReductionFile.write(syscallReductionStatLine.format("Application", "# Import Table Syscalls", "# Master Syscalls", "# Worker Syscalls"))
            syscallReductionFile.flush()


        libSecEvalOutputFilePath = appToPropertyMap.get("sec-eval-lib-output", None)
        temporalSecEvalOutputFilePath = appToPropertyMap.get("sec-eval-temporal-output", None)
        libSecEvalOutputFile = open(libSecEvalOutputFilePath, 'w')
        temporalSecEvalOutputFile = open(temporalSecEvalOutputFilePath, 'w')

        for app in appToPropertyMap["apps"]:
            for appName, appDict in app.items():
                if ( (not options.singleappname and appDict.get("enable","true") == "true") or (options.singleappname and appName == options.singleappname) ):
                    rootLogger.info("Extracting system calls for %s", appName)
                    mastermain = appDict.get("master", None)
                    workermain = appDict.get("worker", None)
                    bininput = appDict.get("bininput", None)
                    output = appDict.get("output", None)
                    output = outputbasepath + "/" + output
                    targetcfg = appDict.get("cfg", None)
                    if ( targetcfg ):
                        svftargetcfg = targetcfg.get("svf", None)
                        temporaltargetcfg = targetcfg.get("svftypefp", None)
                        runtimecfg = targetcfg.get("svftypefpruntime", None)
                        directcfg = targetcfg.get("direct", None)
                        targetcfg = targetcfg.get("svftypefp", None)

                        #rootLogger.info("directCFG: %s temporalCFG: %s runtimeCFG: %s", directcfg, temporaltargetcfg, runtimecfg)
                    if ( not options.libdebloating ):
                        #TODO Some features have not been implemented in case of not using library debloating
                        if ( not os.path.exists(output) ):
                            extractSyscallFromSvf.processSyscalls(targetcfg, cfginput, mastermain, workermain, None, None, None, binprofiler, binbasepath + "/" + bininput, options.apptolibmap, appName, output, options.debug, rootLogger, options.cfginputseparator)
                        if ( os.path.exists(output) ):
                            appSyscallDict = util.readDictFromFile(output)
                            importTableSyscalls = appSyscallDict["importTable"]
                            masterSyscalls = appSyscallDict["master"]
                            workerSyscalls = appSyscallDict["worker"]

                            syscallReductionFile.write(syscallReductionStatLine.format(appName, len(importTableSyscalls), len(masterSyscalls), len(workerSyscalls)))
                            syscallReductionFile.flush()

                            for syscall in sensitiveSyscallSet:
                                if ( syscall in importTableSyscalls ):
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "original", 1))
                                else:
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "original", 0))
                                if ( syscall in masterSyscalls ):
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "master", 1))
                                else:
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "master", 0))
                                if ( syscall in workerSyscalls ):
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "worker", 1))
                                else:
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "worker", 0))
                                sensitiveSyscallOutfile.flush()
                        else:
                            rootLogger.warning("Couldn't create syscall output file, skipping app: %s", appName)
                    else:
                        if ( not os.path.exists(output) ):
                            rootLogger.info("%s doesn't exist, generating first", output)
                            aprRelatedList = ["libaprutil-1", "libapr-1"]
                            uvRelatedList = ["libuv"]
                            eventRelatedList = ["libevent-2"]

                            exceptList = list()
                            exceptList.extend(aprRelatedList)
                            exceptList.extend(uvRelatedList)
                            exceptList.extend(eventRelatedList)

                            #rootLogger.info("Piecewise enabled for %s", appName)
                            startFuncsStr = workermain
                            workerMainList = list()
                            if ( "," in startFuncsStr ):
                                workerMainList = startFuncsStr.split(",")
                            else:
                                workerMainList.append(startFuncsStr)
                            startFuncsStr = mastermain
                            masterMainList = list()
                            if ( "," in startFuncsStr ):
                                masterMainList = startFuncsStr.split(",")
                            else:
                                masterMainList.append(startFuncsStr)

                            importTableSyscalls = extractSyscallFromImportTable.processSyscalls(True, binbasepath + "/" + bininput, options.apptolibmap, appName, options.cfginput, options.debug, rootLogger)
                            #rootLogger.info("Finished extracting import table system calls with len: %d for %s", len(importTableSyscalls), appName)

                            piecewiseObj = piecewise.Piecewise(binbasepath + "/" + bininput + "/" + appName, cfgbasepath + "/" + svftargetcfg, cfginput, options.othercfgpath, rootLogger, options.cfginputseparator)
                            piecewiseWorkerSyscalls = piecewiseObj.extractAccessibleSystemCalls(workerMainList, exceptList)
                            #rootLogger.info("Finished extracting piecewise worker system calls with len: %d for %s", len(piecewiseWorkerSyscalls), appName)
                            piecewiseMasterSyscalls = piecewiseObj.extractAccessibleSystemCalls(masterMainList, exceptList)
                            #rootLogger.info("Finished extracting piecewise master system calls with len: %d for %s", len(piecewiseMasterSyscalls), appName)
                            temporalObj = piecewise.Piecewise(binbasepath + "/" + bininput + "/" + appName, cfgbasepath + "/" + temporaltargetcfg, cfginput, options.othercfgpath, rootLogger, options.cfginputseparator)
                            temporalWorkerSyscalls = temporalObj.extractAccessibleSystemCalls(workerMainList, exceptList)
                            #rootLogger.info("Finished extracting temporal worker system calls with len: %d for %s", len(temporalWorkerSyscalls), appName)
                            temporalMasterSyscalls = temporalObj.extractAccessibleSystemCalls(masterMainList, exceptList)

                            if ( runtimecfg ):
                                runtimeObj = piecewise.Piecewise(binbasepath + "/" + bininput + "/" + appName, cfgbasepath + "/" + runtimecfg, cfginput, options.othercfgpath, rootLogger, options.cfginputseparator)
                                functionToSyscallMap = runtimeObj.extractAccessibleSystemCallsFromIndirectFunctions(cfgbasepath + "/" + directcfg, "->")
                                runtimeWorkerSyscalls = runtimeObj.extractAccessibleSystemCalls(workerMainList, exceptList)
                                #rootLogger.info("Finished extracting temporal worker system calls on runtime CFG with len: %d for %s", len(runtimeWorkerSyscalls), appName)
                                runtimeMasterSyscalls = runtimeObj.extractAccessibleSystemCalls(masterMainList, exceptList)
                                for function, syscalls in functionToSyscallMap.items():
                                    rootLogger.info("function: %s syscalls: %s", function, str(syscalls))
                                #rootLogger.info("////////////////////////////////////////////appName: %s runtime: %d ////////////////////////////////////", appName, len(runtimeWorkerSyscalls))


                            importTableSyscallNames = set()
                            piecewiseWorkerSyscallNames = set()
                            piecewiseMasterSyscallNames = set()
                            temporalWorkerSyscallNames = set()
                            temporalMasterSyscallNames = set()

                            blImportTableSyscallNames = set()
                            blPiecewiseWorkerSyscallNames = set()
                            blPiecewiseMasterSyscallNames = set()
                            blTemporalWorkerSyscallNames = set()
                            blTemporalMasterSyscallNames = set()

                            for syscall in importTableSyscalls:
                                if ( syscallMap.get(syscall, None) ):
                                    importTableSyscallNames.add(syscallMap[syscall])
                            for syscall in piecewiseWorkerSyscalls:
                                if ( syscallMap.get(syscall, None) ):
                                    piecewiseWorkerSyscallNames.add(syscallMap[syscall])
                            for syscall in piecewiseMasterSyscalls:
                                if ( syscallMap.get(syscall, None) ):
                                    piecewiseMasterSyscallNames.add(syscallMap[syscall])
                            for syscall in temporalWorkerSyscalls:
                                if ( syscallMap.get(syscall, None) ):
                                    temporalWorkerSyscallNames.add(syscallMap[syscall])
                            for syscall in temporalMasterSyscalls:
                                if ( syscallMap.get(syscall, None) ):
                                    temporalMasterSyscallNames.add(syscallMap[syscall])


                            i = 0
                            while ( i < 400 ):
                                if i not in importTableSyscalls:
                                    if ( syscallMap.get(i, None) ):
                                        blImportTableSyscallNames.add(syscallMap[i])
                                if i not in piecewiseWorkerSyscalls:
                                    if ( syscallMap.get(i, None) ):
                                        blPiecewiseWorkerSyscallNames.add(syscallMap[i])
                                if i not in piecewiseMasterSyscalls:
                                    if ( syscallMap.get(i, None) ):
                                        blPiecewiseMasterSyscallNames.add(syscallMap[i])
                                if i not in temporalWorkerSyscalls:
                                    if ( syscallMap.get(i, None) ):
                                        blTemporalWorkerSyscallNames.add(syscallMap[i])
                                if i not in temporalMasterSyscalls:
                                    if ( syscallMap.get(i, None) ):
                                        blTemporalMasterSyscallNames.add(syscallMap[i])
                                i += 1
                            outputDict = dict()
                            outputDict['importTable'] = importTableSyscallNames
                            outputDict['piecewiseMaster'] = piecewiseMasterSyscallNames
                            outputDict['piecewiseWorker'] = piecewiseWorkerSyscallNames
                            outputDict['temporalMaster'] = temporalMasterSyscallNames
                            outputDict['temporalWorker'] = temporalWorkerSyscallNames
                            outputDict['blImportTable'] = blImportTableSyscallNames
                            outputDict['blPiecewiseMaster'] = blPiecewiseMasterSyscallNames
                            outputDict['blPiecewiseWorker'] = blPiecewiseWorkerSyscallNames
                            outputDict['blTemporalMaster'] = blTemporalMasterSyscallNames
                            outputDict['blTemporalWorker'] = blTemporalWorkerSyscallNames

                            util.writeDictToFile(outputDict, output)

                            #Write result for each application in file for shellcode security evaluation
                            libSecEvalOutputFile.write(appName + ":" + util.cleanStrList(blPiecewiseMasterSyscallNames).replace(" ", "")+ "\n")
                            libSecEvalOutputFile.flush()
                            temporalSecEvalOutputFile.write(appName + ":" + util.cleanStrList(blTemporalWorkerSyscallNames).replace(" ", "") + "\n")
                            temporalSecEvalOutputFile.flush()

                        if ( os.path.exists(output) ):
                            rootLogger.info("%s exists, creating stats", output)
                            outputDict = util.readDictFromFile(output)
                            importTableSyscalls = outputDict['importTable']
                            piecewiseMasterSyscalls = outputDict['piecewiseMaster']
                            piecewiseWorkerSyscalls = outputDict['piecewiseWorker']
                            temporalMasterSyscalls = outputDict['temporalMaster']
                            temporalWorkerSyscalls = outputDict['temporalWorker']

                            sensitiveSyscallStatLine = "{};{};{};{}\n"
                            syscallReductionStatLine = "{};{};{};{};{};{}\n"

                            rootLogger.info("////////////////////////////////////////////appName: %s libdebloating: %d temporal: %d ////////////////////////////////////", appName, len(piecewiseMasterSyscalls), len(temporalWorkerSyscalls))

                            syscallReductionFile.write(syscallReductionStatLine.format(appName, len(importTableSyscalls), len(piecewiseMasterSyscalls), len(piecewiseWorkerSyscalls), len(temporalMasterSyscalls), len(temporalWorkerSyscalls)))
                            syscallReductionFile.flush()

                            #Write result similar to TABLE2 in paper to file
                            syscallCountOutputFile = open(options.outputpath + "/syscall.count-TABLE2.out", 'w')
                            syscallCountOutputFile.write("application;libdebloating;temporal-init;temporal-serving\n")
                            syscallCountOutputFile.flush()
                            syscallCountOutputFile.write(appName + ";" + str(len(piecewiseMasterSyscalls)) + ";" + str(len(temporalMasterSyscalls)) + ";" + str(len(temporalWorkerSyscalls)) + "\n")
                            syscallCountOutputFile.flush()
                            syscallCountOutputFile.close()

                            for syscall in sensitiveSyscallSet:
                                if ( syscall in importTableSyscalls ):
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "original", 1))
                                else:
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "original", 0))
                                if ( syscall in piecewiseMasterSyscalls ):
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "piecewise-master", 1))
                                else:
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "piecewise-master", 0))
                                if ( syscall in piecewiseWorkerSyscalls ):
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "piecewise-worker", 1))
                                else:
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "piecewise-worker", 0))
                                if ( syscall in temporalMasterSyscalls ):
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "temporal-master", 1))
                                else:
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "temporal-master", 0))
                                if ( syscall in temporalWorkerSyscalls ):
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "temporal-worker", 1))
                                else:
                                    sensitiveSyscallOutfile.write(sensitiveSyscallStatLine.format(syscall, appName, "temporal-worker", 0))
                                sensitiveSyscallOutfile.flush()

                else:
                    rootLogger.info("App %s is disabled, skipping...", appName)

        libSecEvalOutputFile.close()
        temporalSecEvalOutputFile.close()

        sensitiveSyscallOutfile.close()
        syscallReductionFile.close()
