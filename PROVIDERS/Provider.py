from UTILS import strings



class Provider:

    def getMainUrl(self):
        pass

    def getCatalogueName(self):
        pass

    def getArticleFromURL(self, url):
        pass

    def getProducerId(self, article):
        pass

    def getPageCount(self, driver, search_request):
        pass

    def endCondision(self, page):
        pass



    def search(self, driver, page_number, search_request):
        pass

    def parseSearchResult(self, driver, pageNumber):
        pass

    def loadArticlePage(self, driver, article_url, search_type):
        pass

    def getArticleType(self, driver) -> str:
        pass

    def parseCrossReference(self, main_article_name, producer_name, type, cross_ref):
        pass



    def saveJSON(self, driver, article_url, article_name, type, search_request, article):
        pass

    def addAnalogToJSON(self, article, json):
       pass

    def getAnalogs(self, article_url, article_id):
        pass

    def setInfo(self, article_name, producer_name, info_json):
        pass

    def goBack(self, driver):
        pass
