import os, sys, subprocess, signal
import logging
import optparse

import graph
import callfunctiongraph

def isValidOpts(opts):
    """
    Check if the required options are sane to be accepted
        - Check if the provided files exist
        - Check if two sections (additional data) exist
        - Read all target libraries to be debloated from the provided list
    :param opts:
    :return:
    """
    if not options.cfginput or not options.separator:
        parser.error("Both options -c and -s should be provided.")
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
    Find system calls for function
    """
    usage = "Usage: %prog -c <Callgraph> -s <Separator in callgraph file llvm=-> glibc=: > -f <Function name>"

    parser = optparse.OptionParser(usage=usage, version="1")

    parser.add_option("-c", "--cfginpu", dest="cfginput", default=None, nargs=1,
                      help="CFG input for creating graph from CFG")

    parser.add_option("-s", "--separator", dest="separator", default="->", nargs=1,
                      help="CFG file separator per line")

    parser.add_option("-f", "--funcname", dest="funcname", default=None, nargs=1,
                      help="Function name")

    parser.add_option("-e", "--dfs", dest="dfs", action="store_true", default=False, 
                      help="DFS of all functions reachable from start node")

    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Debug enabled/disabled")

    (options, args) = parser.parse_args()
    if isValidOpts(options):
        rootLogger = setLogPath("cfgtest.log")
        requiredStartNode = ['a']
        myGraph = graph.Graph(rootLogger)
        myGraph.createGraphFromInput(options.cfginput, options.separator)
        myCfg = callfunctiongraph.CallFunctionGraph(myGraph, rootLogger)
        requiredSet, unrequiredSet = myCfg.partitionCfg(requiredStartNode)
        rootLogger.info("required set: %s", str(requiredSet))
        rootLogger.info("unrequired set: %s", str(unrequiredSet))
