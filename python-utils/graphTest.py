import os, sys, subprocess, signal
import logging
import optparse

import graph
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
    if not options.cfginput or not options.separator:
        parser.error("Both options -c and -s should be provided.")
        return False

    return True

def pruneInaccessibleFunctionPointers(mygraph, startNode, funcPointerFile, directCfgFile, separator, outputFile, logger):
    if ( startNode and funcPointerFile and directCfgFile and separator and outputFile ):
        mygraph.pruneInaccessibleFunctionPointers(startNode, funcPointerFile, directCfgFile, separator, outputFile)
    else:
        logger.error("Options --funcname, --outputfile, --directgraphfile, --funcpointerfile should be provided.")
        sys.exit(-1)


def testMinimumRemovableEdges(mygraph, start, end, maxDepth, logger):
    if ( start and end and maxDepth ):
        mygraph.minimumRemovableEdges(start, end, int(maxDepth))
    else:
        logger.error("Options --minremovestart, --minremoveend and --minremovemaxdepth should be provided.")
        sys.exit(-1)

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

    parser.add_option("", "--conditionalgraph", dest="conditionalgraph", default=None, nargs=1,
                      help="CFG input for conditional graph to be applied to the original CFG")

    parser.add_option("", "--directgraphfile", dest="directgraphfile", default=None, nargs=1,
                      help="CFG input for direct graph to be applied to the original CFG")

    parser.add_option("", "--funcpointerfile", dest="funcpointerfile", default=None, nargs=1,
                      help="CFG with functions assigned as function pointers")

    parser.add_option("-s", "--separator", dest="separator", default="->", nargs=1,
                      help="CFG file separator per line")

    parser.add_option("-f", "--funcname", dest="funcname", default=None, nargs=1,
                      help="Function name")

    parser.add_option("", "--funcfile", dest="funcfile", default=None, nargs=1,
                      help="File containing list of functions")

    parser.add_option("-o", "--outputfile", dest="outputfile", default=None, nargs=1,
                      help="Output file")

    parser.add_option("", "--dfs", dest="dfs", action="store_true", default=False, 
                      help="DFS of all functions reachable from start node")

    parser.add_option("", "--minremovable", dest="minremovable", action="store_true", default=False, 
                      help="Test minimum removable functionality")

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
        rootLogger = setLogPath("graph.log")
        myGraph = graph.Graph(rootLogger)
#        myGraph.addEdge("A", "B")        
#        myGraph.addEdge("A", "C")        
#        myGraph.addEdge("C", "E")        
#        myGraph.addEdge("B", "D")        
#        myGraph.addEdge("D", "E")
        syscallList = list()

        syscallObj = syscall.Syscall(rootLogger)
        syscallMap = syscallObj.createMap()

        i = 0
        while i < 400:
            syscallList.append("syscall(" + str(i) + ")")
            syscallList.append("syscall(" + str(i) + ")")
            syscallList.append("syscall ( " + str(i) + " )")
            syscallList.append("syscall( " + str(i) + " )")
            i += 1

        myGraph.createGraphFromInput(options.cfginput, options.separator)
        allPaths = myGraph.printAllPaths("ngx_worker_process_cycle", "ngx_resolver_send_query")

        if ( options.funcfile ):
            funcFile = open(options.funcfile, 'r')
            funcLine = funcFile.readline()
            while ( funcLine ):
                funcName = funcLine.strip()
                leaves = myGraph.getLeavesFromStartNode(funcName, syscallList, list())
                syscallNames = set()
                for leaf in leaves:
                    if ( leaf.startswith("syscall") ):
                        leaf = leaf.replace("syscall", "")
                        leaf = leaf.replace("(", "")
                        leaf = leaf.replace(")", "")
                        syscallNum = int(leaf.strip())
                        syscallNames.add(syscallMap.get(syscallNum, ""))
                if ( options.funcname and options.funcname in syscallNames):
                    print (funcName + " calls: " + options.funcname )
                #print (syscallNames)
                funcLine = funcFile.readline()
        else:
            leaves = set()
            if ( options.dfs ):
                if ( options.funcname ):
                    leaves = myGraph.dfs(options.funcname)
                else:
                    leaves = myGraph.dfs("read")
            elif ( options.minremovable ):
                myGraph.applyConditionalGraph(options.conditionalgraph, "->")
                testMinimumRemovableEdges(myGraph, options.minremovestart, options.minremoveend, options.minremovemaxdepth, rootLogger)
            elif ( options.funcpointerfile ):
                pruneInaccessibleFunctionPointers(myGraph, options.funcname, options.funcpointerfile, options.directgraphfile, "->", options.outputfile, rootLogger)
            else:
                if ( options.funcname ):
                    leaves = myGraph.getLeavesFromStartNode(options.funcname, syscallList, list())
                    syscallNames = set()
                    for leaf in leaves:
                        if ( leaf.startswith("syscall") ):
                            leaf = leaf.replace("syscall", "")
                            leaf = leaf.replace("(", "")
                            leaf = leaf.replace(")", "")
                            syscallNum = int(leaf.strip())
                            syscallNames.add(syscallMap.get(syscallNum, ""))
                    print (syscallNames)
                    #leaves = myGraph.getLeavesFromStartNode(options.funcname, list(), list())
                else:
                    leaves = myGraph.getLeavesFromStartNode("read", syscallList, list())
#            print (leaves)
            for leaf in leaves:
                print (leaf)

