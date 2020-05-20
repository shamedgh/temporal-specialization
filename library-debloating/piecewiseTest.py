import os, sys, subprocess, signal
import logging
import optparse

import piecewise

def isValidOpts(opts):
    if ( not opts.binarypath or not opts.binarycfgpath or not opts.libccfgpath or not opts.otherlibcfgpath ):
        parser.error("All options --binarypath, --binarycfgpath, --libccfgpath and --otherlibcfgpath should be provided.")
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
    usage = "Usage: %prog --binarypath <Binary Path> --binarycfgpath <Binary call graph> --libccfgpath <Libc call graph path> --otherlibcfgpath <Path to folder containing other libraries' cfg>"

    parser = optparse.OptionParser(usage=usage, version="1")

    parser.add_option("", "--binarypath", dest="binarypath", default=None, nargs=1,
                      help="Path to binary to analyze")

    parser.add_option("", "--binarycfgpath", dest="binarycfgpath", default=None, nargs=1,
                      help="Path to call graph of binary to analyze")

    parser.add_option("", "--libccfgpath", dest="libccfgpath", default=None, nargs=1,
                      help="Path to libc call graph")

    parser.add_option("", "--otherlibcfgpath", dest="otherlibcfgpath", default=None, nargs=1,
                      help="Path to binary to analyze")

    parser.add_option("", "--startfunc", dest="startfunc", default="main", nargs=1,
                      help="Function starting point")

    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Debug enabled/disabled")

    (options, args) = parser.parse_args()
    if isValidOpts(options):
        rootLogger = setLogPath("piecewisetest.log")
        myPiecewise = piecewise.Piecewise(options.binarypath, options.binarycfgpath, options.libccfgpath, options.otherlibcfgpath, rootLogger)
        startFuncsStr = options.startfunc
        startFuncs = list()
        if ( "," in startFuncsStr ):
            startFuncs = startFuncsStr.split(",")
        else:
            startFuncs.append(startFuncsStr)
        myPiecewise.extractAccessibleSystemCalls(startFuncs)
