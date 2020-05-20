import os, sys, subprocess, signal
import logging
import optparse
import time

sys.path.insert(0, '../')
import graph
import util


def isValidOpts(opts):
    """
    Check if the required options are sane to be accepted
        - Check if the provided files exist
        - Check if two sections (additional data) exist
        - Read all target libraries to be debloated from the provided list
    :param opts:
    :return:
    """
    if not options.inputfolder or not options.outputfolder or not options.glibccfgpath:
        parser.error("All options, -i, -g and -o should be provided.")
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
    Main function for finding physical memory usage of process
    """
    usage = "Usage: %prog -i <Folder containing ELF files> -o <Output folder to store results in> -d <optional: debug>"

    parser = optparse.OptionParser(usage=usage, version="1")

    parser.add_option("-i", "--inputfolder", dest="inputfolder", default=None, nargs=1,
                      help="Path to folder containing EXEs and LIBs")

    parser.add_option("-o", "--outputfolder", dest="outputfolder", default=None, nargs=1,
                      help="Output folder")

    parser.add_option("-g", "--glibccfgpath", dest="glibccfgpath", default=None, nargs=1,
                      help="Glibc CFG file path")

    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Debug enabled/disabled")

    (options, args) = parser.parse_args()
    if isValidOpts(options):
        rootLogger = setLogPath("extractfunctions.log")

        libraryImports = set()
        exeImports = set()

        libFilePath = options.outputfolder + "/" + "libFuncs.out"
        exeFilePath = options.outputfolder + "/" + "exeFuncs.out"

        libFile = open(libFilePath, 'w')
        exeFile = open(exeFilePath, 'w')
        for fileName in os.listdir(options.inputfolder):
            functionList = util.extractImportedFunctionsFromLibc(options.inputfolder + "/" + fileName, rootLogger)
            if ( not functionList ):
                rootLogger.warning("Function extraction for file: %s failed!", fileName)
            else:
                for function in functionList:
                    if ( fileName.startswith("lib") ):
                        rootLogger.debug("filename %s is a library", fileName)
                        libraryImports.add(function)
                        libFile.write(function + "\n")
                        libFile.flush()
                    else:
                        rootLogger.debug("filename %s is an executable", fileName)
                        exeImports.add(function)
                        exeFile.write(function + "\n")
                        exeFile.flush()
        libFile.close()
        exeFile.close()

        rootLogger.info("(libImports-exeImports): %s", str(libraryImports-exeImports))
        rootLogger.info("(exeImports-libImports): %s", str(exeImports-libraryImports))


        #Map to system calls
        libSyscalls = set()
        exeSyscalls = set()
        glibcSyscallList = list()

        i = 0
        while i < 400:
            glibcSyscallList.append("syscall(" + str(i) + ")")
            glibcSyscallList.append("syscall ( " + str(i) + " )")
            glibcSyscallList.append("syscall( " + str(i) + " )")
            i += 1

        glibcGraph = graph.Graph(rootLogger)
        glibcGraph.createGraphFromInput(options.glibccfgpath, ":")
        glibcWrapperListTemp = []
        i = 0
        while i < 400:
            glibcWrapperListTemp.append(i)
            i += 1
        glibcWrapperList = set(glibcWrapperListTemp)

        tmpSet = set()
        for function in libraryImports:
            leaves = glibcGraph.getLeavesFromStartNode(function, glibcSyscallList, list())
            tmpSet = tmpSet.union(leaves)

            for syscallStr in tmpSet:
                syscallStr = syscallStr.replace("syscall( ", "syscall(")
                syscallStr = syscallStr.replace("syscall ( ", "syscall(")
                syscallStr = syscallStr.replace(" )", ")")
                syscallNum = int(syscallStr[8:-1])
                libSyscalls.add(syscallNum)

        tmpSet = set()
        for function in exeImports:
            leaves = glibcGraph.getLeavesFromStartNode(function, glibcSyscallList, list())
            tmpSet = tmpSet.union(leaves)

            for syscallStr in tmpSet:
                syscallStr = syscallStr.replace("syscall( ", "syscall(")
                syscallStr = syscallStr.replace("syscall ( ", "syscall(")
                syscallStr = syscallStr.replace(" )", ")")
                syscallNum = int(syscallStr[8:-1])
                exeSyscalls.add(syscallNum)

        rootLogger.info("len(libSyscalls-exeSyscalls): %d", len(libSyscalls-exeSyscalls))
        rootLogger.info("(libSyscalls-exeSyscalls): %s", str(libSyscalls-exeSyscalls))
        rootLogger.info("len(exeSyscalls-libSyscalls): %d", len(exeSyscalls-libSyscalls))
        rootLogger.info("(exeSyscalls-libSyscalls): %s", str(exeSyscalls-libSyscalls))
