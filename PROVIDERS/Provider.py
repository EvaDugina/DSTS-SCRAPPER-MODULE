class Provider:

    def getMainUrl(self):
        pass

    def getArticleFromURL(self, url):
        pass

    def getProducerId(self, article):
        pass

    def search(self, driver, page_number, search_request):
        pass

    def endCondision(self, page):
        pass

    def parseSearchResult(self, driver):
        pass

    def loadArticlePage(self, driver, article, search_type):
        pass

    def parseCrossReference(self, driver, article_id, timeout):
        pass

    def saveJSON(self, article_url, article_name):
        pass

    def getAnalogs(self, article_url, article_id):
        pass

    def goBack(self, driver):
        pass
