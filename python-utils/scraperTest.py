import os, sys, subprocess, signal
import logging
import optparse
import util
import scraper

def isValidOpts(opts):
    """
    Check if the required options are sane to be accepted
        - Check if the provided files exist
        - Check if two sections (additional data) exist
        - Read all target libraries to be debloated from the provided list
    :param opts:
    :return:
    """
    if not options.url:
        parser.error("Option -u should be provided.")
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

    parser.add_option("-u", "--url", dest="url", default=None, nargs=1,
                      help="Url to run scraper on")

    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Debug enabled/disabled")

    (options, args) = parser.parse_args()
    if isValidOpts(options):
        rootLogger = setLogPath("scraper.log")
        scraperObj = scraper.Scraper(options.url, rootLogger)
        rootLogger.info("url: %s website url: %s", options.url, scraperObj.getWebsiteFromUrl())
        #filterList = ["cve/"]
        filterList = None
        soupObj = scraperObj.loadWebsite()
        if ( soupObj ):
            websiteUrl = scraperObj.getWebsiteFromUrl()
            rootLogger.info("list of urls: %s", str(util.htmlParseExtractLinks(soupObj, websiteUrl, filterList)))
