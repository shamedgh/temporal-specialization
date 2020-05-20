import requests
import urllib.request
import time
from bs4 import BeautifulSoup
from lxml import etree

class Scraper():
    """
    This class can be used to create a graph and run DFS and BFS on it
    """
    def __init__(self, url, logger):
        self.url = url
        self.logger = logger

    def getWebsiteFromUrl(self):
        url = self.url
        websiteUrl = ""
        if ( url.startswith("http://") ):
            websiteUrl = "http://"
            url = url.replace("http://", "")
        elif ( url.startswith("https://") ):
            websiteUrl = "https://"
            url = url.replace("https://", "")
        websiteUrl += url.split("/")[0]
        return websiteUrl
        
    def loadWebsite(self):
        self.logger.debug("loadWebsite called for url: %s", self.url)
        request = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            responseObj = urllib.request.urlopen(request)
            response = responseObj.read()
            soup = BeautifulSoup(response, features="html.parser")
            responseObj.close()
            return soup
        except:
            self.logger.error("Can't load website for url: %s", self.url)
            return None

    #def extractLinks(self, urlFilterList=None):
    #    urlList = list()
    #    if ( not self.soup ):
    #        self.loadWebsite()
    #    allLinks = self.soup.findAll('a')
    #    for aLink in allLinks:
    #        link = aLink.get('href', None)
    #        if ( link ):
    #            if ( urlFilterList ):
    #                for urlFilter in urlFilterList:
    #                    if ( urlFilter in link ):
    #                        if ( not link.startswith("http") ):
    #                            link = self.getWebsiteFromUrl() + link
    #                        urlList.append(link)
    #            else:
    #                if ( not link.startswith("http") ):
    #                    link = self.getWebsiteFromUrl() + link
    #                urlList.append(link)
    #    return urlList

    #def extractFirstTagWithAttr(self, tag, attrDict):
    #    if ( not self.soup ):
    #        self.loadWebsite()
    #    attrComplete = self.soup.find(tag, attrDict)
    #    return attrComplete

    #def extractTagWithAttr(self, tag, attrDict)
    #    if ( not self.soup ):
    #        self.loadWebsite()
    #    attrList = self.soup.find_all(tag, attrDict)
    #    return attrList


