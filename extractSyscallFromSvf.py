"""
Extract the syscalls for each process

"""
import logging
import os
import sys
import json

sys.path.insert(0, './python-utils')

import util
import graph
import binaryAnalysis
import syscall as sycall
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
    if not options.cfginput or not options.targetcfg or not options.mastermain or not options.workermain:
        parser.error("All options -c, -f, -m and -w should be provided.")
        return False

    if options.libsyscalls and (not options.apptolibmap or not options.libsyscallpath or not options.appname):
        parser.error("Options --appname, --apptolibmap and --libsyscallpath  should be provided when enabling the --libsyscalls feature.")
        return False

    if options.binprofiler and (not options.apptolibmap or not options.appname or not options.bininput or not options.output):
        parser.error("Options -o, --appname, --apptolibmap and --bininput should be provided when enabling the --binprofiler feature.")
        return False

    return True

def cleanLib(libName):
    if ( ".so" in libName ):
        libName = re.sub("-.*so",".so",libName)
        libName = libName[:libName.index(".so")]
        libName = libName + ".so"
    return libName


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

def processSyscalls(targetcfg, cfginput, mastermain, workermain, edgefilterlist, libsyscalls, libsyscallpath, binprofiler, bininput, apptolibmap, appname, output, debug, rootLogger, cfginputseparator=":"):

    if not cfginput or not targetcfg or not mastermain or not workermain:
        parser.error("All options -c, -f, -m and -w should be provided.")
        return False

    if libsyscalls and (not apptolibmap or not libsyscallpath or not appname):
        parser.error("Options --appname, --apptolibmap and --libsyscallpath  should be provided when enabling the --libsyscalls feature.")
        return False

    if binprofiler and (not apptolibmap or not appname or not bininput or not output):
        parser.error("Options -o, --appname, --apptolibmap and --bininput should be provided when enabling the --binprofiler feature.")
        return False


    syscallList = list()

    i = 0
    while i < 400:
        syscallList.append("syscall(" + str(i) + ")")
        syscallList.append("syscall(" + str(i) + ")")
        syscallList.append("syscall ( " + str(i) + " )")
        syscallList.append("syscall( " + str(i) + " )")
        i += 1
    
    workerMainFuncList = list()
    if ( "," in workermain ):
        workerMainFuncList = workermain.split(",")
    else:
        workerMainFuncList.append(workermain)
    
    edgeFilterList = list()
    if ( edgefilterlist ):
        if ( "," in edgefilterlist ):
            edgeFilterList = edgefilterlist.split(",")
        else:
            edgeFilterList.append(edgefilterlist)
    else:
        edgeFilterList = workerMainFuncList
    applicationGraph = graph.Graph(rootLogger)
    applicationGraph.createGraphFromInputWithFilter(targetcfg, "->", edgeFilterList)
    libcGraph = graph.Graph(rootLogger)
    libcGraph.createGraphFromInput(cfginput, cfginputseparator)

    rootLogger.info("-------------Extraction Master leave functions---------")
    masterFunctions = applicationGraph.getLeavesFromStartNode(mastermain, list(), list())
    rootLogger.info("-------------Extraction Worker leave functions---------")
    workerFunctions = set()
    for workerFunc in workerMainFuncList:
        workerFunctions.update(applicationGraph.getLeavesFromStartNode(workerFunc, list(), list()))

    masterSyscalls = set()
    for masterFunc in masterFunctions:
        rootLogger.debug("masterfunc: %s", masterFunc)
        masterSyscalls.update(libcGraph.getSyscallFromStartNode(masterFunc))

    workerSyscalls = set()
    for workerFunc in workerFunctions:
        rootLogger.debug("workerfunc: %s", workerFunc)
        workerSyscalls.update(libcGraph.getSyscallFromStartNode(workerFunc))

    rootLogger.info("len(masterSyscalls): %d len(workerSyscalls): %d before adding library syscalls", len(masterSyscalls), len(workerSyscalls))

    libSet = set()      #Libraries which should be added to the both import table and svf analysis output
    otherLibSet = set() #Libraries which should only be added to the import table (e.g. apr, apr-util)
    if ( libsyscalls or binprofiler ):
        appName = appname
        appToLibMap = None
        try:
            appToLibFile = open(apptolibmap, 'r')
            appToLibStr = appToLibFile.read()
            appToLibMap = json.loads(appToLibStr)
        except Exception as e:
            rootLogger.warning("Trying to load app to lib map json from: %s, but doesn't exist: %s", apptolibmap, str(e))
            rootLogger.debug("Finished loading json")
            sys.exit(-1)
        for app in appToLibMap["apps"]:
            for key, value in app.items():
                if ( key.strip() == appName.strip() ):
                    for lib in value["libs"]:
                        libSet.add(cleanLib(lib))
                    for lib in value["otherlibs"]:
                        otherLibSet.add(cleanLib(lib))
    if ( libsyscalls and not binprofiler ):
        libSyscallFile = open(libsyscallpath, 'r')
        libSyscallLine = libSyscallFile.readline()
        while libSyscallLine:
            splittedLine = libSyscallLine.split()
            if ( len(splittedLine) > 2 and cleanLib(splittedLine[1]) in libSet ):
                for syscallNum in splittedLine[2:]:
                    if ( "{" in syscallNum ):
                        syscallNum = syscallNum.replace("{", "")
                    if ( "," in syscallNum ):
                        syscallNum = syscallNum.replace(",", "")
                    if ( "}" in syscallNum ):
                        syscallNum = syscallNum.replace("}", "")
                    masterSyscalls.add(int(syscallNum))
                    workerSyscalls.add(int(syscallNum))
            libSyscallLine = libSyscallFile.readline()
    importTableSyscalls = set()
    if ( not libsyscalls and binprofiler ):
        #TODO Extract required library system calls from binary profiler
        lib =  ".so"
        filesAdded = set()

        for fileName in os.listdir(bininput):
            if ( util.isElf(bininput + "/" + fileName) ):
                if ( lib in fileName ):
                    tmpFileName = cleanLib(fileName)
                else:
                    tmpFileName = fileName
                if (  tmpFileName not in filesAdded and ( tmpFileName in otherLibSet or tmpFileName in libSet or tmpFileName == appname )):
                    filePath = bininput + "/" + fileName
                    myBinary = binaryAnalysis.BinaryAnalysis(filePath, rootLogger)
                    directSyscallSet, successCount, failCount = myBinary.extractDirectSyscalls()
                    indirectSyscallSet = myBinary.extractIndirectSyscalls(libcGraph)
                    importTableSyscalls.update(directSyscallSet)
                    importTableSyscalls.update(indirectSyscallSet)
                    if ( tmpFileName in libSet ):
                        masterSyscalls.update(directSyscallSet)
                        masterSyscalls.update(indirectSyscallSet)
                        workerSyscalls.update(directSyscallSet)
                        workerSyscalls.update(indirectSyscallSet)


    rootLogger.info("len(importTableSyscalls): %d len(masterSyscalls): %d len(workerSyscalls): %d after adding library syscalls", len(importTableSyscalls), len(masterSyscalls), len(workerSyscalls))

    #print ("master: ")
    #print (masterSyscalls)

    #print ("worker: ")
    #print (workerSyscalls)
    translator = sycall.Syscall(rootLogger)
    syscallmap = translator.createMap()
    mminusw = sorted(masterSyscalls.difference(workerSyscalls))
    wminusm = sorted(workerSyscalls.difference(masterSyscalls))

    importTableSyscallNames = set()
    masterSyscallNames = set()
    workerSyscallNames = set()
    blImportTableSyscallNames = set()
    blMasterSyscallNames = set()
    blWorkerSyscallNames = set()

    if ( binprofiler ):
        i = 0
        while ( i < 400 ):
            if i not in importTableSyscalls:
                if ( syscallmap.get(i, None) ):
                    blImportTableSyscallNames.add(syscallmap[i])
            i += 1
        for syscall in importTableSyscalls:
            if ( syscallmap.get(syscall, None) ):
                importTableSyscallNames.add(syscallmap[syscall])
    print ("------- main -------")
    i = 0
    while ( i < 400 ):
        if i not in masterSyscalls:
            if ( syscallmap.get(i, None) ):
                blMasterSyscallNames.add(syscallmap[i])
        i += 1
    for syscall in masterSyscalls:
        if ( syscallmap.get(syscall, None) ):
            masterSyscallNames.add(syscallmap[syscall])
        print (syscallmap.get(syscall, ""))
    print ("------- child -------")
    i = 0
    while ( i < 400 ):
        if i not in workerSyscalls:
            if ( syscallmap.get(i, None) ):
                blWorkerSyscallNames.add(syscallmap[i])
        i += 1
    for syscall in workerSyscalls:
        if ( syscallmap.get(syscall, None) ):
            workerSyscallNames.add(syscallmap[syscall])
        print (syscallmap.get(syscall, ""))

    if ( binprofiler ):
        outputDict = dict()
        outputDict['importTable'] = importTableSyscallNames
        outputDict['master'] = masterSyscallNames
        outputDict['worker'] = workerSyscallNames
        outputDict['blImportTable'] = blImportTableSyscallNames
        outputDict['blMaster'] = blMasterSyscallNames
        outputDict['blWorker'] = blWorkerSyscallNames

        util.writeDictToFile(outputDict, output)

    '''
    mminusw = sorted(mainset.difference(workerset))
    wminusm = sorted(workerset.difference(mainset))

    #mminusc = sorted(mainset.difference(cachemgrset))
    #cminusm = sorted(cachemgrset.difference(mainset))

    rootLogger = setLogPath("graph.log")

    translator = sycall.Syscall(rootLogger)
    syscallmap = translator.createMap()
    '''

    print ("------- main minus worker -------")
    for syscall in mminusw:
        print (syscallmap[syscall])
    print ("------- worker minus main -------")
    for syscall in wminusm:
        print (syscallmap[syscall])


if __name__ == "__main__":

    """
    Find system calls for function
    """
    usage = "Usage: %prog -f <Target program cfg> -c <glibc callgraph file>"

    parser = optparse.OptionParser(usage=usage, version="1")

    parser.add_option("-f", "--targetcfg", dest="targetcfg", default=None, nargs=1,
                      help="Application SVF CFG")

    parser.add_option("-c", "--cfginput", dest="cfginput", default=None, nargs=1,
                      help="Libc CFG input for creating graph from CFG")

    parser.add_option("", "--cfginputseparator", dest="cfginputseparator", default=":", nargs=1,
                      help="Libc CFG separator")

    parser.add_option("-m", "--mastermain", dest="mastermain", default=None, nargs=1,
                      help="Master main function name")

    parser.add_option("-w", "--workermain", dest="workermain", default=None, nargs=1,
                      help="Worker main function name")

    parser.add_option("", "--edgefilterlist", dest="edgefilterlist", default=None, nargs=1,
                      help="List of nodes to filter incoming edges from graph")

    parser.add_option("", "--libsyscalls", dest="libsyscalls", action="store_true", default=False,
                      help="Enable/Disable library system call extraction")

    parser.add_option("", "--libsyscallpath", dest="libsyscallpath", default=None, nargs=1,
                      help="Path to file containing list of system calls required by each library")

    parser.add_option("", "--binprofiler", dest="binprofiler", action="store_true", default=False,
                      help="Enable extracting import table requirements as well")

    parser.add_option("", "--bininput", dest="bininput", default=None, nargs=1,
                      help="Binary profiler input path")

    #Needed for both libsyscalls and binprofiler
    parser.add_option("", "--apptolibmap", dest="apptolibmap", default=None, nargs=1,
                      help="File containing application to library mapping")

    #Needed for both libsyscalls and binprofiler
    parser.add_option("", "--appname", dest="appname", default=None, nargs=1,
                      help="Name of application for extracting list of libraries")

    parser.add_option("-o", "--output", dest="output", default=None, nargs=1,
                      help="Output file path")

    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Debug enabled/disabled")

    (options, args) = parser.parse_args()
    if isValidOpts(options):
        rootLogger = setLogPath("extractsyscallfromsvf.log")
        processSyscalls(options.targetcfg, options.cfginput, options.mastermain, options.workermain, options.edgefilterlist, options.libsyscalls, options.libsyscallpath, options.binprofiler, options.bininput, options.apptolibmap, options.appname, options.output, options.debug, rootLogger, options.cfginputseparator)
