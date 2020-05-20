"""
Extract the syscalls for each process

"""
import logging
import os
import sys
import json
sys.path.insert(0, '/home/hamed/container-debloating')

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
    if options.binprofiler and (not options.apptolibmap or not options.appname or not options.bininput or not options.libccfginput ):
        parser.error("Options --appname, --libccfginput, --apptolibmap and --bininput should be provided when enabling the --binprofiler feature.")
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

def processSyscalls(binprofiler, bininput, apptolibmap, appname, libccfginput, debug, rootLogger):

    if binprofiler and (not apptolibmap or not appname or not bininput ):
        parser.error("Options --appname, --apptolibmap and --bininput should be provided when enabling the --binprofiler feature.")
        return False
    
    libcGraph = graph.Graph(rootLogger)
    libcGraph.createGraphFromInput(libccfginput, ":")


    libSet = set()      #Libraries which should be added to the both import table and svf analysis output
    otherLibSet = set() #Libraries which should only be added to the import table (e.g. apr, apr-util)
    if ( binprofiler ):
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
    importTableSyscalls = set()
    if ( binprofiler ):
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

    rootLogger.info("len(importTableSyscalls): %d", len(importTableSyscalls))
    return importTableSyscalls

if __name__ == "__main__":

    """
    Find system calls for function
    """
    usage = "Usage: %prog -f <Target program cfg> -c <glibc callgraph file>"

    parser = optparse.OptionParser(usage=usage, version="1")

    parser.add_option("", "--binprofiler", dest="binprofiler", action="store_true", default=False,
                      help="Enable extracting import table requirements as well")

    parser.add_option("", "--bininput", dest="bininput", default=None, nargs=1,
                      help="Binary profiler input path")

    parser.add_option("", "--libccfginput", dest="libccfginput", default=None, nargs=1,
                      help="Libc CFG input for creating graph from CFG")

    #Needed for both libsyscalls and binprofiler
    parser.add_option("", "--apptolibmap", dest="apptolibmap", default=None, nargs=1,
                      help="File containing application to library mapping")

    #Needed for both libsyscalls and binprofiler
    parser.add_option("", "--appname", dest="appname", default=None, nargs=1,
                      help="Name of application for extracting list of libraries")

    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Debug enabled/disabled")

    (options, args) = parser.parse_args()
    if isValidOpts(options):
        rootLogger = setLogPath("extractsyscallfromimporttable.log")
        processSyscalls(options.binprofiler, options.bininput, options.apptolibmap, options.appname, options.libccfginput, options.debug, rootLogger)
