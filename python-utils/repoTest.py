import os, sys, subprocess, signal
import logging
import optparse

import repostaticanalysis

def isValidOpts(opts):
    """
    Check if the required options are sane to be accepted
        - Check if the provided files exist
        - Check if two sections (additional data) exist
        - Read all target libraries to be debloated from the provided list
    :param opts:
    :return:
    """
    if not options.repopath:
        parser.error("Option -r should be provided.")
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
    usage = "Usage: %prog -e <Target executable path> -p <PID of process to retrieve information about>"

    parser = optparse.OptionParser(usage=usage, version="1")

    parser.add_option("-r", "--repopath", dest="repopath", default=None, nargs=1,
                      help="Perf output path")

    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Debug enabled/disabled")

    (options, args) = parser.parse_args()
    if isValidOpts(options):
        rootLogger = setLogPath("repotest.log")
        repoObj = repostaticanalysis.RepoStaticAnalysis(options.repopath, rootLogger)
        testKernel = {"05692d7005a364add85c6e25a6c4447ce08f913a":{"drivers/vfio/pci/vfio_pci.c":[829,839]}}
        for commitId, fileDict in testKernel.items():
            for fileName, lineNumberList in fileDict.items():
                for lineNumber in lineNumberList:
                    rootLogger.info("FunctionName: %s", repoObj.getFunction(fileName, lineNumber, commitId))
