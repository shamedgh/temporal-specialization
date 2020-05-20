import os, sys, subprocess, signal
import logging
import optparse
import time

sys.path.insert(0, '../')
import graph
import util
import folderAnalysis
import syscall


def isValidOpts(opts):
    """
    Check if the required options are sane to be accepted
        - Check if the provided files exist
        - Check if two sections (additional data) exist
        - Read all target libraries to be debloated from the provided list
    :param opts:
    :return:
    """
    if not options.inputfolder or not options.othercfgs or not options.muslcfgpath or not options.glibccfgpath:
        parser.error("All options, -i, -c, -g and -m should be provided.")
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

if __name__ == '__main__':
    """
    Main function to extract potential for library specialization
    """
    usage = "Usage: %prog -i <Folder containing ELF and library files> -c <Folder containing library CFGs> -g <Path to glibc CFG file> -m <Path to musl CFG file> -d <optional: debug>"

    parser = optparse.OptionParser(usage=usage, version="1")

    parser.add_option("-i", "--inputfolder", dest="inputfolder", default=None, nargs=1,
                      help="Path to folder containing EXEs and LIBs")

    parser.add_option("-c", "--othercfgs", dest="othercfgs", default=None, nargs=1,
                      help="Folder containing CFGs for other libraries")

    parser.add_option("-g", "--glibccfgpath", dest="glibccfgpath", default=None, nargs=1,
                      help="Glibc CFG file path")

    parser.add_option("-m", "--muslcfgpath", dest="muslcfgpath", default=None, nargs=1,
                      help="Musl CFG file path")

    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Debug enabled/disabled")

    (options, args) = parser.parse_args()
    if isValidOpts(options):
        rootLogger = setLogPath("libspecialpotential.log")

        glibcGraph = graph.Graph(rootLogger)
        glibcGraph.createGraphFromInput(options.glibccfgpath, ":")
        muslGraph = graph.Graph(rootLogger)
        muslGraph.createGraphFromInput(options.muslcfgpath, "->")

        syscallObj = syscall.Syscall(rootLogger)
        syscallMap = syscallObj.createMap()

        filterList = ["nginx"]
        
        for folderName in os.listdir(options.inputfolder):
            if ( len(filterList) == 0 or folderName in filterList ):
                rootLogger.info("Running analysis on folderName: %s", folderName)
                myFolderAnalysis = folderAnalysis.FolderAnalysis(options.inputfolder + "/" + folderName, options.othercfgs, muslGraph, glibcGraph, rootLogger)
                elfSyscalls, libSyscalls, libSyscallsPerLib = myFolderAnalysis.extractLibrarySpecializationPotential()
                onlyLibSyscalls = set(libSyscalls-elfSyscalls)
                rootLogger.info("folderName: %s, len(onlyLibSyscalls): %d", folderName, len(onlyLibSyscalls))
                rootLogger.debug("libSyscalls: %s", libSyscalls)
                rootLogger.debug("elfSyscalls: %s", elfSyscalls)
                allSyscalls = set(elfSyscalls.union(libSyscalls))
                rootLogger.debug("allSyscalls: %s", allSyscalls)
                elfSyscallNames = set()
                for elfSyscallNum in elfSyscalls:
                    if ( syscallMap.get(elfSyscallNum, None) == None ):
                        rootLogger.error("No system call name found for: %d", elfSyscallNum)
                    elfSyscallNames.add(syscallMap[elfSyscallNum])
                rootLogger.debug("elfSyscall Names: %s", elfSyscallNames)
                allSyscallNames = set()
                for allSyscallNum in allSyscalls:
                    allSyscallNames.add(syscallMap[allSyscallNum])
                rootLogger.debug("allSyscall Names: %s", allSyscallNames)
                rootLogger.debug("len(allSyscallNum): %d len(allSyscallNames): %d", len(allSyscalls), len(allSyscallNames))
                if ( len(onlyLibSyscalls) > 10 ):
                    for libName, libSyscalls in libSyscallsPerLib.items():
                        rootLogger.info("   %s (unique syscalls):%d", libName, len(set(libSyscalls-elfSyscalls)))


        #rootLogger.info("len(libSyscalls-exeSyscalls): %d", len(libSyscalls-exeSyscalls))
        #rootLogger.info("(libSyscalls-exeSyscalls): %s", str(libSyscalls-exeSyscalls))
        #rootLogger.info("len(exeSyscalls-libSyscalls): %d", len(exeSyscalls-libSyscalls))
        #rootLogger.info("(exeSyscalls-libSyscalls): %s", str(exeSyscalls-libSyscalls))
