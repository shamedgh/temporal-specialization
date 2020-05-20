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
    if not options.cleancfg and not options.fpanalysis and not options.minremovable and not options.fpanalysisnew:
        parser.error("At least one of the functionalities: cleancfg, fpanalysis or minremovable should be used")
        return False
    if not options.cfginput:
        parser.error("CFG Input must be specifiec with -c")
        return False

    if options.cleancfg and (not options.cfginput or not options.separator or not options.input):
        parser.error("All options -c, -i and -s should be provided.")
        return False
    elif (options.fpanalysis or options.fpanalysisnew) and (not options.funcname or not options.funcpointerfile or not options.directgraphfile or not options.output):
        parser.error("All options --funcname, --output, --directgraphfile, --funcpointerfile should be provided.")
        return False
    elif options.minremovable and (not options.conditionalgraphfile or not options.minremovestart or not options.minremoveend or not options.minremovemaxdepth):
        parser.error("All options --minremovestart, --conditionalgraphfile, --minremoveend and --minremovemaxdepth should be provided.")
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


    ### General Options ###
    parser.add_option("-c", "--cfginput", dest="cfginput", default=None, nargs=1,
                      help="CFG input for creating graph from CFG")

    parser.add_option("-s", "--separator", dest="separator", default="->", nargs=1,
                      help="CFG file separator per line")

    parser.add_option("-o", "--output", dest="output", default=None, nargs=1,
                      help="Path to store cleaned CFG output")

    ### Kernel CFG Cleaner Options ###
    parser.add_option("", "--cleancfg", dest="cleancfg", action="store_true", default=False,
                      help="Clean CFG based on start nodes")

    parser.add_option("-i", "--input", dest="input", default=None, nargs=1,
                      help="Starting points which should be removed or kept")

    parser.add_option("-v", "--inverse", dest="inverse", action="store_true", default=False, help="Starting points which should be removed or kept")

    ### Function Pointer Analysis ###
    parser.add_option("", "--fpanalysisnew", dest="fpanalysisnew", action="store_true", default=False,
                      help="Fun function pointer analysis")

    parser.add_option("", "--fpanalysis", dest="fpanalysis", action="store_true", default=False,
                      help="Fun function pointer analysis")

    parser.add_option("", "--directgraphfile", dest="directgraphfile", default=None, nargs=1,
                      help="CFG input for direct graph to be applied to the original CFG")

    parser.add_option("", "--funcpointerfile", dest="funcpointerfile", default=None, nargs=1,
                      help="CFG with functions assigned as function pointers")

    parser.add_option("-f", "--funcname", dest="funcname", default=None, nargs=1,
                      help="Function name")

    ### Configuration-Guarded Edge Identification ###
    parser.add_option("", "--minremovable", dest="minremovable", action="store_true", default=False,
                      help="Test minimum removable functionality")

    parser.add_option("", "--conditionalgraphfile", dest="conditionalgraphfile", default=None, nargs=1,
                      help="CFG input for conditional graph to be applied to the original CFG")

    parser.add_option("", "--minremovestart", dest="minremovestart", default=None, nargs=1,
                      help="Start node for minimum removable edge")

    parser.add_option("", "--minremoveend", dest="minremoveend", default=None, nargs=1,
                      help="End node for minimum removable edge")

    parser.add_option("", "--minremovemaxdepth", dest="minremovemaxdepth", default=None, nargs=1,
                      help="Max depth for minimum removable edge")


    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Debug enabled/disabled")

    (options, args) = parser.parse_args()
    if isValidOpts(options):
        rootLogger = setLogPath("graphcleaner.log")
        myGraph = graph.Graph(rootLogger)
        rootLogger.info("Creating CFG...")
        myGraph.createGraphFromInput(options.cfginput, options.separator)

        if ( options.cleancfg ):
            keepList = list()
            allStartingNodes = myGraph.extractStartingNodes()
            rootLogger.info("CFG start nodes: %s", str(allStartingNodes))
            rootLogger.info("CFG len(start nodes): %d", len(allStartingNodes))
            rootLogger.info("CFG node count: %d", myGraph.getNodeCount())
            #allNodesBase = myGraph.getAllNodes()
            myCfg = callfunctiongraph.CallFunctionGraph(myGraph, rootLogger, options.cfginput)
            
            #allNodesCfg = set()
            #nodeDfsDict = myCfg.createAllDfs(myGraph.extractStartingNodes())
            #for key, value in nodeDfsDict.items():
            #    allNodesCfg.add(key)
            #    allNodesCfg.update(value)

            #rootLogger.debug("allNodesBase - allNodesCfg = %s", str(allNodesBase-allNodesCfg))

            inputFile = open(options.input, 'r')
            inputLine = inputFile.readline()
            while ( inputLine ):
                keepList.append(inputLine.strip())
                inputLine = inputFile.readline()

            rootLogger.info("Starting to remove starting nodes")
            if ( options.inverse ):
                nodeDfsDict = myCfg.removeSelectStartNodes(keepList, True)
            else:
                nodeDfsDict = myCfg.removeSelectStartNodes(keepList, False)

            #Apply modification to input CFG
            if ( not options.output ):
                outputPath = options.cfginput + ".start.nodes.only"
            allNodes = set()
            for key, value in nodeDfsDict.items():
                allNodes.add(key)
                allNodes.update(value)

            outputFile = open(outputPath, 'w')
            cfgFile = open(options.cfginput, 'r')
            cfgLine = cfgFile.readline()
            while ( cfgLine ):
                caller = cfgLine.split(options.separator)[0].strip()
                rootLogger.debug("Removing %s from CFG file", caller)
                if ( caller in allNodes ):
                    outputFile.write(cfgLine)
                cfgLine = cfgFile.readline()

            outputFile.close()
            cfgFile.close()

        elif ( options.fpanalysis ):
            myGraph.pruneInaccessibleFunctionPointers(options.funcname, options.funcpointerfile, options.directgraphfile, options.separator, options.output)
        elif ( options.fpanalysisnew ):
            myGraph.pruneAllFunctionPointersNotAccessibleFromChild(options.funcname, options.funcpointerfile, options.directgraphfile, options.separator, options.output)
        elif ( options.minremovable ):
            myGraph.minimumRemovableEdges(options.conditionalgraphfile, options.separator, options.minremovestart, options.minremoveend, int(options.minremovemaxdepth))
